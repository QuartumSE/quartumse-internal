"""Common utilities for analysing QuartumSE metrics.

The utilities defined here standardise how QuartumSE computes, aggregates and
reports classical shadow metrics such as the shot-savings ratio (SSR),
confidence-interval coverage and variance reductions.  They are shared between
CLI tooling, experiment notebooks and the provenance report pipeline so that a
single schema is preserved from raw experiment data all the way through to
Phase 1 validation artefacts.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from statistics import NormalDist
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Union

import numpy as np


Number = Union[int, float, np.ndarray]


@dataclass(frozen=True)
class ConfidenceInterval:
    """Container for confidence intervals with helper utilities."""

    lower: float
    upper: float
    level: float = 0.95

    def contains(self, value: float) -> bool:
        """Return ``True`` when ``value`` lies inside the interval."""

        return self.lower <= value <= self.upper

    @property
    def width(self) -> float:
        return float(self.upper - self.lower)

    @property
    def half_width(self) -> float:
        return self.width / 2.0

    def z_value(self) -> float:
        """Return the Gaussian z-score for the configured confidence level."""

        return NormalDist().inv_cdf(0.5 + self.level / 2.0)

    def standard_error(self) -> Optional[float]:
        """Infer the standard error represented by the interval."""

        if self.half_width == 0:
            return 0.0
        z = self.z_value()
        if z == 0:
            return None
        return self.half_width / z

    def to_dict(self) -> Dict[str, float]:
        return {"lower": float(self.lower), "upper": float(self.upper), "level": float(self.level)}


@dataclass(frozen=True)
class MetricEstimate:
    """Describes an estimator for an observable or aggregate quantity."""

    expectation: Optional[float] = None
    variance: Optional[float] = None
    std_error: Optional[float] = None
    ci: Optional[ConfidenceInterval] = None
    shots: Optional[int] = None
    weight: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def effective_variance(self) -> Optional[float]:
        """Return a best-effort variance estimate for downstream comparisons."""

        if self.variance is not None:
            return float(self.variance)
        if self.std_error is not None:
            return float(self.std_error) ** 2
        if self.ci is not None:
            se = self.ci.standard_error()
            return None if se is None else se**2
        return None

    def standard_error(self) -> Optional[float]:
        if self.std_error is not None:
            return float(self.std_error)
        variance = self.effective_variance()
        if variance is not None:
            return float(np.sqrt(variance))
        return None

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "expectation": self.expectation,
            "variance": self.variance,
            "std_error": self.std_error,
            "shots": self.shots,
            "weight": self.weight,
            "metadata": dict(self.metadata),
        }
        if self.ci is not None:
            out["confidence_interval"] = self.ci.to_dict()
        else:
            out["confidence_interval"] = None
        return out


@dataclass(frozen=True)
class ObservableComparison:
    """Pair-wise comparison between a baseline observable and a QuartumSE run."""

    name: str
    baseline: MetricEstimate
    approach: MetricEstimate
    expected_value: Optional[float] = None
    ssr: Optional[float] = None
    variance_ratio: Optional[float] = None
    in_ci: Optional[bool] = None
    weight: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Replace nested dataclasses with explicit dictionaries for manifest/report usage
        data["baseline"] = self.baseline.to_dict()
        data["approach"] = self.approach.to_dict()
        if isinstance(self.baseline.ci, ConfidenceInterval):
            data["baseline"]["confidence_interval"] = self.baseline.ci.to_dict()
        if isinstance(self.approach.ci, ConfidenceInterval):
            data["approach"]["confidence_interval"] = self.approach.ci.to_dict()
        return data


@dataclass(frozen=True)
class MetricsSummary:
    """Aggregate metrics across all observables for a single experiment."""

    comparisons: Dict[str, ObservableComparison]
    ssr_average: Optional[float]
    ci_coverage: Optional[float]
    variance_ratio_average: Optional[float]
    total_observables: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ssr_average": self.ssr_average,
            "ci_coverage": self.ci_coverage,
            "variance_ratio_average": self.variance_ratio_average,
            "total_observables": self.total_observables,
            "observables": {name: comparison.to_dict() for name, comparison in self.comparisons.items()},
        }


def _normalise_precision_to_variance(
    value: float,
    *,
    mode: Optional[str],
    ci_level: float = 0.95,
) -> Optional[float]:
    """Convert any supported precision descriptor to a variance value."""

    if value is None:
        return None
    if mode is None:
        mode = "stderr"
    mode = mode.lower()
    if mode in {"variance", "var"}:
        return float(value)
    if mode in {"std", "stdev", "stddev", "stderr", "std_error", "standard_error"}:
        return float(value) ** 2
    if mode in {"ci", "ci_half_width", "half_width"}:
        if value == 0:
            return 0.0
        z = NormalDist().inv_cdf(0.5 + ci_level / 2.0)
        if z == 0:
            return None
        return (float(value) / z) ** 2
    raise ValueError(f"Unsupported precision mode '{mode}'")


def compute_ssr(
    baseline_shots: int,
    quartumse_shots: int,
    baseline_precision: Optional[float] = None,
    quartumse_precision: Optional[float] = None,
    *,
    baseline_precision_mode: Optional[str] = None,
    quartumse_precision_mode: Optional[str] = None,
    baseline_ci_level: float = 0.95,
    quartumse_ci_level: float = 0.95,
) -> float:
    """Compute Shot-Savings Ratio (SSR).

    SSR compares the number of shots required by a baseline approach against the
    QuartumSE strategy.  When precision measurements (variance, standard error
    or CI widths) are provided the SSR is normalised such that unequal
    precisions are compared fairly by scaling with the variance ratio.
    """

    if quartumse_shots <= 0:
        return float("inf")

    base_ratio = baseline_shots / quartumse_shots
    if baseline_precision is None or quartumse_precision is None:
        return base_ratio

    baseline_variance = _normalise_precision_to_variance(
        baseline_precision,
        mode=baseline_precision_mode,
        ci_level=baseline_ci_level,
    )
    quartumse_variance = _normalise_precision_to_variance(
        quartumse_precision,
        mode=quartumse_precision_mode,
        ci_level=quartumse_ci_level,
    )

    if (
        baseline_variance is None
        or quartumse_variance is None
        or quartumse_variance == 0
    ):
        return base_ratio

    return base_ratio * (baseline_variance / quartumse_variance)


def compute_rmse_at_cost(
    rmse: float,
    cost_usd: float,
) -> float:
    """Compute the RMSE@$ metric (dollars spent per unit RMSE)."""

    return cost_usd / rmse if rmse > 0 else float("inf")


def estimate_gate_error_rate(backend_properties: dict) -> dict:
    """Extract gate error rates from backend properties (placeholder)."""

    # TODO: Parse backend properties properly once the IBMQ API stabilises
    return {}


def weighted_mean(values: Sequence[Number], weights: Optional[Sequence[Number]] = None) -> Optional[float]:
    """Compute a weighted mean, guarding against empty inputs."""

    if not values:
        return None
    arr = np.asarray(values, dtype=float)
    if weights is None:
        return float(np.mean(arr))
    w = np.asarray(weights, dtype=float)
    if arr.shape != w.shape:
        raise ValueError("Values and weights must be the same length")
    weight_sum = np.sum(w)
    if weight_sum == 0:
        return None
    return float(np.average(arr, weights=w))


def weighted_variance(values: Sequence[Number], weights: Optional[Sequence[Number]] = None) -> Optional[float]:
    """Compute the weighted variance of a sequence."""

    if not values:
        return None
    arr = np.asarray(values, dtype=float)
    if weights is None:
        return float(np.var(arr))
    w = np.asarray(weights, dtype=float)
    if arr.shape != w.shape:
        raise ValueError("Values and weights must be the same length")
    total_weight = np.sum(w)
    if total_weight == 0:
        return None
    mean = np.average(arr, weights=w)
    variance = np.average((arr - mean) ** 2, weights=w)
    return float(variance)


def compute_ci_coverage(
    intervals: Sequence[ConfidenceInterval],
    truths: Sequence[float],
    weights: Optional[Sequence[Number]] = None,
) -> Optional[float]:
    """Compute CI coverage given intervals and the ground-truth values."""

    if not intervals:
        return None
    if len(intervals) != len(truths):
        raise ValueError("Intervals and truths must have the same length")

    flags = [1.0 if interval.contains(truth) else 0.0 for interval, truth in zip(intervals, truths)]
    return weighted_mean(flags, weights)


@dataclass(frozen=True)
class BootstrapSummary:
    """Summaries produced by :func:`bootstrap_summary`."""

    estimate: float
    variance: float
    confidence_interval: ConfidenceInterval
    samples: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "estimate": float(self.estimate),
            "variance": float(self.variance),
            "confidence_interval": self.confidence_interval.to_dict(),
            "samples": int(self.samples),
        }


def bootstrap_summary(
    values: Sequence[Number],
    *,
    weights: Optional[Sequence[Number]] = None,
    statistic: Optional[Callable[[np.ndarray], np.ndarray]] = None,
    n_resamples: int = 1000,
    ci_level: float = 0.95,
    random_state: Optional[np.random.Generator] = None,
) -> BootstrapSummary:
    """Bootstrap an arbitrary statistic over ``values``.

    Args:
        values: Iterable of sample values.
        weights: Optional sampling weights (must sum to a positive number).
        statistic: Callable computing the statistic over a 2-D array where the
            last axis indexes samples.  When omitted the mean is used.
        n_resamples: Number of bootstrap resamples.
        ci_level: Desired confidence interval level.
        random_state: Optional numpy random generator.
    """

    if not values:
        raise ValueError("At least one value is required for bootstrapping")

    samples = np.asarray(values, dtype=float)
    if samples.ndim != 1:
        raise ValueError("Bootstrap currently expects a 1D array of values")

    generator = random_state or np.random.default_rng()

    if weights is None:
        probs = None
    else:
        probs = np.asarray(weights, dtype=float)
        if probs.shape != samples.shape:
            raise ValueError("Values and weights must be the same length")
        total = probs.sum()
        if total <= 0:
            raise ValueError("Weights must sum to a positive value")
        probs = probs / total

    if statistic is None:

        def statistic(resampled: np.ndarray) -> np.ndarray:
            return np.asarray(np.mean(resampled, axis=-1))

    resampled = generator.choice(samples, size=(n_resamples, samples.size), replace=True, p=probs)
    stat_values = statistic(resampled)
    if stat_values.ndim != 1:
        raise ValueError("Statistic function must return a 1D array of length n_resamples")

    estimate = float(np.mean(stat_values))
    variance = float(np.var(stat_values, ddof=1))
    alpha = (1.0 - ci_level) / 2.0
    lower = float(np.quantile(stat_values, alpha))
    upper = float(np.quantile(stat_values, 1.0 - alpha))
    interval = ConfidenceInterval(lower=lower, upper=upper, level=ci_level)
    return BootstrapSummary(estimate=estimate, variance=variance, confidence_interval=interval, samples=n_resamples)


def _parse_confidence_interval(
    payload: Mapping[str, Any],
    *,
    default_level: float = 0.95,
) -> Optional[ConfidenceInterval]:
    ci = payload.get("confidence_interval") or payload.get("ci")
    if ci is None:
        return None

    level = float(payload.get("ci_level") or payload.get("confidence_level") or getattr(ci, "get", lambda *_: None)("level") or default_level)
    lower: Optional[float] = None
    upper: Optional[float] = None

    if isinstance(ci, Mapping):
        lower = ci.get("lower")
        upper = ci.get("upper")
    elif isinstance(ci, (list, tuple)) and len(ci) == 2:
        lower, upper = ci
    else:
        raise ValueError("Confidence interval must be a mapping or a 2-tuple/list")

    if lower is None or upper is None:
        raise ValueError("Confidence interval requires both lower and upper bounds")

    return ConfidenceInterval(lower=float(lower), upper=float(upper), level=level)


def build_metric_estimate(payload: Mapping[str, Any], *, default_ci_level: float = 0.95) -> MetricEstimate:
    """Create a :class:`MetricEstimate` from an experiment payload mapping."""

    expectation = payload.get("expectation")
    variance = payload.get("variance") or payload.get("var")
    std_error = payload.get("std_error") or payload.get("stderr") or payload.get("standard_error")
    ci = _parse_confidence_interval(payload, default_level=default_ci_level)
    shots = payload.get("shots")
    weight = payload.get("weight") or shots

    metadata: Dict[str, Any] = {}
    for key in ("expected", "error", "in_ci"):
        if key in payload:
            metadata[key] = payload[key]

    return MetricEstimate(
        expectation=None if expectation is None else float(expectation),
        variance=None if variance is None else float(variance),
        std_error=None if std_error is None else float(std_error),
        ci=ci,
        shots=None if shots is None else int(shots),
        weight=None if weight is None else float(weight),
        metadata=metadata,
    )


def build_observable_comparison(
    name: str,
    baseline_payload: Mapping[str, Any],
    approach_payload: Mapping[str, Any],
    *,
    baseline_total_shots: int,
    approach_total_shots: int,
    default_expected: float = 0.0,
    default_ci_level: float = 0.95,
) -> ObservableComparison:
    """Create an :class:`ObservableComparison` using the raw observable payloads."""

    baseline_estimate = build_metric_estimate(baseline_payload, default_ci_level=default_ci_level)
    approach_estimate = build_metric_estimate(approach_payload, default_ci_level=default_ci_level)

    expected_value = approach_payload.get("expected")
    if expected_value is None:
        expected_value = baseline_payload.get("expected", default_expected)
    if expected_value is not None:
        expected_value = float(expected_value)

    approach_ci = approach_estimate.ci
    in_ci: Optional[bool] = None
    if approach_ci is not None and expected_value is not None:
        in_ci = approach_ci.contains(expected_value)

    baseline_variance = baseline_estimate.effective_variance()
    approach_variance = approach_estimate.effective_variance()
    variance_ratio = None
    if (
        baseline_variance is not None
        and approach_variance is not None
        and approach_variance != 0
    ):
        variance_ratio = float(baseline_variance / approach_variance)

    baseline_precision = baseline_estimate.standard_error()
    approach_precision = approach_estimate.standard_error()
    ssr = None
    if baseline_precision is not None and approach_precision is not None:
        ssr = compute_ssr(
            baseline_total_shots,
            approach_total_shots,
            baseline_precision=baseline_precision,
            quartumse_precision=approach_precision,
            baseline_precision_mode="stderr",
            quartumse_precision_mode="stderr",
        )
    else:
        ssr = compute_ssr(baseline_total_shots, approach_total_shots)

    weight = approach_estimate.weight or baseline_estimate.weight or 1.0

    return ObservableComparison(
        name=name,
        baseline=baseline_estimate,
        approach=approach_estimate,
        expected_value=expected_value,
        ssr=ssr,
        variance_ratio=variance_ratio,
        in_ci=in_ci,
        weight=float(weight),
    )


def summarise_observable_comparisons(
    comparisons: Iterable[ObservableComparison],
) -> MetricsSummary:
    """Aggregate observable comparisons into summary statistics."""

    comparisons = list(comparisons)
    per_obs: Dict[str, ObservableComparison] = {item.name: item for item in comparisons}

    ssr_values: List[float] = []
    ssr_weights: List[float] = []
    coverage_flags: List[float] = []
    coverage_weights: List[float] = []
    variance_ratios: List[float] = []
    variance_weights: List[float] = []

    for comparison in comparisons:
        weight = comparison.weight
        if comparison.ssr is not None and np.isfinite(comparison.ssr):
            ssr_values.append(float(comparison.ssr))
            ssr_weights.append(weight)
        if comparison.in_ci is not None:
            coverage_flags.append(1.0 if comparison.in_ci else 0.0)
            coverage_weights.append(weight)
        if comparison.variance_ratio is not None and comparison.variance_ratio > 0:
            variance_ratios.append(float(comparison.variance_ratio))
            variance_weights.append(weight)

    ssr_average = weighted_mean(ssr_values, ssr_weights)
    ci_coverage = weighted_mean(coverage_flags, coverage_weights)
    variance_ratio_average = weighted_mean(variance_ratios, variance_weights)

    return MetricsSummary(
        comparisons=per_obs,
        ssr_average=ssr_average,
        ci_coverage=ci_coverage,
        variance_ratio_average=variance_ratio_average,
        total_observables=len(per_obs),
    )
