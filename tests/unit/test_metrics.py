import numpy as np
import pytest

from quartumse.utils.metrics import (
    ConfidenceInterval,
    bootstrap_summary,
    build_observable_comparison,
    compute_ci_coverage,
    compute_ssr,
    summarise_observable_comparisons,
)


def test_compute_ssr_counts_calibration_shots_in_total():
    baseline_shots = 5_000
    measurement_shots = 1_200
    calibration_shots = 800
    quartumse_total_shots = measurement_shots + calibration_shots

    expected_ssr = baseline_shots / quartumse_total_shots

    assert compute_ssr(baseline_shots, quartumse_total_shots) == pytest.approx(expected_ssr)


def test_compute_ssr_applies_precision_scaling_with_calibration_total():
    baseline_shots = 5_000
    measurement_shots = 900
    calibration_shots = 600
    quartumse_total_shots = measurement_shots + calibration_shots

    baseline_precision = 0.04
    quartumse_precision = 0.02

    expected_ssr = (baseline_shots / quartumse_total_shots) * (
        (baseline_precision / quartumse_precision) ** 2
    )

    assert compute_ssr(
        baseline_shots,
        quartumse_total_shots,
        baseline_precision=baseline_precision,
        quartumse_precision=quartumse_precision,
    ) == pytest.approx(expected_ssr)


def test_compute_ssr_supports_variance_precision_modes():
    baseline_shots = 10_000
    approach_shots = 2_500
    baseline_variance = 0.04
    approach_variance = 0.01

    expected_ssr = (baseline_shots / approach_shots) * (baseline_variance / approach_variance)

    ssr = compute_ssr(
        baseline_shots,
        approach_shots,
        baseline_precision=baseline_variance,
        quartumse_precision=approach_variance,
        baseline_precision_mode="variance",
        quartumse_precision_mode="variance",
    )

    assert ssr == pytest.approx(expected_ssr)


def test_compute_ci_coverage_supports_weights():
    intervals = [
        ConfidenceInterval(lower=-0.2, upper=0.2),
        ConfidenceInterval(lower=0.4, upper=0.6),
    ]
    truths = [0.0, 0.7]
    weights = [1.0, 2.0]

    coverage = compute_ci_coverage(intervals, truths, weights)

    assert coverage == pytest.approx(1.0 / 3.0)


def test_bootstrap_summary_returns_expected_structure():
    rng = np.random.default_rng(42)
    summary = bootstrap_summary([1, 2, 3, 4], n_resamples=512, random_state=rng)

    assert summary.samples == 512
    assert summary.estimate == pytest.approx(2.5, abs=0.1)
    assert summary.variance > 0
    assert summary.confidence_interval.lower < summary.confidence_interval.upper


def test_observable_comparison_and_summary_pipeline():
    baseline_payload = {"expectation": 0.4, "variance": 0.04}
    approach_payload = {
        "expectation": 0.42,
        "variance": 0.01,
        "confidence_interval": {"lower": 0.3, "upper": 0.5},
        "expected": 0.5,
    }

    comparison = build_observable_comparison(
        "Z",
        baseline_payload,
        approach_payload,
        baseline_total_shots=10_000,
        approach_total_shots=2_500,
    )

    assert comparison.variance_ratio == pytest.approx(4.0)
    assert comparison.in_ci is True
    assert comparison.ssr == pytest.approx((10_000 / 2_500) * 4.0)

    summary = summarise_observable_comparisons([comparison])
    assert summary.total_observables == 1
    assert summary.ssr_average == pytest.approx(comparison.ssr)
    assert summary.ci_coverage == pytest.approx(1.0)
    assert summary.variance_ratio_average == pytest.approx(4.0)

    summary_dict = summary.to_dict()
    assert summary_dict["observables"]["Z"]["ssr"] == pytest.approx(comparison.ssr)
