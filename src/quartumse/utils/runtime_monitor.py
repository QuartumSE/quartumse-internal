"""Utilities for monitoring IBM Quantum Runtime usage and queue depth."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Mapping, Optional

LOGGER = logging.getLogger(__name__)


@dataclass
class QueueStatus:
    """Details about a backend's queue state."""

    backend_name: str
    pending_jobs: Optional[int] = None
    operational: Optional[bool] = None
    status_msg: Optional[str] = None


@dataclass
class QuotaStatus:
    """Details about runtime quota consumption."""

    plan: Optional[str] = None
    limit_seconds: Optional[int] = None
    consumed_seconds: Optional[int] = None
    remaining_seconds: Optional[int] = None
    refresh_date: Optional[datetime] = None
    max_pending_jobs: Optional[int] = None
    current_pending_jobs: Optional[int] = None
    raw: Optional[Dict[str, Any]] = None


@dataclass
class RuntimeStatusReport:
    """Aggregated runtime status."""

    queue: QueueStatus
    quota: QuotaStatus
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def collect_runtime_status(
    backend_name: str,
    *,
    service: Any | None = None,
    service_kwargs: Optional[Dict[str, Any]] = None,
) -> RuntimeStatusReport:
    """Collect queue depth and quota usage for ``backend_name``.

    Args:
        backend_name: Name of the IBM Quantum backend (without provider prefix).
        service: Optional pre-configured ``QiskitRuntimeService`` instance. When provided,
            ``service_kwargs`` are ignored.
        service_kwargs: Keyword arguments forwarded to ``QiskitRuntimeService`` when
            ``service`` is ``None``.

    Returns:
        RuntimeStatusReport: Structured report containing queue and quota metrics.

    Raises:
        ImportError: When ``qiskit-ibm-runtime`` is not installed.
        RuntimeError: When the runtime service cannot be initialised or queried.
    """

    runtime_service = service
    if runtime_service is None:
        runtime_service = _build_service(service_kwargs or {})

    backend = _resolve_backend(runtime_service, backend_name)
    queue_status = _extract_queue_status(backend, backend_name)
    quota_status = _extract_quota_status(runtime_service)

    return RuntimeStatusReport(queue=queue_status, quota=quota_status)


def seconds_to_pretty(seconds: Optional[int]) -> str:
    """Render ``seconds`` into a human friendly duration string."""

    if seconds is None:
        return "unknown"

    if seconds < 60:
        return f"{seconds}s"

    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.1f}m"

    hours = minutes / 60
    if hours < 24:
        return f"{hours:.2f}h"

    days = hours / 24
    return f"{days:.2f}d"


def build_notification_message(report: RuntimeStatusReport) -> str:
    """Generate a concise multiline message for chat/incident systems."""

    parts = [
        f"IBM runtime status — backend {report.queue.backend_name}",
        f"Queue depth: {report.queue.pending_jobs if report.queue.pending_jobs is not None else 'unknown'}",
    ]

    if report.queue.operational is not None:
        parts[-1] += f" (operational={report.queue.operational})"
    if report.queue.status_msg:
        parts.append(f"Backend status: {report.queue.status_msg}")

    quota_line = "Quota: "
    if report.quota.consumed_seconds is not None:
        quota_line += f"{seconds_to_pretty(report.quota.consumed_seconds)} used"
    if report.quota.limit_seconds is not None:
        if not quota_line.endswith("used"):
            quota_line += ""
        quota_line += f" / {seconds_to_pretty(report.quota.limit_seconds)} total"
    if report.quota.remaining_seconds is not None:
        quota_line += f" ({seconds_to_pretty(report.quota.remaining_seconds)} remaining)"
    parts.append(quota_line)

    if report.quota.plan:
        parts.append(f"Plan: {report.quota.plan}")
    if report.quota.max_pending_jobs is not None:
        current = report.quota.current_pending_jobs
        parts.append(
            f"Pending jobs cap: {current if current is not None else '?'} / {report.quota.max_pending_jobs}"
        )
    if report.quota.refresh_date is not None:
        parts.append(f"Quota refreshes on: {report.quota.refresh_date.isoformat()}")

    parts.append(f"Snapshot collected at {report.collected_at.isoformat()}")
    return "\n".join(parts)


def report_to_dict(report: RuntimeStatusReport) -> Dict[str, Any]:
    """Serialise ``report`` into a JSON-friendly dictionary."""

    data = asdict(report)
    quota = data.get("quota", {})
    refresh_date = quota.get("refresh_date")
    if isinstance(refresh_date, datetime):
        quota["refresh_date"] = refresh_date.isoformat()
    collected_at = data.get("collected_at")
    if isinstance(collected_at, datetime):
        data["collected_at"] = collected_at.isoformat()
    raw_usage = quota.get("raw")
    if raw_usage is not None:
        quota["raw"] = _sanitize_jsonable(raw_usage)
    return data


def post_to_webhook(webhook_url: str, message: str, *, dry_run: bool = False, timeout: int = 10) -> None:
    """POST ``message`` to ``webhook_url`` (Slack-compatible JSON payload)."""

    if dry_run:
        LOGGER.info("Dry-run enabled: skipping webhook POST to %s", webhook_url)
        return

    import urllib.error
    import urllib.request

    payload = json.dumps({"text": message}).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310
            response.read()
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to post webhook message: {exc}") from exc


def _build_service(service_kwargs: Mapping[str, Any]) -> Any:
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
    except ImportError as exc:  # pragma: no cover - import guard
        raise ImportError(
            "qiskit-ibm-runtime is not installed. Install quartumse[aws] or add qiskit-ibm-runtime to your environment."
        ) from exc

    try:
        return QiskitRuntimeService(**dict(service_kwargs))
    except Exception as exc:  # pragma: no cover - requires remote service
        raise RuntimeError(f"Unable to initialise QiskitRuntimeService: {exc}") from exc


def _resolve_backend(service: Any, backend_name: str) -> Any:
    try:
        return service.backend(backend_name)
    except Exception as exc:  # pragma: no cover - requires remote service
        raise RuntimeError(f"Unable to resolve backend '{backend_name}': {exc}") from exc


def _extract_queue_status(backend: Any, default_name: str) -> QueueStatus:
    backend_name = getattr(backend, "name", default_name)
    pending_jobs: Optional[int] = None
    operational: Optional[bool] = None
    status_msg: Optional[str] = None

    try:
        status = backend.status()
    except Exception as exc:  # pragma: no cover - requires remote service
        LOGGER.warning("Failed to query backend status for %s: %s", backend_name, exc)
        status_msg = str(exc)
    else:
        pending_jobs = getattr(status, "pending_jobs", None)
        operational = getattr(status, "operational", None)
        status_msg = getattr(status, "status_msg", None)

    return QueueStatus(
        backend_name=str(backend_name),
        pending_jobs=pending_jobs,
        operational=operational,
        status_msg=status_msg,
    )


def _extract_quota_status(service: Any) -> QuotaStatus:
    usage: Dict[str, Any]
    try:
        usage = service.usage()
    except Exception as exc:  # pragma: no cover - requires remote service
        LOGGER.warning("Failed to retrieve runtime usage information: %s", exc)
        return QuotaStatus(raw={"error": str(exc)})

    plan = _first_value(usage, ("plan", "planId", "type"))
    limit_seconds = _first_int(usage, ("usage_limit_seconds", "usage_limit", "usage_allocation_seconds"))
    consumed_seconds = _first_int(usage, ("usage_consumed_seconds", "usage_consumed"))
    remaining_seconds = _first_int(usage, ("usage_remaining_seconds", "usage_remaining"))
    if remaining_seconds is None and limit_seconds is not None and consumed_seconds is not None:
        remaining_seconds = max(limit_seconds - consumed_seconds, 0)

    refresh_raw = _first_value(usage, ("usage_refresh_date", "refreshDate"))
    refresh_date = _parse_datetime(refresh_raw)

    by_instance = usage.get("byInstance") or usage.get("by_instance")
    max_pending_jobs: Optional[int] = None
    current_pending_jobs: Optional[int] = None
    if isinstance(by_instance, Iterable):
        try:
            instance_entry = next(iter(by_instance))
        except StopIteration:
            instance_entry = None
        if isinstance(instance_entry, Mapping):
            max_pending_jobs = _first_int(
                instance_entry,
                ("maxPendingJobs", "max_pending_jobs"),
            )
            current_pending_jobs = _first_int(
                instance_entry,
                ("pendingJobs", "pending_jobs"),
            )

    return QuotaStatus(
        plan=plan,
        limit_seconds=limit_seconds,
        consumed_seconds=consumed_seconds,
        remaining_seconds=remaining_seconds,
        refresh_date=refresh_date,
        max_pending_jobs=max_pending_jobs,
        current_pending_jobs=current_pending_jobs,
        raw=_sanitize_jsonable(usage),
    )


def _first_value(mapping: Mapping[str, Any], keys: Iterable[str]) -> Optional[str]:
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            return str(value)
    return None


def _first_int(mapping: Mapping[str, Any], keys: Iterable[str]) -> Optional[int]:
    for key in keys:
        if key not in mapping:
            continue
        value = mapping[key]
        if value is None:
            continue
        try:
            return int(float(value))
        except (TypeError, ValueError):
            continue
    return None


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        candidate = value.strip()
        if candidate.endswith("Z"):
            candidate = candidate[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            return None
    return None


def _sanitize_jsonable(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, default=str))
    except Exception:  # pragma: no cover - defensive fallback
        return value


__all__ = [
    "QueueStatus",
    "QuotaStatus",
    "RuntimeStatusReport",
    "build_notification_message",
    "collect_runtime_status",
    "post_to_webhook",
    "report_to_dict",
    "seconds_to_pretty",
]
