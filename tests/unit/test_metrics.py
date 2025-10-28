import math

import pytest

from quartumse.utils.metrics import (
    SSR_EQUAL_BUDGET_EPSILON,
    compute_ci_coverage,
    compute_mae,
    compute_ssr_equal_budget,
)


def test_compute_mae_perfect_agreement_returns_zero():
    results = {
        "ZII": {"expectation_value": 0.5, "ci_95": (0.3, 0.7), "expected": 0.5},
        "XII": {"expectation_value": -0.3, "ci_width": 0.2, "expected": -0.3},
    }
    truths = {"ZII": {"expectation_value": 0.5}, "XII": {"expectation_value": -0.3}}

    mae = compute_mae(results, truths)

    assert mae == pytest.approx(0.0)


def test_compute_mae_uses_observable_intersection():
    results = {
        "A": {"expectation_value": 0.2, "expected": 0.0},
        "B": {"expectation_value": -0.1, "expected": 0.5},
        "C": {"expectation_value": 0.9, "expected": 0.8},
    }
    truths = {"A": 0.0, "B": 0.5}

    mae = compute_mae(results, truths)

    assert mae == pytest.approx((0.2 + 0.6) / 2.0)


def test_compute_ci_coverage_mixed_interval_sources():
    results = {
        "A": {"expectation_value": 0.5, "ci_95": (0.3, 0.7)},
        "B": {"expectation_value": 0.0, "ci_width": 0.4},
        "C": {"expectation_value": 0.1},
    }
    truths = {
        "A": {"expectation_value": 0.6},
        "B": {"expectation_value": 0.3},
        "C": {"expectation_value": 0.1},
    }

    coverage = compute_ci_coverage(results, truths)

    assert coverage == pytest.approx(0.5)


def test_compute_ci_coverage_returns_nan_when_missing_intervals():
    results = {"A": {"expectation_value": 0.2}, "B": {"expectation_value": -0.1}}
    truths = {"A": 0.1, "B": -0.2}

    coverage = compute_ci_coverage(results, truths)

    assert math.isnan(coverage)


def test_compute_ssr_equal_budget_uses_observable_intersection():
    baseline = {
        "A": {"expectation_value": 0.8, "expected": 0.5},
        "B": {"expectation_value": -0.3, "expected": 0.1},
    }
    approach = {
        "B": {"expectation_value": -0.1, "expected": 0.1},
        "C": {"expectation_value": 0.0, "expected": 0.0},
    }

    ssr = compute_ssr_equal_budget(baseline, approach)

    # Only observable B is shared → | -0.3 - 0.1 | / | -0.1 - 0.1 | = 0.4 / 0.2 = 2.0
    assert ssr == pytest.approx(2.0)


def test_compute_ssr_equal_budget_guards_against_zero_division():
    baseline = {"A": {"error": 0.2}}
    approach = {"A": {"error": 0.0}}

    ssr = compute_ssr_equal_budget(baseline, approach)

    assert math.isfinite(ssr)
    assert ssr == pytest.approx(0.2 / SSR_EQUAL_BUDGET_EPSILON)
