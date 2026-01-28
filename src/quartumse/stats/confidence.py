"""Confidence interval construction (Measurements Bible §6.1, §6.2).

This module provides utilities for constructing confidence intervals
for expectation value estimates with proper clamping and CI methodology.

CI Methods Implemented:
- Normal (Wald): Based on CLT approximation
- Bootstrap percentile: Empirical resampling
- Bootstrap BCa: Bias-corrected accelerated bootstrap

Clamping (§6.2):
All CIs are clamped to [-1, 1] (physical bounds for expectation values).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

import numpy as np
from numpy.typing import NDArray


class CIMethodType(str, Enum):
    """Confidence interval construction method."""

    NORMAL = "normal"  # Normal/Wald interval
    BOOTSTRAP_PERCENTILE = "bootstrap_percentile"
    BOOTSTRAP_BCA = "bootstrap_bca"  # Bias-corrected accelerated


@dataclass
class ConfidenceInterval:
    """A confidence interval result.

    Attributes:
        estimate: Point estimate.
        se: Standard error.
        ci_low_raw: Lower bound before clamping.
        ci_high_raw: Upper bound before clamping.
        ci_low: Lower bound after clamping to [-1, 1].
        ci_high: Upper bound after clamping to [-1, 1].
        confidence_level: Confidence level (e.g., 0.95).
        method: CI construction method used.
        n_samples: Number of samples used.
    """

    estimate: float
    se: float
    ci_low_raw: float
    ci_high_raw: float
    ci_low: float
    ci_high: float
    confidence_level: float
    method: CIMethodType
    n_samples: int

    @property
    def width(self) -> float:
        """Width of the (clamped) confidence interval."""
        return self.ci_high - self.ci_low

    @property
    def width_raw(self) -> float:
        """Width of the raw (unclamped) confidence interval."""
        return self.ci_high_raw - self.ci_low_raw

    def contains(self, value: float) -> bool:
        """Check if value is within the clamped CI."""
        return self.ci_low <= value <= self.ci_high


def clamp_to_physical_bounds(
    value: float,
    lower: float = -1.0,
    upper: float = 1.0,
) -> float:
    """Clamp value to physical bounds for expectation values.

    Args:
        value: Value to clamp.
        lower: Lower bound (default -1).
        upper: Upper bound (default 1).

    Returns:
        Clamped value.
    """
    return max(lower, min(upper, value))


def normal_ci(
    estimate: float,
    se: float,
    confidence_level: float = 0.95,
    n_samples: int = 0,
) -> ConfidenceInterval:
    """Construct normal (Wald) confidence interval.

    CI = estimate ± z_{α/2} * SE

    where z_{α/2} is the (1 - α/2) quantile of the standard normal.

    Args:
        estimate: Point estimate.
        se: Standard error.
        confidence_level: Confidence level (default 0.95).
        n_samples: Number of samples (for metadata).

    Returns:
        ConfidenceInterval with normal CI.
    """
    from scipy import stats

    alpha = 1 - confidence_level
    z = stats.norm.ppf(1 - alpha / 2)

    ci_low_raw = estimate - z * se
    ci_high_raw = estimate + z * se

    return ConfidenceInterval(
        estimate=estimate,
        se=se,
        ci_low_raw=ci_low_raw,
        ci_high_raw=ci_high_raw,
        ci_low=clamp_to_physical_bounds(ci_low_raw),
        ci_high=clamp_to_physical_bounds(ci_high_raw),
        confidence_level=confidence_level,
        method=CIMethodType.NORMAL,
        n_samples=n_samples,
    )


def bootstrap_percentile_ci(
    data: NDArray[np.floating],
    statistic: Callable[[NDArray], float] | None = None,
    confidence_level: float = 0.95,
    n_bootstrap: int = 1000,
    seed: int | None = None,
) -> ConfidenceInterval:
    """Construct bootstrap percentile confidence interval.

    Resamples data with replacement and computes CI from the
    empirical distribution of the statistic.

    Args:
        data: Array of observations.
        statistic: Function to compute statistic (default: mean).
        confidence_level: Confidence level (default 0.95).
        n_bootstrap: Number of bootstrap samples.
        seed: Random seed for reproducibility.

    Returns:
        ConfidenceInterval with bootstrap percentile CI.
    """
    if statistic is None:
        statistic = np.mean

    rng = np.random.default_rng(seed)
    n = len(data)

    # Generate bootstrap samples
    bootstrap_stats = []
    for _ in range(n_bootstrap):
        resample = rng.choice(data, size=n, replace=True)
        bootstrap_stats.append(statistic(resample))

    bootstrap_stats = np.array(bootstrap_stats)

    # Compute percentile CI
    alpha = 1 - confidence_level
    ci_low_raw = float(np.percentile(bootstrap_stats, 100 * alpha / 2))
    ci_high_raw = float(np.percentile(bootstrap_stats, 100 * (1 - alpha / 2)))

    # Point estimate and SE
    estimate = float(statistic(data))
    se = float(np.std(bootstrap_stats))

    return ConfidenceInterval(
        estimate=estimate,
        se=se,
        ci_low_raw=ci_low_raw,
        ci_high_raw=ci_high_raw,
        ci_low=clamp_to_physical_bounds(ci_low_raw),
        ci_high=clamp_to_physical_bounds(ci_high_raw),
        confidence_level=confidence_level,
        method=CIMethodType.BOOTSTRAP_PERCENTILE,
        n_samples=n,
    )


def bootstrap_bca_ci(
    data: NDArray[np.floating],
    statistic: Callable[[NDArray], float] | None = None,
    confidence_level: float = 0.95,
    n_bootstrap: int = 1000,
    seed: int | None = None,
) -> ConfidenceInterval:
    """Construct bias-corrected accelerated (BCa) bootstrap CI.

    BCa corrects for bias and skewness in the bootstrap distribution.
    More accurate than percentile bootstrap for small samples.

    Args:
        data: Array of observations.
        statistic: Function to compute statistic (default: mean).
        confidence_level: Confidence level (default 0.95).
        n_bootstrap: Number of bootstrap samples.
        seed: Random seed for reproducibility.

    Returns:
        ConfidenceInterval with BCa bootstrap CI.
    """
    from scipy import stats

    if statistic is None:
        statistic = np.mean

    rng = np.random.default_rng(seed)
    n = len(data)
    original_stat = float(statistic(data))

    # Generate bootstrap samples
    bootstrap_stats = []
    for _ in range(n_bootstrap):
        resample = rng.choice(data, size=n, replace=True)
        bootstrap_stats.append(statistic(resample))

    bootstrap_stats = np.array(bootstrap_stats)

    # Bias correction factor
    z0 = stats.norm.ppf(np.mean(bootstrap_stats < original_stat))
    if np.isinf(z0):
        z0 = 0.0

    # Acceleration factor (jackknife estimate)
    jackknife_stats = []
    for i in range(n):
        jackknife_sample = np.delete(data, i)
        jackknife_stats.append(statistic(jackknife_sample))

    jackknife_stats = np.array(jackknife_stats)
    jackknife_mean = np.mean(jackknife_stats)

    # Acceleration
    num = np.sum((jackknife_mean - jackknife_stats) ** 3)
    denom = 6 * (np.sum((jackknife_mean - jackknife_stats) ** 2) ** 1.5)

    if denom == 0:
        a = 0.0
    else:
        a = num / denom

    # Adjusted percentiles
    alpha = 1 - confidence_level
    z_alpha = stats.norm.ppf(alpha / 2)
    z_1_alpha = stats.norm.ppf(1 - alpha / 2)

    # BCa adjustment
    def bca_percentile(z: float) -> float:
        return stats.norm.cdf(z0 + (z0 + z) / (1 - a * (z0 + z)))

    alpha_low = bca_percentile(z_alpha)
    alpha_high = bca_percentile(z_1_alpha)

    # Handle edge cases
    alpha_low = max(0.001, min(0.499, alpha_low))
    alpha_high = max(0.501, min(0.999, alpha_high))

    ci_low_raw = float(np.percentile(bootstrap_stats, 100 * alpha_low))
    ci_high_raw = float(np.percentile(bootstrap_stats, 100 * alpha_high))

    se = float(np.std(bootstrap_stats))

    return ConfidenceInterval(
        estimate=original_stat,
        se=se,
        ci_low_raw=ci_low_raw,
        ci_high_raw=ci_high_raw,
        ci_low=clamp_to_physical_bounds(ci_low_raw),
        ci_high=clamp_to_physical_bounds(ci_high_raw),
        confidence_level=confidence_level,
        method=CIMethodType.BOOTSTRAP_BCA,
        n_samples=n,
    )


def construct_ci(
    data: NDArray[np.floating] | None = None,
    estimate: float | None = None,
    se: float | None = None,
    method: CIMethodType | str = CIMethodType.NORMAL,
    confidence_level: float = 0.95,
    n_bootstrap: int = 1000,
    seed: int | None = None,
) -> ConfidenceInterval:
    """Construct confidence interval using specified method.

    For NORMAL method, provide estimate and se.
    For BOOTSTRAP methods, provide data array.

    Args:
        data: Array of observations (for bootstrap methods).
        estimate: Point estimate (for normal method).
        se: Standard error (for normal method).
        method: CI construction method.
        confidence_level: Confidence level (default 0.95).
        n_bootstrap: Number of bootstrap samples.
        seed: Random seed for reproducibility.

    Returns:
        ConfidenceInterval result.

    Raises:
        ValueError: If required parameters are missing.
    """
    if isinstance(method, str):
        method = CIMethodType(method)

    if method == CIMethodType.NORMAL:
        if estimate is None or se is None:
            raise ValueError("Normal CI requires estimate and se")
        n_samples = len(data) if data is not None else 0
        return normal_ci(estimate, se, confidence_level, n_samples)

    elif method == CIMethodType.BOOTSTRAP_PERCENTILE:
        if data is None:
            raise ValueError("Bootstrap CI requires data array")
        return bootstrap_percentile_ci(data, None, confidence_level, n_bootstrap, seed)

    elif method == CIMethodType.BOOTSTRAP_BCA:
        if data is None:
            raise ValueError("Bootstrap CI requires data array")
        return bootstrap_bca_ci(data, None, confidence_level, n_bootstrap, seed)

    else:
        raise ValueError(f"Unknown CI method: {method}")


def ci_from_eigenvalues(
    eigenvalues: NDArray[np.floating],
    coefficient: float = 1.0,
    method: CIMethodType | str = CIMethodType.NORMAL,
    confidence_level: float = 0.95,
    n_bootstrap: int = 1000,
    seed: int | None = None,
) -> ConfidenceInterval:
    """Construct CI from measurement eigenvalues.

    This is the primary entry point for constructing CIs from raw
    measurement outcomes for Pauli observables.

    Args:
        eigenvalues: Array of +1/-1 eigenvalues.
        coefficient: Observable coefficient.
        method: CI construction method.
        confidence_level: Confidence level.
        n_bootstrap: Bootstrap samples (if applicable).
        seed: Random seed.

    Returns:
        ConfidenceInterval for the expectation value.
    """
    # Scale eigenvalues by coefficient
    scaled_data = eigenvalues * coefficient

    if method == CIMethodType.NORMAL or isinstance(method, str) and method == "normal":
        estimate = float(np.mean(scaled_data))
        se = float(np.std(scaled_data, ddof=1) / np.sqrt(len(scaled_data)))
        return normal_ci(estimate, se, confidence_level, len(eigenvalues))
    else:
        return construct_ci(
            data=scaled_data,
            method=method,
            confidence_level=confidence_level,
            n_bootstrap=n_bootstrap,
            seed=seed,
        )
