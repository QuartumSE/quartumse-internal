from __future__ import annotations

import json
import sys
from pathlib import Path

import math
from statistics import mean

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.pipeline import analyze_experiment, execute_experiment
from experiments.pipeline import analyzer as analyzer_module
from experiments.pipeline.metadata_schema import ExperimentMetadata


@pytest.fixture
def example_metadata() -> ExperimentMetadata:
    metadata_path = (
        Path(__file__).resolve().parents[2]
        / "experiments"
        / "shadows"
        / "examples"
        / "extended_ghz"
        / "experiment_metadata.yaml"
    )
    with metadata_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)

    metadata = ExperimentMetadata.model_validate(payload)
    return metadata.model_copy(update={"device": "aer_simulator"})


def _load_manifest(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_analyze_experiment_aer(tmp_path: Path, example_metadata: ExperimentMetadata) -> None:
    outputs = execute_experiment(example_metadata, tmp_path, backend="aer_simulator")

    manifest_v0 = _load_manifest(outputs["manifest_v0"])
    manifest_v1 = _load_manifest(outputs["manifest_v1"])
    manifest_baseline = _load_manifest(outputs["manifest_baseline"])

    ground_truth = {
        "observables": {
            "ZIII": {"expectation": 0.0},
            "IZII": {"expectation": 0.0},
            "IIZI": {"expectation": 0.0},
            "IIIZ": {"expectation": 0.0},
            "ZZZZ": {"expectation": 1.0},
        },
        "stabilizers": ["ZIII", "IZII", "IIZI", "IIIZ", "ZZZZ"],
    }

    analysis = analyze_experiment(
        manifest_v0=manifest_v0,
        manifest_v1=manifest_v1,
        manifest_baseline=manifest_baseline,
        ground_truth=ground_truth,
        targets={"ssr_average": 1.5, "ci_coverage": 0.9},
    )

    assert "per_observable" in analysis
    assert "summary_metrics" in analysis
    assert "plots_data" in analysis

    per_obs_v1 = analysis["per_observable"]["v1"]
    assert set(per_obs_v1) == {
        "1.0*ZIII",
        "1.0*IZII",
        "1.0*IIZI",
        "1.0*IIIZ",
        "1.0*ZZZZ",
    }

    canonical = analyzer_module._canonical_name  # type: ignore[attr-defined]
    baseline_results = {
        canonical(name): payload
        for name, payload in manifest_baseline["results_summary"].items()
    }
    v0_results = {
        canonical(name): payload
        for name, payload in manifest_v0["results_summary"].items()
    }
    v1_results = {
        canonical(name): payload
        for name, payload in manifest_v1["results_summary"].items()
    }

    truth_map = {
        canonical(name): value["expectation"]
        for name, value in ground_truth["observables"].items()
    }

    mae_expected = mean(
        abs(v1_results[name]["expectation_value"] - truth_map[name])
        for name in truth_map
    )

    ci_flags = []
    for name in truth_map:
        ci = v1_results[name].get("ci_95")
        if not ci:
            continue
        lower, upper = ci
        ci_flags.append(1.0 if lower <= truth_map[name] <= upper else 0.0)
    ci_expected = mean(ci_flags) if ci_flags else math.nan

    ssr_values = []
    for name in truth_map:
        baseline_error = abs(baseline_results[name]["expectation"] - truth_map[name])
        approach_error = abs(v1_results[name]["expectation_value"] - truth_map[name])
        denom = max(approach_error, 1e-12)
        ssr_values.append(baseline_error / denom)
    ssr_expected = mean(ssr_values)

    summary = analysis["summary_metrics"]
    assert summary["mae"] == pytest.approx(mae_expected, rel=1e-6)
    if ci_flags:
        assert summary["ci_coverage"] == pytest.approx(ci_expected, rel=1e-6)
    else:
        assert summary["ci_coverage"] is None
    assert summary["ssr_average"] == pytest.approx(ssr_expected, rel=1e-6)

    plots = analysis["plots_data"]
    expected_observables = sorted(
        name
        for name in truth_map
        if name in baseline_results and name in v0_results and name in v1_results
    )
    assert plots["observables"] == expected_observables

    expected_baseline_errors = [
        abs(baseline_results[name]["expectation"] - truth_map[name])
        for name in expected_observables
    ]
    expected_v0_errors = [
        abs(v0_results[name]["expectation_value"] - truth_map[name])
        for name in expected_observables
    ]
    expected_v1_errors = [
        abs(v1_results[name]["expectation_value"] - truth_map[name])
        for name in expected_observables
    ]

    assert plots["baseline_errors"] == pytest.approx(expected_baseline_errors, rel=1e-6)
    assert plots["v0_errors"] == pytest.approx(expected_v0_errors, rel=1e-6)
    assert plots["v1_errors"] == pytest.approx(expected_v1_errors, rel=1e-6)
    assert plots["ground_truth"] == [truth_map[name] for name in expected_observables]

    fidelity = analysis.get("stabilizer_fidelity_lower_bound")
    stabilizer_values = [v1_results[name]["expectation_value"] for name in truth_map]
    fidelity_expected = (1.0 + mean(stabilizer_values)) / 2.0
    assert fidelity == pytest.approx(fidelity_expected, rel=1e-6)

    assert analysis["targets"] == {"ssr_average": 1.5, "ci_coverage": 0.9}
