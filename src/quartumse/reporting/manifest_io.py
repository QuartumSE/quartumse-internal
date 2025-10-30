"""Utility helpers for reading provenance manifest JSON files."""

from __future__ import annotations

import json
import os
from collections.abc import Iterable, Mapping, MutableMapping
from pathlib import Path
from typing import Any

ManifestDict = dict[str, Any]


def load_manifest(path: str | Path) -> ManifestDict:
    """Load a provenance manifest JSON file.

    Args:
        path: Path to the manifest JSON file.

    Returns:
        Parsed manifest dictionary.
    """

    manifest_path = Path(path)
    with manifest_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Manifest JSON must decode to a dictionary")
    return data


def extract_observable_table(
    manifest_dict: Mapping[str, Any],
) -> dict[str, dict[str, float | None]]:
    """Normalize observable estimates from a manifest dictionary.

    The manifest stores observable estimates within ``results_summary``.  Historically
    manifests have either used the summary dictionary directly or nested the entries
    under ``results_summary["observables"]``.  This helper accepts either layout and
    returns a consistent mapping of observable labels to expectation statistics.

    Args:
        manifest_dict: Parsed manifest dictionary.

    Returns:
        Dictionary mapping observable label to a normalized structure with the keys
        ``expectation``, ``variance``, ``ci_lower`` and ``ci_upper``.  Missing fields
        are represented as ``None``.
    """

    summary = manifest_dict.get("results_summary", {})
    observables_section: Any
    if isinstance(summary, Mapping) and "observables" in summary:
        observables_section = summary.get("observables", {})
    else:
        observables_section = summary

    if not isinstance(observables_section, Mapping):
        return {}

    normalized: dict[str, dict[str, float | None]] = {}
    for label, payload in observables_section.items():
        if not isinstance(payload, Mapping):
            continue
        expectation = _coerce_number(
            payload,
            ("expectation", "expectation_value", "value"),
        )
        variance = _coerce_number(payload, ("variance", "var"))
        ci_lower: float | None = None
        ci_upper: float | None = None

        if "ci_95" in payload:
            ci_lower, ci_upper = _coerce_interval(payload.get("ci_95"))
        elif "confidence_interval" in payload:
            ci_lower, ci_upper = _coerce_interval(payload.get("confidence_interval"))
        elif "ci" in payload:
            ci_lower, ci_upper = _coerce_interval(payload.get("ci"))

        normalized[label] = {
            "expectation": expectation,
            "variance": variance,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
        }

    return normalized


def extract_artifact_paths(manifest_dict: Mapping[str, Any]) -> dict[str, str | None]:
    """Return a dictionary of artifact paths referenced by the manifest.

    The helper is intentionally tolerant and will surface any ``*_path`` keys found
    within the manifest structure while ensuring commonly referenced keys are always
    present in the result.

    Args:
        manifest_dict: Parsed manifest dictionary.

    Returns:
        Mapping of artifact identifier to a normalized string path (or ``None``).
    """

    artifacts: MutableMapping[str, str | None] = {
        "shot_data_path": _normalize_path(manifest_dict.get("shot_data_path")),
        "confusion_matrix_path": None,
        "noise_model_path": None,
    }

    mitigation = manifest_dict.get("mitigation")
    if isinstance(mitigation, Mapping):
        artifacts["confusion_matrix_path"] = _normalize_path(
            mitigation.get("confusion_matrix_path")
        )

        for key, value in mitigation.items():
            if key.endswith("_path") and key not in artifacts:
                artifacts[key] = _normalize_path(value)

    shadows = manifest_dict.get("shadows")
    if isinstance(shadows, Mapping):
        artifacts["noise_model_path"] = _normalize_path(shadows.get("noise_model_path"))

        for key, value in shadows.items():
            if key.endswith("_path") and key not in artifacts:
                artifacts[key] = _normalize_path(value)

    # Collect additional *_path entries anywhere in the manifest to remain future-proof.
    for key, value in _iter_path_fields(manifest_dict):
        if key not in artifacts or artifacts[key] is None:
            artifacts[key] = _normalize_path(value)

    return dict(artifacts)


def _iter_path_fields(data: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(data, Mapping):
        for key, value in data.items():
            if isinstance(key, str) and key.endswith("_path"):
                yield key, value
            if isinstance(value, (Mapping, list, tuple)):
                yield from _iter_path_fields(value)
    elif isinstance(data, (list, tuple)):
        for item in data:
            yield from _iter_path_fields(item)


def _coerce_number(payload: Mapping[str, Any], keys: Iterable[str]) -> float | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return None


def _coerce_interval(value: Any) -> tuple[float | None, float | None]:
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        lower = value[0]
        upper = value[1]
        return (
            float(lower) if isinstance(lower, (int, float)) else None,
            float(upper) if isinstance(upper, (int, float)) else None,
        )
    if isinstance(value, Mapping):
        lower = value.get("lower")
        upper = value.get("upper")
        return (
            float(lower) if isinstance(lower, (int, float)) else None,
            float(upper) if isinstance(upper, (int, float)) else None,
        )
    return (None, None)


def _normalize_path(value: Any) -> str | None:
    if not isinstance(value, str):
        return None

    candidate = value.strip()
    if not candidate:
        return None

    # Preserve URI-style paths (e.g., s3://, gs://).
    if "://" in candidate:
        return candidate

    expanded = os.path.expanduser(candidate)
    return os.path.normpath(expanded)
