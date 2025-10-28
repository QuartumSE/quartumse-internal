"""Stage-4 reporter utilities for building HTML/PDF artefacts."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

import math

import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader, select_autoescape

from experiments.pipeline.metadata_schema import ExperimentMetadata

_TEMPLATE_NAME = "report_template.html.jinja2"
_TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"
_REDACTED_PLACEHOLDER = "[redacted]"
_SENSITIVE_ENV_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "KEY")


def _is_sensitive_env_name(name: str) -> bool:
    upper = name.upper()
    return any(marker in upper for marker in _SENSITIVE_ENV_MARKERS)


def _collect_sensitive_env_values(min_length: int = 6) -> tuple[str, ...]:
    values: set[str] = set()
    for key, value in os.environ.items():
        if not value:
            continue
        if len(value) < min_length:
            continue
        if _is_sensitive_env_name(key):
            values.add(value)
    return tuple(sorted(values, key=len, reverse=True))


def _normalise_path(value: Path, *, output_dir: Path) -> str:
    value_path = Path(value)
    try:
        resolved_value = value_path.resolve()
    except (OSError, RuntimeError):
        resolved_value = value_path

    resolved_output = output_dir.resolve()
    try:
        relative = resolved_value.relative_to(resolved_output)
        return relative.as_posix()
    except ValueError:
        repo_root = Path(__file__).resolve().parents[2]
        try:
            relative = resolved_value.relative_to(repo_root)
            return relative.as_posix()
        except ValueError:
            try:
                rel_str = os.path.relpath(resolved_value, resolved_output)
            except (OSError, ValueError):
                return resolved_value.name
            rel_path = Path(rel_str)
            return rel_path.as_posix()


def _sanitize_text(value: str, *, output_dir: Path, secrets: Sequence[str]) -> str:
    sanitised = value

    home_dir = str(Path.home())
    if home_dir and home_dir in sanitised:
        sanitised = sanitised.replace(home_dir, "~")

    for secret in secrets:
        if secret and secret in sanitised:
            sanitised = sanitised.replace(secret, _REDACTED_PLACEHOLDER)

    stripped = sanitised.strip()
    if stripped == sanitised and stripped:
        path_candidate = Path(stripped)
        if path_candidate.is_absolute():
            return _normalise_path(path_candidate, output_dir=output_dir)

    return sanitised


def _sanitize_structure(value: Any, *, output_dir: Path, secrets: Sequence[str]) -> Any:
    if isinstance(value, Mapping):
        return {key: _sanitize_structure(item, output_dir=output_dir, secrets=secrets) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_structure(item, output_dir=output_dir, secrets=secrets) for item in value]
    if isinstance(value, tuple):
        return tuple(_sanitize_structure(item, output_dir=output_dir, secrets=secrets) for item in value)
    if isinstance(value, Path):
        return _normalise_path(value, output_dir=output_dir)
    if isinstance(value, str):
        return _sanitize_text(value, output_dir=output_dir, secrets=secrets)
    return value


@dataclass
class _StatusTile:
    metric: str
    label: str
    value_display: str
    target_display: str
    passed: bool


def _normalise_metadata(metadata: ExperimentMetadata | Mapping[str, Any]) -> ExperimentMetadata:
    if isinstance(metadata, ExperimentMetadata):
        return metadata
    if isinstance(metadata, Mapping):
        return ExperimentMetadata.model_validate(metadata)
    raise TypeError("metadata must be ExperimentMetadata or mapping")


def _ensure_output_path(output_path: Path) -> tuple[Path, Path]:
    output_path = Path(output_path)
    if output_path.suffix.lower() != ".html":
        output_dir = output_path
        output_path = output_dir / "report.html"
    else:
        output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_path, output_dir


def _create_environment() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    def _format_number(value: Any) -> str:
        if value is None:
            return "—"
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        if math.isfinite(number):
            if abs(number) >= 1000:
                return f"{number:,.0f}"
            return f"{number:.3f}".rstrip("0").rstrip(".")
        return "nan"

    env.filters["number"] = _format_number
    return env


def _format_metric_value(value: Optional[float], *, percentage: bool = False) -> str:
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return "N/A"
    if percentage:
        return f"{value:.1%}"
    return f"{value:.3f}"


def _build_status_tiles(summary: Mapping[str, Any], targets: Mapping[str, float]) -> list[_StatusTile]:
    tiles: list[_StatusTile] = []
    ssr_value = summary.get("ssr_average")
    ssr_target = float(targets.get("ssr_average", 1.0))
    if ssr_value is not None:
        tiles.append(
            _StatusTile(
                metric="ssr_average",
                label="Shot-Savings Ratio",
                value_display=_format_metric_value(ssr_value),
                target_display=_format_metric_value(ssr_target),
                passed=ssr_value >= ssr_target,
            )
        )
    ci_value = summary.get("ci_coverage")
    ci_target = float(targets.get("ci_coverage", 0.95))
    if ci_value is not None:
        tiles.append(
            _StatusTile(
                metric="ci_coverage",
                label="CI Coverage",
                value_display=_format_metric_value(ci_value, percentage=True),
                target_display=_format_metric_value(ci_target, percentage=True),
                passed=ci_value >= ci_target,
            )
        )
    return tiles


def _build_key_metrics(summary: Mapping[str, Any], analysis: Mapping[str, Any]) -> list[Dict[str, str]]:
    entries: list[Dict[str, str]] = []
    mae = summary.get("mae")
    entries.append(
        {
            "label": "Mean Absolute Error",
            "value": _format_metric_value(mae),
            "detail": "Lower is better",
        }
    )
    if "stabilizer_fidelity_lower_bound" in analysis:
        entries.append(
            {
                "label": "Stabilizer Fidelity (LB)",
                "value": _format_metric_value(analysis["stabilizer_fidelity_lower_bound"]),
                "detail": None,
            }
        )
    entries.append(
        {
            "label": "CI Coverage",
            "value": _format_metric_value(summary.get("ci_coverage"), percentage=True),
            "detail": "Fraction of truth estimates inside 95% CI",
        }
    )
    entries.append(
        {
            "label": "Average SSR",
            "value": _format_metric_value(summary.get("ssr_average")),
            "detail": "Improvement vs. baseline",
        }
    )
    return entries


def _build_per_observable_rows(per_obs: Mapping[str, Mapping[str, Any]]) -> list[Dict[str, str]]:
    rows: list[Dict[str, str]] = []
    for name in sorted(per_obs):
        payload = per_obs[name]
        baseline = payload.get("baseline", {})
        approach = payload.get("approach", {})
        rows.append(
            {
                "name": name,
                "baseline": _format_metric_value(baseline.get("expectation")),
                "approach": _format_metric_value(approach.get("expectation")),
                "ssr": _format_metric_value(payload.get("ssr")),
                "in_ci": "Yes" if payload.get("in_ci") else "No",
                "variance_ratio": _format_metric_value(payload.get("variance_ratio")),
            }
        )
    return rows


def _generate_figures(analysis: Mapping[str, Any], figures_dir: Path) -> list[Dict[str, str]]:
    plots = analysis.get("plots_data") or {}
    observables: Iterable[str] = plots.get("observables") or []
    observables = list(observables)
    results: list[Dict[str, str]] = []

    if observables:
        baseline_errors = plots.get("baseline_errors") or []
        v0_errors = plots.get("v0_errors") or []
        v1_errors = plots.get("v1_errors") or []

        x = range(len(observables))
        fig, ax = plt.subplots(figsize=(8, 4.5))
        width = 0.25
        ax.bar([i - width for i in x], baseline_errors, width=width, label="Baseline")
        ax.bar(x, v0_errors, width=width, label="v0")
        ax.bar([i + width for i in x], v1_errors, width=width, label="v1")
        ax.set_xticks(list(x))
        ax.set_xticklabels(observables, rotation=45, ha="right")
        ax.set_ylabel("Absolute error")
        ax.set_title("Absolute error vs. ground truth")
        ax.legend()
        fig.tight_layout()

        figures_dir.mkdir(parents=True, exist_ok=True)
        path = figures_dir / "observable_errors.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        results.append({"path": path.relative_to(figures_dir.parent).as_posix(), "caption": "Absolute error across observables"})

    per_obs_v1 = (analysis.get("per_observable") or {}).get("v1") or {}
    if per_obs_v1:
        names = sorted(per_obs_v1)
        ssr_values = [per_obs_v1[name].get("ssr") or 0.0 for name in names]
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.bar(names, ssr_values, color="#6366F1")
        ax.set_ylabel("SSR")
        ax.set_title("Shot-savings ratio by observable")
        ax.tick_params(axis="x", rotation=45)
        fig.tight_layout()

        figures_dir.mkdir(parents=True, exist_ok=True)
        path = figures_dir / "ssr_by_observable.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        results.append({"path": path.relative_to(figures_dir.parent).as_posix(), "caption": "Shot-savings ratio per observable"})

    return results


def _resolve_discussion(metadata: ExperimentMetadata, summary: Mapping[str, Any], analysis: Mapping[str, Any]) -> str:
    template = metadata.discussion_template or ""
    if not template.strip():
        return ""

    def _prepare(value: Any) -> Any:
        if value is None:
            return float("nan")
        return value

    context = {
        "mae": _prepare(summary.get("mae")),
        "ci_coverage": _prepare(summary.get("ci_coverage")),
        "ssr_average": _prepare(summary.get("ssr_average")),
        "stabilizer_fidelity": _prepare(analysis.get("stabilizer_fidelity_lower_bound")),
    }
    try:
        return template.format(**context)
    except Exception:
        return template


def _normalise_artifacts(artifacts: Mapping[str, Any]) -> Dict[str, Any]:
    normalised: Dict[str, Any] = {}
    for key, value in artifacts.items():
        normalised[key] = str(value)
    return normalised


def _build_verification_table(verification: Mapping[str, Any]) -> list[Dict[str, str]]:
    table: list[Dict[str, str]] = []
    for key, label in (
        ("manifest_exists", "Manifest present"),
        ("manifest_valid", "Manifest valid"),
        ("shot_data_exists", "Shot data available"),
        ("shot_data_checksum_matches", "Shot data checksum"),
        ("mem_confusion_matrix_exists", "MEM confusion matrix"),
        (
            "mem_confusion_matrix_checksum_matches",
            "MEM checksum",
        ),
        ("replay_matches", "Estimator replay"),
    ):
        value = verification.get(key)
        if value is None:
            display = "Unknown"
        elif isinstance(value, bool):
            display = "Yes" if value else "No"
        else:
            display = str(value)
        table.append({"label": label, "value": display})

    errors = verification.get("errors") or []
    if errors:
        table.append({"label": "Errors", "value": "; ".join(str(item) for item in errors)})
    return table


def generate_report(
    metadata: ExperimentMetadata | Mapping[str, Any],
    artifacts: Mapping[str, Any],
    analysis: Mapping[str, Any],
    verification: Mapping[str, Any],
    output_path: Path,
) -> Path:
    """Render the HTML (and optional PDF) report to ``output_path``."""

    metadata_model = _normalise_metadata(metadata)
    summary_metrics: Mapping[str, Any] = analysis.get("summary_metrics", {}) if analysis else {}

    output_path, output_dir = _ensure_output_path(output_path)
    normalized_artifacts = _normalise_artifacts(dict(artifacts))
    figures_dir = output_dir / "figures"
    figures = _generate_figures(analysis or {}, figures_dir)

    env = _create_environment()
    template = env.get_template(_TEMPLATE_NAME)

    targets: Dict[str, float] = {"ssr_average": 1.0, "ci_coverage": 0.95}
    if analysis and isinstance(analysis.get("targets"), Mapping):
        for key, value in analysis["targets"].items():
            try:
                targets[key] = float(value)
            except (TypeError, ValueError):
                continue

    status_tiles = _build_status_tiles(summary_metrics, targets)
    key_metrics = _build_key_metrics(summary_metrics, analysis or {})
    per_observable = _build_per_observable_rows((analysis or {}).get("per_observable", {}).get("v1", {}))
    discussion = _resolve_discussion(metadata_model, summary_metrics, analysis or {})
    verification_table = _build_verification_table(verification)

    secrets = _collect_sensitive_env_values()
    context = {
        "metadata": metadata_model.model_dump(),
        "artifacts": normalized_artifacts,
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ"),
        "executive_summary": discussion or "Key performance metrics are summarised below.",
        "status_tiles": [tile.__dict__ for tile in status_tiles],
        "key_metrics": key_metrics,
        "per_observable": per_observable,
        "figures": figures,
        "discussion": discussion,
        "verification": verification,
        "verification_table": verification_table,
        "references": analysis.get("references", []) if analysis else [],
        "build_info": "QuartumSE pipeline reporter",
    }
    sanitized_context = _sanitize_structure(context, output_dir=output_dir, secrets=secrets)

    rendered = template.render(**sanitized_context)

    output_path.write_text(rendered, encoding="utf-8")

    try:
        from weasyprint import HTML  # type: ignore

        pdf_path = output_path.with_suffix(".pdf")
        HTML(string=rendered, base_url=str(output_dir)).write_pdf(str(pdf_path))
    except Exception:
        pass

    return output_path


__all__ = ["generate_report"]
