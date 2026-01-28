"""Task 2: Average/weighted accuracy target (Measurements Bible §8, Task 2).

Objective: Minimal N such that the average (or weighted) accuracy meets
the target with probability 1-δ.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ..io.schemas import LongFormRow
from ..protocols import Estimates
from ..utils.metrics import weighted_mean
from .base import (
    BenchmarkTask,
    CriterionType,
    TaskConfig,
    TaskOutput,
    TaskType,
    group_results_by_n,
    group_results_by_replicate,
)


class AverageTargetTask(BenchmarkTask):
    """Task 2: Average/weighted accuracy target."""

    task_type: TaskType = TaskType.AVERAGE_TARGET

    def __init__(self, config: TaskConfig) -> None:
        """Initialize average target task."""
        super().__init__(config)
        if config.task_type != TaskType.AVERAGE_TARGET:
            config.task_type = TaskType.AVERAGE_TARGET

    def evaluate(
        self,
        long_form_results: list[LongFormRow],
        truth_values: dict[str, float] | None = None,
    ) -> TaskOutput:
        """Evaluate average/weighted accuracy target.

        Args:
            long_form_results: Results from protocol execution.
            truth_values: Ground truth values.

        Returns:
            TaskOutput with N*, SSF, and average-quality curves.
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
        weights = self._resolve_weights(long_form_results)

        average_quality_by_n: dict[int, dict[str, float]] = {}
        success_fraction_by_n: dict[int, float] = {}

        for n, rows in results_by_n.items():
            replicate_groups = group_results_by_replicate(rows)
            replicate_quality = []

            for replicate_rows in replicate_groups.values():
                avg_quality = self._compute_average_quality(replicate_rows, truth_values, weights)
                if avg_quality is not None:
                    replicate_quality.append(avg_quality)

            if replicate_quality:
                average_quality_by_n[n] = {
                    "mean": float(np.mean(replicate_quality)),
                    "median": float(np.median(replicate_quality)),
                }
                success_fraction_by_n[n] = float(
                    np.mean([q <= self.config.epsilon for q in replicate_quality])
                )
            else:
                average_quality_by_n[n] = {"mean": float("nan"), "median": float("nan")}
                success_fraction_by_n[n] = 0.0

        n_star = self._find_n_star(success_fraction_by_n)
        baseline_n_star = self.config.additional_params.get("baseline_n_star")
        ssf = self.compute_ssf(n_star, baseline_n_star) if baseline_n_star else None

        return TaskOutput(
            task_id=self.task_id,
            task_type=self.task_type,
            protocol_id=protocol_id,
            circuit_id=circuit_id,
            n_star=n_star,
            ssf=ssf,
            baseline_protocol_id=self.config.baseline_protocol_id if ssf is not None else None,
            metrics={
                "epsilon": self.config.epsilon,
                "delta": self.config.delta,
                "criterion_type": self.config.criterion_type.value,
            },
            details={
                "average_quality_by_n": average_quality_by_n,
                "success_fraction_by_n": success_fraction_by_n,
                "weights": weights,
            },
        )

    def check_criterion(
        self,
        estimates: Estimates,
        truth_values: dict[str, float] | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Check if average/weighted criterion is satisfied."""
        weights = self.config.additional_params.get("observable_weights")
        if not isinstance(weights, dict):
            weights = {est.observable_id: 1.0 for est in estimates.estimates}
        avg_quality = self._compute_average_quality_from_estimates(estimates, truth_values, weights)
        if avg_quality is None:
            return False, {"error": "Truth values required for truth-based criterion"}
        return avg_quality <= self.config.epsilon, {
            "average_quality": avg_quality,
            "threshold": self.config.epsilon,
        }

    def _resolve_weights(self, rows: list[LongFormRow]) -> dict[str, float]:
        weights = self.config.additional_params.get("observable_weights")
        if isinstance(weights, dict):
            return {str(k): float(v) for k, v in weights.items()}
        return {row.observable_id: float(row.coefficient) for row in rows}

    def _compute_average_quality(
        self,
        rows: list[LongFormRow],
        truth_values: dict[str, float] | None,
        weights: dict[str, float],
    ) -> float | None:
        qualities = []
        weight_values = []
        for row in rows:
            if self.config.criterion_type == CriterionType.CI_BASED:
                quality = row.se
            else:
                if truth_values is None or row.observable_id not in truth_values:
                    return None
                quality = abs(row.estimate - truth_values[row.observable_id])
            qualities.append(quality)
            weight_values.append(weights.get(row.observable_id, 1.0))

        return weighted_mean(qualities, weight_values)

    def _compute_average_quality_from_estimates(
        self,
        estimates: Estimates,
        truth_values: dict[str, float] | None,
        weights: dict[str, float],
    ) -> float | None:
        qualities = []
        weight_values = []
        for est in estimates.estimates:
            if self.config.criterion_type == CriterionType.CI_BASED:
                quality = est.se
            else:
                if truth_values is None or est.observable_id not in truth_values:
                    return None
                quality = abs(est.estimate - truth_values[est.observable_id])
            qualities.append(quality)
            weight_values.append(weights.get(est.observable_id, 1.0))

        return weighted_mean(qualities, weight_values)

    def _find_n_star(self, success_fraction_by_n: dict[int, float]) -> int | None:
        target = 1.0 - self.config.delta
        for n in sorted(success_fraction_by_n.keys()):
            if success_fraction_by_n[n] >= target:
                return n
        return None
