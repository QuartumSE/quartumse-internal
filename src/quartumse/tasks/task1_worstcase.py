"""Task 1: Worst-case guarantee (Measurements Bible §8, Task 1).

Objective: Minimal N such that ALL observables meet target at global
confidence 1-δ.

This is the most stringent task - requires simultaneous precision
guarantees for all M observables with FWER control.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..io.schemas import LongFormRow
from ..protocols import Estimates
from ..stats import compute_fwer_adjustment
from .base import (
    BenchmarkTask,
    CriterionType,
    TaskConfig,
    TaskOutput,
    TaskType,
    group_results_by_n,
    group_results_by_replicate,
)


@dataclass
class WorstCaseResult:
    """Detailed result for worst-case task.

    Attributes:
        n_star: Shots-to-target.
        worst_observable_id: Observable with worst metric.
        worst_metric_value: Value of worst metric.
        all_observables_met: Whether all observables met criterion.
        per_observable_status: Status for each observable.
    """

    n_star: int | None
    worst_observable_id: str | None
    worst_metric_value: float
    all_observables_met: bool
    per_observable_status: dict[str, dict[str, Any]]


class WorstCaseTask(BenchmarkTask):
    """Task 1: Worst-case simultaneous guarantee.

    Computes N* such that max_i(quality_i) ≤ ε with probability 1-δ.

    For CI-based criterion (default):
    - Constructs simultaneous CIs at global δ using FWER correction
    - Stops when each CI half-width ≤ ε

    For truth-based criterion:
    - Stops when max_i |ô_i - o_i| ≤ ε
    - Reports empirical success probability across repetitions
    """

    task_type: TaskType = TaskType.WORST_CASE

    def __init__(self, config: TaskConfig) -> None:
        """Initialize worst-case task."""
        super().__init__(config)
        if config.task_type != TaskType.WORST_CASE:
            config.task_type = TaskType.WORST_CASE

    def evaluate(
        self,
        long_form_results: list[LongFormRow],
        truth_values: dict[str, float] | None = None,
    ) -> TaskOutput:
        """Evaluate worst-case task.

        Args:
            long_form_results: Results from protocol execution.
            truth_values: Ground truth values.

        Returns:
            TaskOutput with N*, SSF, and detailed results.
        """
        if not long_form_results:
            return TaskOutput(
                task_id=self.task_id,
                task_type=self.task_type,
                protocol_id="unknown",
                circuit_id="unknown",
                n_star=None,
                metrics={"error": "No results provided"},
            )

        protocol_id = long_form_results[0].protocol_id
        circuit_id = long_form_results[0].circuit_id

        # Group by N
        results_by_n = group_results_by_n(long_form_results)

        # Find N*
        n_star = self._find_n_star(results_by_n, truth_values)

        # Find worst observable at each N
        worst_by_n = self._find_worst_observables(results_by_n, truth_values)

        # Compute detailed results
        details = self._compute_details(results_by_n, truth_values, n_star)

        return TaskOutput(
            task_id=self.task_id,
            task_type=self.task_type,
            protocol_id=protocol_id,
            circuit_id=circuit_id,
            n_star=n_star,
            metrics={
                "epsilon": self.config.epsilon,
                "delta": self.config.delta,
                "fwer_method": self.config.fwer_method,
            },
            details={
                "worst_by_n": worst_by_n,
                "criterion_type": self.config.criterion_type.value,
                **details,
            },
        )

    def check_criterion(
        self,
        estimates: Estimates,
        truth_values: dict[str, float] | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Check if worst-case criterion is satisfied.

        Args:
            estimates: Protocol estimates.
            truth_values: Ground truth values.

        Returns:
            Tuple of (all_satisfied, details).
        """
        M = len(estimates.estimates)

        if self.config.criterion_type == CriterionType.CI_BASED:
            # Get FWER-adjusted confidence level
            compute_fwer_adjustment(M, self.config.delta, self.config.fwer_method)

            # Check all CI half-widths
            worst_obs = None
            worst_value = 0.0
            all_satisfied = True

            for est in estimates.estimates:
                # Compute CI half-width (using SE * z for normal)
                from scipy import stats

                z = stats.norm.ppf(1 - self.config.delta / (2 * M))
                half_width = est.se * z

                if half_width > self.config.epsilon:
                    all_satisfied = False
                    if half_width > worst_value:
                        worst_value = half_width
                        worst_obs = est.observable_id

            return all_satisfied, {
                "worst_observable": worst_obs,
                "worst_half_width": worst_value,
                "threshold": self.config.epsilon,
            }

        elif self.config.criterion_type == CriterionType.TRUTH_BASED:
            if truth_values is None:
                return False, {"error": "Truth values required"}

            worst_obs = None
            worst_error = 0.0

            for est in estimates.estimates:
                truth = truth_values.get(est.observable_id)
                if truth is not None:
                    error = abs(est.estimate - truth)
                    if error > worst_error:
                        worst_error = error
                        worst_obs = est.observable_id

            all_satisfied = worst_error <= self.config.epsilon

            return all_satisfied, {
                "worst_observable": worst_obs,
                "worst_error": worst_error,
                "threshold": self.config.epsilon,
            }

        return False, {"error": "Unknown criterion type"}

    def _find_n_star(
        self,
        results_by_n: dict[int, list[LongFormRow]],
        truth_values: dict[str, float] | None,
    ) -> int | None:
        """Find N* for worst-case criterion."""
        sorted_ns = sorted(results_by_n.keys())

        for n in sorted_ns:
            rows = results_by_n[n]

            # Group by replicate to check across replicates
            by_replicate = group_results_by_replicate(rows)

            # For each replicate, check if criterion is met
            success_count = 0
            for _rep_id, rep_rows in by_replicate.items():
                if self._check_replicate_criterion(rep_rows, truth_values):
                    success_count += 1

            # Require success in at least (1-δ) fraction of replicates
            required_fraction = 1 - self.config.delta
            if len(by_replicate) > 0:
                actual_fraction = success_count / len(by_replicate)
                if actual_fraction >= required_fraction:
                    return n

        return None

    def _check_replicate_criterion(
        self,
        rows: list[LongFormRow],
        truth_values: dict[str, float] | None,
    ) -> bool:
        """Check criterion for a single replicate."""
        M = len(rows)

        if self.config.criterion_type == CriterionType.CI_BASED:
            # Get FWER-adjusted threshold
            from scipy import stats

            z = stats.norm.ppf(1 - self.config.delta / (2 * M))

            for row in rows:
                half_width = row.se * z
                if half_width > self.config.epsilon:
                    return False
            return True

        elif self.config.criterion_type == CriterionType.TRUTH_BASED:
            if truth_values is None:
                return False

            for row in rows:
                truth = truth_values.get(row.observable_id)
                if truth is not None:
                    error = abs(row.estimate - truth)
                    if error > self.config.epsilon:
                        return False
            return True

        return False

    def _find_worst_observables(
        self,
        results_by_n: dict[int, list[LongFormRow]],
        truth_values: dict[str, float] | None,
    ) -> dict[int, dict[str, Any]]:
        """Find worst observable at each N."""
        result = {}

        for n, rows in results_by_n.items():
            worst_obs = None
            worst_value = 0.0

            for row in rows:
                if self.config.criterion_type == CriterionType.CI_BASED:
                    value = row.se
                else:
                    if truth_values and row.observable_id in truth_values:
                        value = abs(row.estimate - truth_values[row.observable_id])
                    else:
                        value = row.se

                if value > worst_value:
                    worst_value = value
                    worst_obs = row.observable_id

            result[n] = {
                "worst_observable": worst_obs,
                "worst_value": worst_value,
                "meets_criterion": worst_value <= self.config.epsilon,
            }

        return result

    def _compute_details(
        self,
        results_by_n: dict[int, list[LongFormRow]],
        truth_values: dict[str, float] | None,
        n_star: int | None,
    ) -> dict[str, Any]:
        """Compute detailed task results."""
        # Compute success rate at each N
        success_rates = {}
        for n, rows in results_by_n.items():
            by_replicate = group_results_by_replicate(rows)
            successes = sum(
                1
                for rep_rows in by_replicate.values()
                if self._check_replicate_criterion(rep_rows, truth_values)
            )
            success_rates[n] = successes / len(by_replicate) if by_replicate else 0.0

        return {
            "success_rates_by_n": success_rates,
            "n_star": n_star,
            "n_evaluated": sorted(results_by_n.keys()),
        }
