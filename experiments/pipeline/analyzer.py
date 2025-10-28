"""Stage-3 analysis helpers for Phase-1 experiment manifests."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

import numpy as np

from quartumse.reporting.manifest import ManifestSchema, ProvenanceManifest
from quartumse.reporting.manifest_io import extract_observable_table, load_manifest
from quartumse.utils.metrics import (
    build_observable_comparison,
    compute_ci_coverage,
    compute_mae,
    compute_ssr_equal_budget,
    summarise_observable_comparisons,
)


Number = float | int


def _load_manifest(manifest: Any) -> tuple[ProvenanceManifest, Mapping[str, Any]]:
    """Normalise ``manifest`` into schema and raw dictionary payload."""

    if isinstance(manifest, ProvenanceManifest):
        schema = manifest
        payload = manifest.schema.model_dump()
        return schema, payload

    if isinstance(manifest, (str, Path)):
        manifest_dict = load_manifest(manifest)
    elif isinstance(manifest, Mapping):
        manifest_dict = dict(manifest)
    else:
        raise TypeError(
            "Manifest payload must be a path, mapping, or ProvenanceManifest instance"
        )

    schema = ManifestSchema.model_validate(manifest_dict)
    return ProvenanceManifest(schema), manifest_dict


def _canonical_name(name: str) -> str:
    name = str(name).strip()
    if "*" in name:
        coef_str, pauli = name.split("*", 1)
        try:
            coefficient = float(coef_str)
        except ValueError:
            return name
    else:
        coefficient = 1.0
        pauli = name
    return f"{coefficient}*{pauli.strip()}"


def _extract_observable_payloads(
    manifest: ProvenanceManifest, manifest_payload: Mapping[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """Return manifest result payloads keyed by canonical observable names."""

    results: Dict[str, Dict[str, Any]] = {}

    summary = manifest.schema.results_summary or {}
    for name, payload in summary.items():
        canonical = _canonical_name(name)
        if isinstance(payload, Mapping):
            results[canonical] = dict(payload)
        else:
            results[canonical] = {"expectation_value": payload}

    normalized_table = extract_observable_table(manifest_payload)
    for name, stats in normalized_table.items():
        canonical = _canonical_name(name)
        payload = results.setdefault(canonical, {})
        expectation = stats.get("expectation")
        if expectation is not None and "expectation_value" not in payload:
            payload["expectation_value"] = float(expectation)
        if expectation is not None and "expectation" not in payload:
            payload["expectation"] = float(expectation)
        variance = stats.get("variance")
        if variance is not None and "variance" not in payload:
            payload["variance"] = float(variance)
        lower = stats.get("ci_lower")
        upper = stats.get("ci_upper")
        if (lower is not None or upper is not None) and "ci_95" not in payload:
            payload["ci_95"] = (lower, upper)

    return results


def _extract_expectation(payload: Optional[Mapping[str, Any]]) -> Optional[float]:
    if not payload:
        return None
    for key in ("expectation_value", "expectation", "value", "estimate"):
        value = payload.get(key) if isinstance(payload, Mapping) else None
        if value is not None:
            return float(value)
    if isinstance(payload, Mapping) and "ground_truth" in payload and payload["ground_truth"] is not None:
        return float(payload["ground_truth"])
    return None


def _normalise_ground_truth(
    ground_truth: Optional[Mapping[str, Any]]
) -> Tuple[Dict[str, Dict[str, Number]], Tuple[str, ...]]:
    if ground_truth is None:
        return {}, ()

    if "observables" in ground_truth:
        observable_map = ground_truth["observables"]
    else:
        observable_map = ground_truth

    normalised: Dict[str, Dict[str, Number]] = {}
    for name, payload in observable_map.items():
        canonical = _canonical_name(name)
        if isinstance(payload, Mapping):
            expectation = None
            for key in ("expectation", "value", "target"):
                if key in payload and payload[key] is not None:
                    expectation = float(payload[key])
                    break
            if expectation is None:
                continue
            normalised[canonical] = {"expectation": expectation}
        else:
            normalised[canonical] = {"expectation": float(payload)}

    stabilizers: Iterable[str]
    if "stabilizers" in ground_truth and isinstance(ground_truth["stabilizers"], Iterable):
        stabilizers = tuple(_canonical_name(name) for name in ground_truth["stabilizers"])
    else:
        stabilizers = ()

    return normalised, tuple(stabilizers)


def _attach_ground_truth(
    observables: Mapping[str, Mapping[str, Any]],
    ground_truth: Mapping[str, Mapping[str, Number]],
) -> Dict[str, Dict[str, Any]]:
    enriched: Dict[str, Dict[str, Any]] = {}
    for name, payload in observables.items():
        enriched_payload: Dict[str, Any] = dict(payload)
        truth = ground_truth.get(name)
        if truth and "expectation" in truth:
            enriched_payload.setdefault("ground_truth", truth["expectation"])
        enriched[name] = enriched_payload
    return enriched


def _compute_mae(
    observables: Mapping[str, Mapping[str, Any]],
    ground_truth: Mapping[str, Mapping[str, Number]],
) -> Optional[float]:
    if not ground_truth:
        return None
    try:
        return compute_mae(observables, ground_truth)
    except ValueError:
        return None


def _compute_ci_coverage(
    observables: Mapping[str, Mapping[str, Any]],
    ground_truth: Mapping[str, Mapping[str, Number]],
) -> Optional[float]:
    if not ground_truth:
        return None
    coverage = compute_ci_coverage(observables, ground_truth)
    if np.isnan(coverage):
        return None
    return float(coverage)


def _compute_ssr_equal_budget(
    baseline: Mapping[str, Mapping[str, Any]],
    approach: Mapping[str, Mapping[str, Any]],
    ground_truth: Mapping[str, Mapping[str, Number]],
) -> Optional[float]:
    if not ground_truth:
        return None
    baseline_truth = _attach_ground_truth(baseline, ground_truth)
    approach_truth = _attach_ground_truth(approach, ground_truth)
    try:
        return compute_ssr_equal_budget(baseline_truth, approach_truth)
    except ValueError:
        return None


def _build_comparisons(
    baseline: Mapping[str, Mapping[str, Any]],
    approach: Mapping[str, Mapping[str, Any]],
    *,
    baseline_shots: int,
    approach_shots: int,
) -> Dict[str, Dict[str, Any]]:
    comparisons = []
    for name in sorted(set(baseline) & set(approach)):
        comparison = build_observable_comparison(
            name,
            baseline[name],
            approach[name],
            baseline_total_shots=baseline_shots,
            approach_total_shots=approach_shots,
        )
        comparisons.append(comparison)

    summary = summarise_observable_comparisons(comparisons)
    return {name: item.to_dict() for name, item in summary.comparisons.items()}


def _prepare_plots_data(
    baseline: Mapping[str, Mapping[str, Any]],
    v0: Mapping[str, Mapping[str, Any]],
    v1: Mapping[str, Mapping[str, Any]],
    ground_truth: Mapping[str, Mapping[str, Number]],
) -> Dict[str, Any]:
    names = sorted(set(baseline) | set(v0) | set(v1))
    observables: list[str] = []
    baseline_errors: list[float] = []
    v0_errors: list[float] = []
    v1_errors: list[float] = []
    truth_values: list[float] = []

    for name in names:
        truth_payload = ground_truth.get(name)
        truth_value = None
        if truth_payload is not None:
            truth_value = truth_payload.get("expectation")
        if truth_value is None:
            continue

        baseline_expect = _extract_expectation(baseline.get(name))
        v0_expect = _extract_expectation(v0.get(name))
        v1_expect = _extract_expectation(v1.get(name))

        if baseline_expect is None or v0_expect is None or v1_expect is None:
            continue

        observables.append(name)
        truth_values.append(float(truth_value))
        baseline_errors.append(abs(baseline_expect - truth_value))
        v0_errors.append(abs(v0_expect - truth_value))
        v1_errors.append(abs(v1_expect - truth_value))

    return {
        "observables": observables,
        "baseline_errors": baseline_errors,
        "v0_errors": v0_errors,
        "v1_errors": v1_errors,
        "ground_truth": truth_values,
    }


def _compute_stabilizer_fidelity(
    approach: Mapping[str, Mapping[str, Any]],
    stabilizers: Iterable[str],
) -> Optional[float]:
    values: list[float] = []
    for name in stabilizers:
        expectation = _extract_expectation(approach.get(name))
        if expectation is None:
            continue
        values.append(expectation)

    if not values:
        return None

    average = float(np.mean(values))
    fidelity = (1.0 + average) / 2.0
    return float(min(1.0, max(0.0, fidelity)))


def analyze_experiment(
    manifest_v0: Any,
    manifest_v1: Any,
    manifest_baseline: Any,
    ground_truth: Optional[Dict[str, Any]] = None,
    targets: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Aggregate Phase-1 metrics from experiment manifests."""

    baseline_manifest, baseline_payload = _load_manifest(manifest_baseline)
    v0_manifest, v0_payload = _load_manifest(manifest_v0)
    v1_manifest, v1_payload = _load_manifest(manifest_v1)

    baseline_obs = _extract_observable_payloads(baseline_manifest, baseline_payload)
    v0_obs = _extract_observable_payloads(v0_manifest, v0_payload)
    v1_obs = _extract_observable_payloads(v1_manifest, v1_payload)

    truth_map, stabilizers = _normalise_ground_truth(ground_truth)

    baseline_shots = baseline_manifest.schema.resource_usage.total_shots
    v0_shots = v0_manifest.schema.resource_usage.total_shots
    v1_shots = v1_manifest.schema.resource_usage.total_shots

    per_observable = {
        "v0": _build_comparisons(baseline_obs, v0_obs, baseline_shots=baseline_shots, approach_shots=v0_shots),
        "v1": _build_comparisons(baseline_obs, v1_obs, baseline_shots=baseline_shots, approach_shots=v1_shots),
    }

    mae = _compute_mae(_attach_ground_truth(v1_obs, truth_map), truth_map)
    ci_coverage = _compute_ci_coverage(_attach_ground_truth(v1_obs, truth_map), truth_map)
    ssr_average = _compute_ssr_equal_budget(baseline_obs, v1_obs, truth_map)

    plots_data = _prepare_plots_data(baseline_obs, v0_obs, v1_obs, truth_map)

    fidelity = _compute_stabilizer_fidelity(v1_obs, stabilizers) if stabilizers else None

    result: Dict[str, Any] = {
        "per_observable": per_observable,
        "summary_metrics": {
            "mae": mae,
            "ci_coverage": ci_coverage,
            "ssr_average": ssr_average,
        },
        "plots_data": plots_data,
    }

    if fidelity is not None:
        result["stabilizer_fidelity_lower_bound"] = fidelity

    if targets:
        normalised_targets: Dict[str, float] = {}
        for key, value in targets.items():
            try:
                normalised_targets[key] = float(value)
            except (TypeError, ValueError):
                continue
        if normalised_targets:
            result["targets"] = normalised_targets

    return result

