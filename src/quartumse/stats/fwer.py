"""Family-Wise Error Rate (FWER) control (Measurements Bible §6.3).

This module provides utilities for controlling the family-wise error rate
when estimating multiple observables simultaneously.

FWER Control Methods:
- Bonferroni: Conservative, α/M per comparison
- Šidák: Slightly less conservative, 1 - (1-α)^(1/M)
- Holm-Bonferroni: Step-down procedure, more powerful

Key concepts:
- α: Global significance level (e.g., 0.05)
- M: Number of observables (family size)
- δ: Global failure probability (1 - confidence_level)
- Individual CI confidence: 1 - α_adj (adjusted significance level)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from .confidence import CIMethodType, ConfidenceInterval, construct_ci


class FWERMethod(str, Enum):
    """Method for controlling family-wise error rate."""

    BONFERRONI = "bonferroni"
    SIDAK = "sidak"
    HOLM = "holm"
    NONE = "none"  # No adjustment


@dataclass
class FWERAdjustment:
    """Result of FWER adjustment computation.

    Attributes:
        method: FWER method used.
        M: Number of comparisons (family size).
        alpha_global: Global significance level.
        alpha_individual: Adjusted individual significance levels.
        confidence_individual: Individual confidence levels.
        effective_confidence: Effective family-wise confidence level.
    """

    method: FWERMethod
    M: int
    alpha_global: float
    alpha_individual: list[float]
    confidence_individual: list[float]
    effective_confidence: float

    @property
    def delta_global(self) -> float:
        """Global failure probability."""
        return self.alpha_global

    @property
    def confidence_global(self) -> float:
        """Global (family-wise) confidence level."""
        return 1 - self.alpha_global


def bonferroni_adjustment(
    M: int,
    alpha: float = 0.05,
) -> FWERAdjustment:
    """Compute Bonferroni adjustment for M comparisons.

    Bonferroni: α_i = α/M for all i.

    This is conservative but simple and widely applicable.

    Args:
        M: Number of comparisons.
        alpha: Global significance level.

    Returns:
        FWERAdjustment with Bonferroni-adjusted levels.
    """
    alpha_individual = [alpha / M] * M
    confidence_individual = [1 - alpha / M] * M

    return FWERAdjustment(
        method=FWERMethod.BONFERRONI,
        M=M,
        alpha_global=alpha,
        alpha_individual=alpha_individual,
        confidence_individual=confidence_individual,
        effective_confidence=1 - alpha,
    )


def sidak_adjustment(
    M: int,
    alpha: float = 0.05,
) -> FWERAdjustment:
    """Compute Šidák adjustment for M comparisons.

    Šidák: α_i = 1 - (1 - α)^(1/M) for all i.

    Slightly less conservative than Bonferroni, exact for independent tests.

    Args:
        M: Number of comparisons.
        alpha: Global significance level.

    Returns:
        FWERAdjustment with Šidák-adjusted levels.
    """
    alpha_adj = 1 - (1 - alpha) ** (1 / M)
    alpha_individual = [alpha_adj] * M
    confidence_individual = [1 - alpha_adj] * M

    return FWERAdjustment(
        method=FWERMethod.SIDAK,
        M=M,
        alpha_global=alpha,
        alpha_individual=alpha_individual,
        confidence_individual=confidence_individual,
        effective_confidence=1 - alpha,
    )


def holm_adjustment(
    M: int,
    alpha: float = 0.05,
    p_values: list[float] | None = None,
) -> FWERAdjustment:
    """Compute Holm-Bonferroni step-down adjustment.

    Holm procedure: Sort p-values, reject H_i if p_(i) ≤ α/(M-i+1).

    More powerful than Bonferroni while still controlling FWER.

    For CI construction (without p-values), uses the most conservative
    adjustment α/M for all CIs to maintain family-wise coverage.

    Args:
        M: Number of comparisons.
        alpha: Global significance level.
        p_values: Optional sorted p-values (for hypothesis testing).

    Returns:
        FWERAdjustment with Holm-adjusted levels.
    """
    # For CI construction, we use α/M for all to ensure coverage
    # The step-down is only applicable when we have p-values
    if p_values is None:
        # Conservative: use Bonferroni for CIs
        alpha_individual = [alpha / M] * M
        confidence_individual = [1 - alpha / M] * M
    else:
        # Step-down adjustment
        sorted_indices = np.argsort(p_values)
        alpha_individual = [0.0] * M
        for rank, idx in enumerate(sorted_indices):
            alpha_individual[idx] = alpha / (M - rank)
        confidence_individual = [1 - a for a in alpha_individual]

    return FWERAdjustment(
        method=FWERMethod.HOLM,
        M=M,
        alpha_global=alpha,
        alpha_individual=alpha_individual,
        confidence_individual=confidence_individual,
        effective_confidence=1 - alpha,
    )


def compute_fwer_adjustment(
    M: int,
    alpha: float = 0.05,
    method: FWERMethod | str = FWERMethod.BONFERRONI,
    p_values: list[float] | None = None,
) -> FWERAdjustment:
    """Compute FWER adjustment using specified method.

    Args:
        M: Number of comparisons.
        alpha: Global significance level.
        method: FWER control method.
        p_values: Optional p-values (for Holm procedure).

    Returns:
        FWERAdjustment with adjusted significance levels.
    """
    if isinstance(method, str):
        method = FWERMethod(method)

    if method == FWERMethod.NONE:
        return FWERAdjustment(
            method=FWERMethod.NONE,
            M=M,
            alpha_global=alpha,
            alpha_individual=[alpha] * M,
            confidence_individual=[1 - alpha] * M,
            effective_confidence=1 - alpha,
        )
    elif method == FWERMethod.BONFERRONI:
        return bonferroni_adjustment(M, alpha)
    elif method == FWERMethod.SIDAK:
        return sidak_adjustment(M, alpha)
    elif method == FWERMethod.HOLM:
        return holm_adjustment(M, alpha, p_values)
    else:
        raise ValueError(f"Unknown FWER method: {method}")


@dataclass
class SimultaneousCIs:
    """Collection of simultaneous confidence intervals with FWER control.

    Attributes:
        intervals: List of individual CIs.
        fwer_adjustment: FWER adjustment used.
        coverage_guarantee: Family-wise coverage probability.
    """

    intervals: list[ConfidenceInterval]
    fwer_adjustment: FWERAdjustment
    coverage_guarantee: float

    @property
    def M(self) -> int:
        """Number of intervals."""
        return len(self.intervals)

    def all_contain(self, values: list[float]) -> bool:
        """Check if all CIs contain their respective truth values."""
        if len(values) != len(self.intervals):
            raise ValueError("Number of values must match number of intervals")
        return all(ci.contains(v) for ci, v in zip(self.intervals, values, strict=False))

    def coverage_count(self, values: list[float]) -> int:
        """Count how many CIs contain their truth values."""
        if len(values) != len(self.intervals):
            raise ValueError("Number of values must match number of intervals")
        return sum(ci.contains(v) for ci, v in zip(self.intervals, values, strict=False))

    def coverage_fraction(self, values: list[float]) -> float:
        """Fraction of CIs containing their truth values."""
        return self.coverage_count(values) / self.M


def construct_simultaneous_cis(
    estimates: list[float],
    standard_errors: list[float],
    alpha: float = 0.05,
    fwer_method: FWERMethod | str = FWERMethod.BONFERRONI,
    ci_method: CIMethodType | str = CIMethodType.NORMAL,
) -> SimultaneousCIs:
    """Construct simultaneous CIs with FWER control.

    Each CI is constructed at the FWER-adjusted confidence level
    to ensure family-wise coverage.

    Args:
        estimates: List of point estimates.
        standard_errors: List of standard errors.
        alpha: Global significance level.
        fwer_method: Method for FWER control.
        ci_method: Method for individual CI construction.

    Returns:
        SimultaneousCIs with family-wise coverage guarantee.
    """
    M = len(estimates)
    if len(standard_errors) != M:
        raise ValueError("Must have same number of estimates and SEs")

    # Get FWER adjustment
    adjustment = compute_fwer_adjustment(M, alpha, fwer_method)

    # Construct individual CIs at adjusted confidence level
    intervals = []
    for i, (est, se) in enumerate(zip(estimates, standard_errors, strict=False)):
        ci = construct_ci(
            estimate=est,
            se=se,
            method=ci_method,
            confidence_level=adjustment.confidence_individual[i],
        )
        intervals.append(ci)

    return SimultaneousCIs(
        intervals=intervals,
        fwer_adjustment=adjustment,
        coverage_guarantee=adjustment.effective_confidence,
    )


def compute_required_confidence_for_fwer(
    M: int,
    delta: float = 0.05,
    method: FWERMethod | str = FWERMethod.BONFERRONI,
) -> float:
    """Compute required per-comparison confidence level for FWER control.

    Given a global failure probability δ and M comparisons, compute
    the required individual confidence level for each CI.

    Args:
        M: Number of comparisons.
        delta: Global failure probability (1 - family-wise confidence).
        method: FWER control method.

    Returns:
        Required individual confidence level.
    """
    if isinstance(method, str):
        method = FWERMethod(method)

    if method == FWERMethod.NONE:
        return 1 - delta
    elif method == FWERMethod.BONFERRONI:
        return 1 - delta / M
    elif method == FWERMethod.SIDAK:
        return (1 - delta) ** (1 / M)
    elif method == FWERMethod.HOLM:
        # For CIs, use Bonferroni (most conservative for Holm)
        return 1 - delta / M
    else:
        raise ValueError(f"Unknown FWER method: {method}")
