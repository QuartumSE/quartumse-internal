from __future__ import annotations

from datetime import datetime

import pytest

from quartumse.utils.runtime_monitor import (
    build_notification_message,
    collect_runtime_status,
    compute_budgeting_hints,
    post_to_webhook,
    report_to_dict,
    seconds_to_pretty,
)


class _FakeBackendStatus:
    def __init__(self, pending_jobs: int, operational: bool, status_msg: str) -> None:
        self.pending_jobs = pending_jobs
        self.operational = operational
        self.status_msg = status_msg


class _FakeBackend:
    def __init__(self, name: str, status: _FakeBackendStatus) -> None:
        self.name = name
        self._status = status

    def status(self) -> _FakeBackendStatus:
        return self._status


class _FakeService:
    def __init__(self) -> None:
        status = _FakeBackendStatus(pending_jobs=3, operational=True, status_msg="running")
        self._backend = _FakeBackend("ibmq_fake", status)

    def backend(self, backend_name: str) -> _FakeBackend:
        assert backend_name == "ibmq_fake"
        return self._backend

    def usage(self) -> dict:
        return {
            "plan": "OPEN",
            "usage_limit_seconds": 600,
            "usage_consumed_seconds": 120,
            "usage_refresh_date": "2025-05-01T00:00:00Z",
            "byInstance": [
                {
                    "pendingJobs": 2,
                    "maxPendingJobs": 5,
                }
            ],
        }


def test_collect_runtime_status_from_fake_service() -> None:
    report = collect_runtime_status("ibmq_fake", service=_FakeService())

    assert report.queue.backend_name == "ibmq_fake"
    assert report.queue.pending_jobs == 3
    assert report.queue.operational is True
    assert report.queue.status_msg == "running"

    assert report.quota.plan == "OPEN"
    assert report.quota.limit_seconds == 600
    assert report.quota.consumed_seconds == 120
    assert report.quota.remaining_seconds == 480
    assert report.quota.max_pending_jobs == 5
    assert report.quota.current_pending_jobs == 2
    assert isinstance(report.quota.refresh_date, datetime)
    assert report.quota.refresh_date.tzinfo is not None


@pytest.mark.parametrize(
    "seconds, expected",
    [
        (None, "unknown"),
        (30, "30s"),
        (90, "1.5m"),
        (3600, "1.00h"),
        (172800, "2.00d"),
    ],
)
def test_seconds_to_pretty(seconds, expected) -> None:
    assert seconds_to_pretty(seconds) == expected


def test_report_to_dict_serialises_datetimes() -> None:
    report = collect_runtime_status("ibmq_fake", service=_FakeService())
    payload = report_to_dict(report)

    assert "collected_at" in payload
    assert "T" in payload["collected_at"]
    assert "quota" in payload
    assert "refresh_date" in payload["quota"]
    assert payload["quota"]["refresh_date"].endswith("+00:00")


def test_build_notification_message_contains_key_fields() -> None:
    report = collect_runtime_status("ibmq_fake", service=_FakeService())
    message = build_notification_message(report)

    assert "IBM runtime status" in message
    assert "Queue depth" in message
    assert "Quota" in message
    assert "Plan" in message


def test_post_to_webhook_dry_run() -> None:
    # Should not raise when dry_run=True even with invalid URL.
    post_to_webhook("https://example.com/webhook", "payload", dry_run=True)


def test_compute_budgeting_hints_uses_remaining_seconds() -> None:
    report = collect_runtime_status("ibmq_fake", service=_FakeService())
    hints = compute_budgeting_hints(
        report, shots_per_second=10.0, batch_seconds=600, calibration_shots=100
    )

    assert hints["assumptions"]["shots_per_second"] == 10.0
    assert hints["shot_capacity"]["estimated_total_shots"] == 4800
    assert hints["shot_capacity"]["estimated_batch_shots"] == 4800
    assert hints["shot_capacity"]["measurement_shots_available"] == 4700
    assert hints["shot_capacity"]["calibration_shots"] == 100
    assert isinstance(hints["fallbacks"], list)


def test_compute_budgeting_hints_rejects_invalid_settings() -> None:
    report = collect_runtime_status("ibmq_fake", service=_FakeService())

    with pytest.raises(ValueError):
        compute_budgeting_hints(report, shots_per_second=0.0)
    with pytest.raises(ValueError):
        compute_budgeting_hints(report, shots_per_second=1.0, batch_seconds=0)
    with pytest.raises(ValueError):
        compute_budgeting_hints(report, shots_per_second=1.0, calibration_shots=-1)
