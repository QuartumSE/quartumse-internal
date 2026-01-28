"""Coverage verification and analysis (Measurements Bible §6.4).

This module provides utilities for verifying that confidence intervals
achieve their nominal coverage rates through simulation and empirical
testing.

Key metrics:
- Per-observable coverage: E[I(truth ∈ CI)] for each observable
- Family-wise coverage: P(all truths ∈ CIs simultaneously)
- Average coverage: Mean coverage across observables
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .confidence import ConfidenceInterval
from .fwer import FWERMethod, SimultaneousCIs


@dataclass
class CoverageResult:
    """Result of coverage verification.

    Attributes:
        n_replicates: Number of replicates analyzed.
        n_observables: Number of observables per replicate.
        per_observable_coverage: Coverage rate for each observable.
        average_coverage: Mean coverage across observables.
        family_wise_coverage: Fraction of replicates with all CIs covering.
        nominal_confidence: Nominal confidence level.
        coverage_deficit: nominal - average (positive = undercoverage).
        is_valid: Whether coverage meets nominal level (within tolerance).
    """

    n_replicates: int
    n_observables: int
    per_observable_coverage: list[float]
    average_coverage: float
    family_wise_coverage: float
    nominal_confidence: float
    coverage_deficit: float
    is_valid: bool

    @property
    def min_coverage(self) -> float:
        """Minimum per-observable coverage."""
        return min(self.per_observable_coverage)

    @property
    def max_coverage(self) -> float:
        """Maximum per-observable coverage."""
        return max(self.per_observable_coverage)


def compute_coverage(
    ci_results: list[list[ConfidenceInterval]],
    truth_values: list[float],
    tolerance: float = 0.02,
) -> CoverageResult:
    """Compute coverage statistics from CI results.

    Args:
        ci_results: List of CI lists, one per replicate. Each inner list
            contains CIs for all observables in that replicate.
        truth_values: Ground truth expectation values (one per observable).
        tolerance: Tolerance for coverage validation.

    Returns:
        CoverageResult with detailed coverage statistics.
    """
    n_replicates = len(ci_results)
    if n_replicates == 0:
        raise ValueError("No CI results provided")

    n_observables = len(truth_values)
    if n_observables == 0:
        raise ValueError("No truth values provided")

    # Verify dimensions
    for rep_idx, cis in enumerate(ci_results):
        if len(cis) != n_observables:
            raise ValueError(
                f"Replicate {rep_idx} has {len(cis)} CIs, expected {n_observables}"
            )

    # Get nominal confidence from first CI
    nominal_confidence = ci_results[0][0].confidence_level

    # Compute per-observable coverage
    per_obs_coverage = []
    for obs_idx in range(n_observables):
        truth = truth_values[obs_idx]
        covered = sum(
            1 for cis in ci_results if cis[obs_idx].contains(truth)
        )
        per_obs_coverage.append(covered / n_replicates)

    # Compute average coverage
    average_coverage = sum(per_obs_coverage) / n_observables

    # Compute family-wise coverage
    family_wise = sum(
        1
        for cis in ci_results
        if all(ci.contains(truth) for ci, truth in zip(cis, truth_values, strict=False))
    )
    family_wise_coverage = family_wise / n_replicates

    # Compute coverage deficit
    coverage_deficit = nominal_confidence - average_coverage

    # Validate coverage
    is_valid = coverage_deficit <= tolerance

    return CoverageResult(
        n_replicates=n_replicates,
        n_observables=n_observables,
        per_observable_coverage=per_obs_coverage,
        average_coverage=average_coverage,
        family_wise_coverage=family_wise_coverage,
        nominal_confidence=nominal_confidence,
        coverage_deficit=coverage_deficit,
        is_valid=is_valid,
    )


def compute_simultaneous_coverage(
    sim_ci_results: list[SimultaneousCIs],
    truth_values: list[float],
    tolerance: float = 0.02,
) -> CoverageResult:
    """Compute coverage statistics for simultaneous CI results.

    Args:
        sim_ci_results: List of SimultaneousCIs, one per replicate.
        truth_values: Ground truth expectation values.
        tolerance: Tolerance for coverage validation.

    Returns:
        CoverageResult with detailed coverage statistics.
    """
    # Extract individual CIs
    ci_results = [sim_ci.intervals for sim_ci in sim_ci_results]

    # Get nominal confidence from FWER adjustment
    nominal_confidence = sim_ci_results[0].coverage_guarantee

    result = compute_coverage(ci_results, truth_values, tolerance)

    # Override nominal confidence with family-wise guarantee
    return CoverageResult(
        n_replicates=result.n_replicates,
        n_observables=result.n_observables,
        per_observable_coverage=result.per_observable_coverage,
        average_coverage=result.average_coverage,
        family_wise_coverage=result.family_wise_coverage,
        nominal_confidence=nominal_confidence,
        coverage_deficit=nominal_confidence - result.family_wise_coverage,
        is_valid=result.family_wise_coverage >= nominal_confidence - tolerance,
    )


@dataclass
class CoverageSimulationResult:
    """Result of coverage simulation study.

    Attributes:
        n_simulations: Number of Monte Carlo simulations.
        n_observables: Number of observables.
        shots_per_sim: Shots used per simulation.
        empirical_coverage: Empirical coverage rates.
        theoretical_coverage: Expected theoretical coverage.
        coverage_se: Standard error of empirical coverage.
        ci_for_coverage: 95% CI for the coverage estimate.
    """

    n_simulations: int
    n_observables: int
    shots_per_sim: int
    empirical_coverage: float
    theoretical_coverage: float
    coverage_se: float
    ci_for_coverage: tuple[float, float]

    @property
    def is_consistent(self) -> bool:
        """Check if empirical coverage is consistent with theoretical."""
        return self.ci_for_coverage[0] <= self.theoretical_coverage <= self.ci_for_coverage[1]


def simulate_coverage(
    true_expectations: list[float],
    n_shots: int,
    n_simulations: int = 1000,
    confidence_level: float = 0.95,
    fwer_method: FWERMethod | str = FWERMethod.BONFERRONI,
    seed: int | None = None,
) -> CoverageSimulationResult:
    """Simulate coverage for Bernoulli sampling model.

    Simulates measurement outcomes assuming each observable yields
    ±1 eigenvalues with P(+1) = (1 + ⟨O⟩)/2.

    Args:
        true_expectations: True expectation values for each observable.
        n_shots: Number of shots per observable.
        n_simulations: Number of Monte Carlo simulations.
        confidence_level: Nominal confidence level.
        fwer_method: FWER control method.
        seed: Random seed for reproducibility.

    Returns:
        CoverageSimulationResult with empirical coverage analysis.
    """
    from .confidence import normal_ci
    from .fwer import compute_fwer_adjustment

    rng = np.random.default_rng(seed)
    M = len(true_expectations)

    # Get FWER adjustment
    alpha = 1 - confidence_level
    adjustment = compute_fwer_adjustment(M, alpha, fwer_method)

    family_covered_count = 0

    for _ in range(n_simulations):
        all_covered = True

        for obs_idx, true_exp in enumerate(true_expectations):
            # Simulate Bernoulli outcomes
            p_plus = (1 + true_exp) / 2
            outcomes = 2 * rng.binomial(1, p_plus, n_shots) - 1  # Map to ±1

            # Compute estimate and SE
            estimate = float(np.mean(outcomes))
            se = float(np.std(outcomes, ddof=1) / np.sqrt(n_shots))

            # Construct CI at adjusted confidence level
            ci = normal_ci(
                estimate, se, adjustment.confidence_individual[obs_idx], n_shots
            )

            if not ci.contains(true_exp):
                all_covered = False

        if all_covered:
            family_covered_count += 1

    # Compute empirical coverage and its SE
    empirical_coverage = family_covered_count / n_simulations
    coverage_se = np.sqrt(empirical_coverage * (1 - empirical_coverage) / n_simulations)

    # 95% CI for coverage
    z = 1.96
    ci_low = max(0, empirical_coverage - z * coverage_se)
    ci_high = min(1, empirical_coverage + z * coverage_se)

    return CoverageSimulationResult(
        n_simulations=n_simulations,
        n_observables=M,
        shots_per_sim=n_shots,
        empirical_coverage=empirical_coverage,
        theoretical_coverage=confidence_level,
        coverage_se=coverage_se,
        ci_for_coverage=(ci_low, ci_high),
    )


def validate_coverage(
    result: CoverageResult | CoverageSimulationResult,
    min_coverage: float | None = None,
    max_deficit: float = 0.02,
) -> tuple[bool, str]:
    """Validate coverage result against requirements.

    Args:
        result: Coverage result to validate.
        min_coverage: Minimum required coverage (default: nominal - max_deficit).
        max_deficit: Maximum allowed coverage deficit.

    Returns:
        Tuple of (is_valid, message).
    """
    if isinstance(result, CoverageResult):
        nominal = result.nominal_confidence
        actual = result.average_coverage
        deficit = result.coverage_deficit
    else:
        nominal = result.theoretical_coverage
        actual = result.empirical_coverage
        deficit = nominal - actual

    if min_coverage is None:
        min_coverage = nominal - max_deficit

    is_valid = actual >= min_coverage

    if is_valid:
        msg = f"Coverage {actual:.3f} meets requirement {min_coverage:.3f}"
    else:
        msg = f"Coverage {actual:.3f} below requirement {min_coverage:.3f} (deficit: {deficit:.3f})"

    return is_valid, msg
