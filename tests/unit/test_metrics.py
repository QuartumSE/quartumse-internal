import pytest

from quartumse.utils.metrics import compute_ssr


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
