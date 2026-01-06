"""Task 4: Dominance and crossover (Measurements Bible §8, Task 4).

Objective: Determine shot budgets where one protocol dominates another.

Reports:
- Crossover point(s) if they exist
- Observables preventing dominance otherwise
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from ..io.schemas import LongFormRow
from ..protocols import Estimates
from .base import (
    BenchmarkTask,
    CriterionType,
    TaskConfig,
    TaskOutput,
    TaskType,
    group_results_by_n,
)


@dataclass
class DominanceResult:
    """Result of dominance analysis.

    Attributes:
        crossover_n: N where protocol A starts dominating B.
        always_dominates: True if A always dominates B.
        never_dominates: True if A never dominates B.
        blocking_observables: Observables preventing dominance.
    """

    crossover_n: int | None
    always_dominates: bool
    never_dominates: bool
    blocking_observables: list[str]


class DominanceTask(BenchmarkTask):
    """Task 4: Dominance and crossover analysis.

    Compares two protocols to find:
    - Whether one dominates the other at all N
    - Crossover points where dominance switches
    - Observables that prevent dominance

    Two versions:
    - Uncertainty-based: using simultaneous CIs
    - Truth-based: using actual errors (preferred in simulation)
    """

    task_type: TaskType = TaskType.DOMINANCE

    def __init__(self, config: TaskConfig) -> None:
        """Initialize dominance task."""
        super().__init__(config)
        if config.task_type != TaskType.DOMINANCE:
            config.task_type = TaskType.DOMINANCE

    def evaluate(
        self,
        long_form_results: list[LongFormRow],
        truth_values: dict[str, float] | None = None,
    ) -> TaskOutput:
        """Evaluate dominance for a single protocol.

        Note: For full dominance analysis, use compare_protocols().
        This method provides per-N quality metrics.

        Args:
            long_form_results: Results from protocol execution.
            truth_values: Ground truth values.

        Returns:
            TaskOutput with quality metrics per N.
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

        results_by_n = group_results_by_n(long_form_results)

        # Compute quality metric at each N
        quality_by_n = {}
        for n, rows in results_by_n.items():
            if self.config.criterion_type == CriterionType.CI_BASED:
                # Use max SE as quality (worst-case)
                quality_by_n[n] = {
                    "max_se": max(r.se for r in rows),
                    "mean_se": np.mean([r.se for r in rows]),
                    "median_se": np.median([r.se for r in rows]),
                }
            else:
                # Use max error
                if truth_values:
                    errors = [
                        abs(r.estimate - truth_values.get(r.observable_id, r.estimate))
                        for r in rows
                    ]
                    quality_by_n[n] = {
                        "max_error": max(errors),
                        "mean_error": np.mean(errors),
                        "median_error": np.median(errors),
                    }
                else:
                    quality_by_n[n] = {"error": "Truth values required"}

        return TaskOutput(
            task_id=self.task_id,
            task_type=self.task_type,
            protocol_id=protocol_id,
            circuit_id=circuit_id,
            metrics={"n_evaluated": sorted(results_by_n.keys())},
            details={"quality_by_n": quality_by_n},
        )

    def check_criterion(
        self,
        estimates: Estimates,
        truth_values: dict[str, float] | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Check if protocol meets quality threshold.

        Args:
            estimates: Protocol estimates.
            truth_values: Ground truth values.

        Returns:
            Tuple of (meets_threshold, details).
        """
        if self.config.criterion_type == CriterionType.CI_BASED:
            max_se = max(est.se for est in estimates.estimates)
            meets = max_se <= self.config.epsilon
            return meets, {"max_se": max_se, "threshold": self.config.epsilon}
        else:
            if not truth_values:
                return False, {"error": "Truth values required"}
            max_error = max(
                abs(est.estimate - truth_values.get(est.observable_id, est.estimate))
                for est in estimates.estimates
            )
            meets = max_error <= self.config.epsilon
            return meets, {"max_error": max_error, "threshold": self.config.epsilon}

    def compare_protocols(
        self,
        results_a: list[LongFormRow],
        results_b: list[LongFormRow],
        truth_values: dict[str, float] | None = None,
        metric: str = "mean_se",
    ) -> dict[str, Any]:
        """Compare two protocols for dominance.

        Args:
            results_a: Results from protocol A (candidate).
            results_b: Results from protocol B (baseline).
            truth_values: Ground truth values.
            metric: Metric to use for comparison.

        Returns:
            Dominance analysis results.
        """
        by_n_a = group_results_by_n(results_a)
        by_n_b = group_results_by_n(results_b)

        common_ns = sorted(set(by_n_a.keys()) & set(by_n_b.keys()))

        if not common_ns:
            return {"error": "No common N values"}

        # Compute metric at each N for both protocols
        metrics_a = {}
        metrics_b = {}

        for n in common_ns:
            rows_a = by_n_a[n]
            rows_b = by_n_b[n]

            if metric == "max_se":
                metrics_a[n] = max(r.se for r in rows_a)
                metrics_b[n] = max(r.se for r in rows_b)
            elif metric == "mean_se":
                metrics_a[n] = np.mean([r.se for r in rows_a])
                metrics_b[n] = np.mean([r.se for r in rows_b])
            elif metric == "median_se":
                metrics_a[n] = np.median([r.se for r in rows_a])
                metrics_b[n] = np.median([r.se for r in rows_b])
            elif metric in ("max_error", "mean_error") and truth_values:
                errors_a = [
                    abs(r.estimate - truth_values.get(r.observable_id, r.estimate))
                    for r in rows_a
                ]
                errors_b = [
                    abs(r.estimate - truth_values.get(r.observable_id, r.estimate))
                    for r in rows_b
                ]
                if metric == "max_error":
                    metrics_a[n] = max(errors_a)
                    metrics_b[n] = max(errors_b)
                else:
                    metrics_a[n] = np.mean(errors_a)
                    metrics_b[n] = np.mean(errors_b)

        # Determine dominance
        a_better = [n for n in common_ns if metrics_a[n] < metrics_b[n]]
        b_better = [n for n in common_ns if metrics_b[n] < metrics_a[n]]

        # Find crossover point
        crossover_n = None
        if a_better and b_better:
            # Find where A starts being better
            for i, n in enumerate(common_ns[1:], 1):
                prev_n = common_ns[i - 1]
                if metrics_b[prev_n] < metrics_a[prev_n] and metrics_a[n] < metrics_b[n]:
                    crossover_n = n
                    break

        # Identify blocking observables (those where A is worse)
        blocking = []
        if b_better:
            n_worst = max(b_better)  # N where B is most better
            rows_a = by_n_a[n_worst]
            rows_b = by_n_b[n_worst]

            se_a = {r.observable_id: r.se for r in rows_a}
            se_b = {r.observable_id: r.se for r in rows_b}

            for obs_id in se_a:
                if obs_id in se_b and se_a[obs_id] > se_b[obs_id]:
                    blocking.append(obs_id)

        return {
            "crossover_n": crossover_n,
            "a_dominates_at": a_better,
            "b_dominates_at": b_better,
            "always_a_better": len(b_better) == 0 and len(a_better) > 0,
            "always_b_better": len(a_better) == 0 and len(b_better) > 0,
            "blocking_observables": blocking,
            "metrics_a": metrics_a,
            "metrics_b": metrics_b,
            "metric_used": metric,
        }

    def find_crossover_points(
        self,
        results_a: list[LongFormRow],
        results_b: list[LongFormRow],
        metrics: list[str] = None,
    ) -> dict[str, int | None]:
        """Find crossover points for multiple metrics.

        Args:
            results_a: Results from protocol A.
            results_b: Results from protocol B.
            metrics: Metrics to analyze.

        Returns:
            Dict mapping metric name to crossover N.
        """
        if metrics is None:
            metrics = ["mean_se", "max_se", "median_se"]

        crossovers = {}
        for metric in metrics:
            comparison = self.compare_protocols(results_a, results_b, metric=metric)
            crossovers[metric] = comparison.get("crossover_n")

        return crossovers
