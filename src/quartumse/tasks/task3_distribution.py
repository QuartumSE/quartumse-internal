"""Task 3: Fixed-budget distribution (Measurements Bible §8, Task 3).

Objective: Compare distributions of uncertainty and truth-error across
observables at fixed N.

This task provides detailed distributional analysis rather than a
single N* value.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from ..io.schemas import LongFormRow
from ..protocols import Estimates
from .base import (
    BenchmarkTask,
    TaskConfig,
    TaskOutput,
    TaskType,
    compute_attainment,
    group_results_by_n,
    group_results_by_replicate,
)


@dataclass
class DistributionStats:
    """Distribution statistics for a metric.

    Attributes:
        mean: Mean value.
        median: Median value.
        std: Standard deviation.
        min: Minimum value.
        max: Maximum value.
        p10: 10th percentile.
        p25: 25th percentile (Q1).
        p75: 75th percentile (Q3).
        p90: 90th percentile.
        p95: 95th percentile.
        p99: 99th percentile.
    """

    mean: float
    median: float
    std: float
    min: float
    max: float
    p10: float
    p25: float
    p75: float
    p90: float
    p95: float
    p99: float

    @classmethod
    def from_values(cls, values: list[float]) -> DistributionStats:
        """Compute statistics from a list of values."""
        if not values:
            return cls(
                mean=0, median=0, std=0, min=0, max=0,
                p10=0, p25=0, p75=0, p90=0, p95=0, p99=0
            )

        arr = np.array(values)
        return cls(
            mean=float(np.mean(arr)),
            median=float(np.median(arr)),
            std=float(np.std(arr)),
            min=float(np.min(arr)),
            max=float(np.max(arr)),
            p10=float(np.percentile(arr, 10)),
            p25=float(np.percentile(arr, 25)),
            p75=float(np.percentile(arr, 75)),
            p90=float(np.percentile(arr, 90)),
            p95=float(np.percentile(arr, 95)),
            p99=float(np.percentile(arr, 99)),
        )

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "mean": self.mean,
            "median": self.median,
            "std": self.std,
            "min": self.min,
            "max": self.max,
            "p10": self.p10,
            "p25": self.p25,
            "p75": self.p75,
            "p90": self.p90,
            "p95": self.p95,
            "p99": self.p99,
        }


class FixedBudgetDistributionTask(BenchmarkTask):
    """Task 3: Fixed-budget distribution analysis.

    Compares distributions of uncertainty and truth-error across
    observables at each fixed shot budget N.

    Reports:
    - Percentiles (median/90%/95%/max)
    - CDF curves
    - Attainment fraction vs ε
    """

    task_type: TaskType = TaskType.FIXED_BUDGET

    def __init__(self, config: TaskConfig) -> None:
        """Initialize fixed-budget task."""
        super().__init__(config)
        if config.task_type != TaskType.FIXED_BUDGET:
            config.task_type = TaskType.FIXED_BUDGET

    def evaluate(
        self,
        long_form_results: list[LongFormRow],
        truth_values: dict[str, float] | None = None,
    ) -> TaskOutput:
        """Evaluate fixed-budget distribution task.

        Args:
            long_form_results: Results from protocol execution.
            truth_values: Ground truth values.

        Returns:
            TaskOutput with distributional analysis.
        """
        if not long_form_results:
            return TaskOutput(
                task_id=self.task_id,
                task_type=self.task_type,
                protocol_id="unknown",
                circuit_id="unknown",
                metrics={"error": "No results provided"},
            )

        protocol_id = long_form_results[0].protocol_id
        circuit_id = long_form_results[0].circuit_id

        # Group by N
        results_by_n = group_results_by_n(long_form_results)

        # Compute distributions at each N
        se_distributions = {}
        error_distributions = {}
        attainment_curves = {}
        cdf_data = {}

        for n, rows in results_by_n.items():
            # SE distribution
            se_values = [row.se for row in rows]
            se_distributions[n] = DistributionStats.from_values(se_values).to_dict()

            # Error distribution (if truth available)
            if truth_values:
                errors = []
                for row in rows:
                    if row.observable_id in truth_values:
                        errors.append(abs(row.estimate - truth_values[row.observable_id]))
                if errors:
                    error_distributions[n] = DistributionStats.from_values(errors).to_dict()

            # Attainment curve
            epsilon_grid = self.config.additional_params.get(
                "epsilon_grid", [0.001, 0.005, 0.01, 0.02, 0.05, 0.1]
            )
            attainment_curves[n] = {
                eps: compute_attainment(rows, eps, use_se=True)
                for eps in epsilon_grid
            }

            # CDF data (for plotting)
            sorted_se = sorted(se_values)
            cdf_data[n] = {
                "se_values": sorted_se,
                "cdf": [i / len(sorted_se) for i in range(1, len(sorted_se) + 1)],
            }

        return TaskOutput(
            task_id=self.task_id,
            task_type=self.task_type,
            protocol_id=protocol_id,
            circuit_id=circuit_id,
            n_star=None,  # Not applicable for this task
            metrics={
                "n_evaluated": list(results_by_n.keys()),
                "n_observables": len(set(r.observable_id for r in long_form_results)),
            },
            details={
                "se_distributions": se_distributions,
                "error_distributions": error_distributions,
                "attainment_curves": attainment_curves,
                "cdf_data": cdf_data,
            },
        )

    def check_criterion(
        self,
        estimates: Estimates,
        truth_values: dict[str, float] | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Check attainment criterion.

        For fixed-budget task, checks if attainment fraction meets threshold.

        Args:
            estimates: Protocol estimates.
            truth_values: Ground truth values.

        Returns:
            Tuple of (attainment_met, details).
        """
        target_attainment = self.config.additional_params.get("target_attainment", 0.9)

        se_values = [est.se for est in estimates.estimates]
        attained = sum(1 for se in se_values if se <= self.config.epsilon)
        attainment = attained / len(se_values) if se_values else 0.0

        return attainment >= target_attainment, {
            "attainment": attainment,
            "target_attainment": target_attainment,
            "epsilon": self.config.epsilon,
            "n_attained": attained,
            "n_total": len(se_values),
        }

    def compute_comparison(
        self,
        results_a: list[LongFormRow],
        results_b: list[LongFormRow],
        truth_values: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Compare distributions between two protocols.

        Args:
            results_a: Results from protocol A.
            results_b: Results from protocol B.
            truth_values: Ground truth values.

        Returns:
            Comparison statistics.
        """
        # Group by N
        by_n_a = group_results_by_n(results_a)
        by_n_b = group_results_by_n(results_b)

        common_ns = set(by_n_a.keys()) & set(by_n_b.keys())

        comparison = {}
        for n in sorted(common_ns):
            rows_a = by_n_a[n]
            rows_b = by_n_b[n]

            se_a = [r.se for r in rows_a]
            se_b = [r.se for r in rows_b]

            # Compute relative improvement
            mean_a = np.mean(se_a)
            mean_b = np.mean(se_b)
            improvement = (mean_b - mean_a) / mean_b if mean_b > 0 else 0

            # Kolmogorov-Smirnov test for distribution difference
            from scipy import stats
            ks_stat, ks_pvalue = stats.ks_2samp(se_a, se_b)

            comparison[n] = {
                "mean_se_a": mean_a,
                "mean_se_b": mean_b,
                "relative_improvement": improvement,
                "ks_statistic": ks_stat,
                "ks_pvalue": ks_pvalue,
                "a_better_fraction": sum(1 for a, b in zip(sorted(se_a), sorted(se_b)) if a < b) / min(len(se_a), len(se_b)),
            }

        return comparison
