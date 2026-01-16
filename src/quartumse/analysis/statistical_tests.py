"""Statistical hypothesis testing for benchmark comparisons.

Implements Benchmarking_Improvement.md enhancement:
- Bootstrap confidence intervals
- Bootstrap hypothesis tests for protocol differences
- Kolmogorov-Smirnov tests for distribution differences
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
from scipy import stats


@dataclass
class BootstrapCI:
    """Bootstrap confidence interval result.

    Attributes:
        estimate: Point estimate
        ci_low: Lower CI bound
        ci_high: Upper CI bound
        confidence: Confidence level (e.g., 0.95)
        n_bootstrap: Number of bootstrap samples
        bootstrap_std: Standard deviation of bootstrap distribution
    """
    estimate: float
    ci_low: float
    ci_high: float
    confidence: float
    n_bootstrap: int
    bootstrap_std: float

    def to_dict(self) -> dict[str, float]:
        return {
            "estimate": self.estimate,
            "ci_low": self.ci_low,
            "ci_high": self.ci_high,
            "confidence": self.confidence,
            "n_bootstrap": self.n_bootstrap,
            "bootstrap_std": self.bootstrap_std,
        }


@dataclass
class HypothesisTestResult:
    """Result of hypothesis test.

    Attributes:
        statistic: Test statistic value
        p_value: P-value (two-sided)
        effect_size: Effect size measure
        ci: Confidence interval for difference
        reject_null: Whether to reject null at alpha level
        alpha: Significance level
        test_name: Name of the test
    """
    statistic: float
    p_value: float
    effect_size: float
    ci: BootstrapCI | None
    reject_null: bool
    alpha: float
    test_name: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "statistic": self.statistic,
            "p_value": self.p_value,
            "effect_size": self.effect_size,
            "reject_null": self.reject_null,
            "alpha": self.alpha,
            "test_name": self.test_name,
            "ci": self.ci.to_dict() if self.ci else None,
        }


@dataclass
class StatisticalComparison:
    """Complete statistical comparison between protocols.

    Attributes:
        protocol_a: Protocol A identifier
        protocol_b: Protocol B identifier
        n_total: Shot budget compared
        metric: Metric compared (e.g., "mean_se")
        difference_test: Test for A - B difference
        ks_test: Kolmogorov-Smirnov distribution test
        ssf_ci: Bootstrap CI for shot-savings factor
    """
    protocol_a: str
    protocol_b: str
    n_total: int
    metric: str
    difference_test: HypothesisTestResult
    ks_test: HypothesisTestResult
    ssf_ci: BootstrapCI | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_a": self.protocol_a,
            "protocol_b": self.protocol_b,
            "n_total": self.n_total,
            "metric": self.metric,
            "difference_test": self.difference_test.to_dict(),
            "ks_test": self.ks_test.to_dict(),
            "ssf_ci": self.ssf_ci.to_dict() if self.ssf_ci else None,
        }


def bootstrap_ci(
    data: np.ndarray | list[float],
    statistic: Callable[[np.ndarray], float] = np.mean,
    confidence: float = 0.95,
    n_bootstrap: int = 10000,
    seed: int | None = 42,
) -> BootstrapCI:
    """Compute bootstrap confidence interval.

    Args:
        data: Sample data
        statistic: Function to compute statistic (default: mean)
        confidence: Confidence level
        n_bootstrap: Number of bootstrap resamples
        seed: Random seed

    Returns:
        BootstrapCI with estimate and bounds
    """
    data = np.asarray(data)
    rng = np.random.default_rng(seed)

    # Point estimate
    estimate = float(statistic(data))

    # Bootstrap resamples
    n = len(data)
    bootstrap_stats = np.zeros(n_bootstrap)

    for i in range(n_bootstrap):
        resample = rng.choice(data, size=n, replace=True)
        bootstrap_stats[i] = statistic(resample)

    # Percentile method for CI
    alpha = 1 - confidence
    ci_low = float(np.percentile(bootstrap_stats, 100 * alpha / 2))
    ci_high = float(np.percentile(bootstrap_stats, 100 * (1 - alpha / 2)))

    return BootstrapCI(
        estimate=estimate,
        ci_low=ci_low,
        ci_high=ci_high,
        confidence=confidence,
        n_bootstrap=n_bootstrap,
        bootstrap_std=float(np.std(bootstrap_stats)),
    )


def bootstrap_hypothesis_test(
    data_a: np.ndarray | list[float],
    data_b: np.ndarray | list[float],
    statistic: Callable[[np.ndarray], float] = np.mean,
    alternative: str = "two-sided",
    n_bootstrap: int = 10000,
    alpha: float = 0.05,
    seed: int | None = 42,
) -> HypothesisTestResult:
    """Bootstrap hypothesis test for difference between groups.

    Tests H0: statistic(A) = statistic(B)

    Args:
        data_a: Sample from group A
        data_b: Sample from group B
        statistic: Function to compute statistic
        alternative: "two-sided", "less", or "greater"
        n_bootstrap: Number of bootstrap resamples
        alpha: Significance level
        seed: Random seed

    Returns:
        HypothesisTestResult
    """
    data_a = np.asarray(data_a)
    data_b = np.asarray(data_b)
    rng = np.random.default_rng(seed)

    # Observed difference
    stat_a = statistic(data_a)
    stat_b = statistic(data_b)
    observed_diff = stat_a - stat_b

    # Pool data under null hypothesis
    pooled = np.concatenate([data_a, data_b])
    n_a, n_b = len(data_a), len(data_b)

    # Bootstrap under null (permutation approach)
    null_diffs = np.zeros(n_bootstrap)
    for i in range(n_bootstrap):
        permuted = rng.permutation(pooled)
        perm_a = permuted[:n_a]
        perm_b = permuted[n_a:]
        null_diffs[i] = statistic(perm_a) - statistic(perm_b)

    # P-value
    if alternative == "two-sided":
        p_value = float(np.mean(np.abs(null_diffs) >= np.abs(observed_diff)))
    elif alternative == "less":
        p_value = float(np.mean(null_diffs <= observed_diff))
    elif alternative == "greater":
        p_value = float(np.mean(null_diffs >= observed_diff))
    else:
        raise ValueError(f"Unknown alternative: {alternative}")

    # Effect size (Cohen's d approximation)
    pooled_std = np.sqrt((np.var(data_a) + np.var(data_b)) / 2)
    effect_size = observed_diff / pooled_std if pooled_std > 0 else 0.0

    # CI for difference via bootstrap
    diff_bootstrap = np.zeros(n_bootstrap)
    for i in range(n_bootstrap):
        resample_a = rng.choice(data_a, size=n_a, replace=True)
        resample_b = rng.choice(data_b, size=n_b, replace=True)
        diff_bootstrap[i] = statistic(resample_a) - statistic(resample_b)

    ci = BootstrapCI(
        estimate=float(observed_diff),
        ci_low=float(np.percentile(diff_bootstrap, 100 * alpha / 2)),
        ci_high=float(np.percentile(diff_bootstrap, 100 * (1 - alpha / 2))),
        confidence=1 - alpha,
        n_bootstrap=n_bootstrap,
        bootstrap_std=float(np.std(diff_bootstrap)),
    )

    return HypothesisTestResult(
        statistic=float(observed_diff),
        p_value=p_value,
        effect_size=float(effect_size),
        ci=ci,
        reject_null=p_value < alpha,
        alpha=alpha,
        test_name="bootstrap_permutation",
    )


def ks_test_protocols(
    se_a: np.ndarray | list[float],
    se_b: np.ndarray | list[float],
    alpha: float = 0.05,
) -> HypothesisTestResult:
    """Kolmogorov-Smirnov test for distribution difference.

    Tests whether SE distributions differ significantly.

    Args:
        se_a: SE values from protocol A
        se_b: SE values from protocol B
        alpha: Significance level

    Returns:
        HypothesisTestResult
    """
    se_a = np.asarray(se_a)
    se_b = np.asarray(se_b)

    # K-S test
    ks_stat, p_value = stats.ks_2samp(se_a, se_b)

    # Effect size: difference in means / pooled std
    pooled_std = np.sqrt((np.var(se_a) + np.var(se_b)) / 2)
    effect_size = (np.mean(se_a) - np.mean(se_b)) / pooled_std if pooled_std > 0 else 0.0

    return HypothesisTestResult(
        statistic=float(ks_stat),
        p_value=float(p_value),
        effect_size=float(effect_size),
        ci=None,
        reject_null=p_value < alpha,
        alpha=alpha,
        test_name="kolmogorov_smirnov",
    )


def bootstrap_ssf(
    se_a: np.ndarray | list[float],
    se_b: np.ndarray | list[float],
    epsilon: float,
    n_bootstrap: int = 10000,
    confidence: float = 0.95,
    seed: int | None = 42,
) -> BootstrapCI:
    """Bootstrap confidence interval for shot-savings factor.

    SSF = N*_baseline / N*_protocol (estimated from SE scaling)

    Args:
        se_a: SE values from protocol A (candidate)
        se_b: SE values from protocol B (baseline)
        epsilon: Target precision
        n_bootstrap: Number of bootstrap resamples
        confidence: Confidence level
        seed: Random seed

    Returns:
        BootstrapCI for SSF
    """
    se_a = np.asarray(se_a)
    se_b = np.asarray(se_b)
    rng = np.random.default_rng(seed)

    def estimate_ssf(se_protocol, se_baseline):
        # Estimate N* ratio from SE ratio
        # SE ∝ 1/sqrt(N) => N ∝ 1/SE^2
        # SSF = N*_baseline / N*_protocol = SE_protocol^2 / SE_baseline^2
        mean_se_p = np.mean(se_protocol)
        mean_se_b = np.mean(se_baseline)
        if mean_se_p > 0 and mean_se_b > 0:
            return (mean_se_b / mean_se_p) ** 2
        elif mean_se_p == 0 and mean_se_b > 0:
            return float('inf')  # Protocol is perfect, infinite savings
        return float('nan')  # Can't compute

    # Point estimate
    ssf_point = estimate_ssf(se_a, se_b)

    # Bootstrap
    n_a, n_b = len(se_a), len(se_b)
    bootstrap_ssf_values = np.zeros(n_bootstrap)

    for i in range(n_bootstrap):
        resample_a = rng.choice(se_a, size=n_a, replace=True)
        resample_b = rng.choice(se_b, size=n_b, replace=True)
        bootstrap_ssf_values[i] = estimate_ssf(resample_a, resample_b)

    # Filter out infinities for percentile calculation
    valid = np.isfinite(bootstrap_ssf_values)
    if np.sum(valid) < n_bootstrap * 0.1:
        # Too many infinities
        return BootstrapCI(
            estimate=float(ssf_point),
            ci_low=float('nan'),
            ci_high=float('nan'),
            confidence=confidence,
            n_bootstrap=n_bootstrap,
            bootstrap_std=float('nan'),
        )

    valid_ssf = bootstrap_ssf_values[valid]
    alpha = 1 - confidence

    return BootstrapCI(
        estimate=float(ssf_point),
        ci_low=float(np.percentile(valid_ssf, 100 * alpha / 2)),
        ci_high=float(np.percentile(valid_ssf, 100 * (1 - alpha / 2))),
        confidence=confidence,
        n_bootstrap=n_bootstrap,
        bootstrap_std=float(np.std(valid_ssf)),
    )


def compare_protocols_statistically(
    results_a: list,  # LongFormRow
    results_b: list,  # LongFormRow
    n_total: int,
    epsilon: float = 0.01,
    alpha: float = 0.05,
    n_bootstrap: int = 10000,
    seed: int = 42,
) -> StatisticalComparison:
    """Complete statistical comparison between two protocols.

    Args:
        results_a: Long-form results from protocol A
        results_b: Long-form results from protocol B
        n_total: Shot budget to compare at
        epsilon: Target precision for SSF
        alpha: Significance level
        n_bootstrap: Number of bootstrap samples
        seed: Random seed

    Returns:
        StatisticalComparison with all tests
    """
    # Filter to specific N
    se_a = np.array([r.se for r in results_a if r.N_total == n_total])
    se_b = np.array([r.se for r in results_b if r.N_total == n_total])

    protocol_a = results_a[0].protocol_id if results_a else "unknown"
    protocol_b = results_b[0].protocol_id if results_b else "unknown"

    # Bootstrap test for mean SE difference
    diff_test = bootstrap_hypothesis_test(
        se_a, se_b,
        statistic=np.mean,
        n_bootstrap=n_bootstrap,
        alpha=alpha,
        seed=seed,
    )

    # K-S test for distribution difference
    ks_result = ks_test_protocols(se_a, se_b, alpha=alpha)

    # Bootstrap SSF
    ssf_ci = bootstrap_ssf(se_a, se_b, epsilon, n_bootstrap, 1 - alpha, seed)

    return StatisticalComparison(
        protocol_a=protocol_a,
        protocol_b=protocol_b,
        n_total=n_total,
        metric="mean_se",
        difference_test=diff_test,
        ks_test=ks_result,
        ssf_ci=ssf_ci,
    )
