"""Task 8: Adaptive protocol efficiency (Measurements Bible §8, Task 8)."""

from __future__ import annotations

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
    group_results_by_replicate,
)


class AdaptiveEfficiencyTask(BenchmarkTask):
    """Task 8: Adaptive protocol efficiency."""

    task_type: TaskType = TaskType.ADAPTIVE_EFFICIENCY

    def __init__(self, config: TaskConfig) -> None:
        """Initialize adaptive efficiency task."""
        super().__init__(config)
        if config.task_type != TaskType.ADAPTIVE_EFFICIENCY:
            config.task_type = TaskType.ADAPTIVE_EFFICIENCY

    def evaluate(
        self,
        long_form_results: list[LongFormRow],
        truth_values: dict[str, float] | None = None,
    ) -> TaskOutput:
        """Evaluate adaptive protocol efficiency."""
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
        efficiency_by_n: dict[int, dict[str, float]] = {}
        success_fraction_by_n: dict[int, float] = {}

        for n, rows in results_by_n.items():
            replicate_groups = group_results_by_replicate(rows)
            replicate_quality = []
            n_settings = []
            classical_times = []

            for replicate_rows in replicate_groups.values():
                qualities = []
                for row in replicate_rows:
                    if self.config.criterion_type == CriterionType.CI_BASED:
                        quality = row.se
                    else:
                        if truth_values is None or row.observable_id not in truth_values:
                            continue
                        quality = abs(row.estimate - truth_values[row.observable_id])
                    qualities.append(quality)
                    n_settings.append(row.n_settings)
                    if row.time_classical_s is not None:
                        classical_times.append(row.time_classical_s)
                if qualities:
                    replicate_quality.append(float(np.mean(qualities)))

            if replicate_quality:
                success_fraction_by_n[n] = float(
                    np.mean([q <= self.config.epsilon for q in replicate_quality])
                )
            else:
                success_fraction_by_n[n] = 0.0

            efficiency_by_n[n] = {
                "mean_quality": float(np.mean(replicate_quality)) if replicate_quality else float("nan"),
                "mean_n_settings": float(np.mean(n_settings)) if n_settings else float("nan"),
                "mean_classical_time_s": float(np.mean(classical_times))
                if classical_times
                else float("nan"),
            }

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
            baseline_protocol_id=self.config.baseline_protocol_id
            if ssf is not None
            else None,
            metrics={
                "epsilon": self.config.epsilon,
                "delta": self.config.delta,
                "criterion_type": self.config.criterion_type.value,
                "baseline_n_star": baseline_n_star,
            },
            details={
                "efficiency_by_n": efficiency_by_n,
                "success_fraction_by_n": success_fraction_by_n,
            },
        )

    def check_criterion(
        self,
        estimates: Estimates,
        truth_values: dict[str, float] | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Check if adaptive efficiency meets the target."""
        if not estimates.estimates:
            return False, {"error": "No estimates provided"}
        if self.config.criterion_type == CriterionType.CI_BASED:
            avg_quality = float(np.mean([est.se for est in estimates.estimates]))
        else:
            if truth_values is None:
                return False, {"error": "Truth values required for truth-based criterion"}
            avg_quality = float(
                np.mean(
                    [
                        abs(est.estimate - truth_values[est.observable_id])
                        for est in estimates.estimates
                        if est.observable_id in truth_values
                    ]
                )
            )
        return avg_quality <= self.config.epsilon, {
            "average_quality": avg_quality,
            "threshold": self.config.epsilon,
        }

    def _find_n_star(self, success_fraction_by_n: dict[int, float]) -> int | None:
        target = 1.0 - self.config.delta
        for n in sorted(success_fraction_by_n.keys()):
            if success_fraction_by_n[n] >= target:
                return n
        return None
