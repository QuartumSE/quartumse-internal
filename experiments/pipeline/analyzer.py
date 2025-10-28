"""Stage-3 analysis helpers for Phase-1 experiment manifests."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

import numpy as np

from quartumse.reporting.manifest import ManifestSchema, ProvenanceManifest
from quartumse.utils.metrics import (
    build_observable_comparison,
    compute_ci_coverage,
    compute_mae,
    compute_ssr_equal_budget,
    summarise_observable_comparisons,
)


Number = float | int


def _load_manifest(manifest: Any) -> ProvenanceManifest:
    """Normalise ``manifest`` into a :class:`ProvenanceManifest` instance."""

    if isinstance(manifest, ProvenanceManifest):
        return manifest
    if isinstance(manifest, Mapping):
        schema = ManifestSchema.model_validate(manifest)
        return ProvenanceManifest(schema)
    raise TypeError("Manifest payload must be a mapping or ProvenanceManifest")


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


def _extract_observable_payloads(manifest: ProvenanceManifest) -> Dict[str, Dict[str, Any]]:
    """Return manifest result payloads keyed by canonical observable names."""

    results: Dict[str, Dict[str, Any]] = {}
    for name, payload in manifest.schema.results_summary.items():
        results[_canonical_name(name)] = dict(payload)
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
) -> Dict[str, Any]:
    """Aggregate Phase-1 metrics from experiment manifests."""

    baseline_manifest = _load_manifest(manifest_baseline)
    v0_manifest = _load_manifest(manifest_v0)
    v1_manifest = _load_manifest(manifest_v1)

    baseline_obs = _extract_observable_payloads(baseline_manifest)
    v0_obs = _extract_observable_payloads(v0_manifest)
    v1_obs = _extract_observable_payloads(v1_manifest)

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

    return result

