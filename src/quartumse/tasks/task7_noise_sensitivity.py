"""Task 7: Noise sensitivity and robustness (Measurements Bible §8, Task 7)."""

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


class NoiseSensitivityTask(BenchmarkTask):
    """Task 7: Noise sensitivity and robustness."""

    task_type: TaskType = TaskType.NOISE_SENSITIVITY

    def __init__(self, config: TaskConfig) -> None:
        """Initialize noise sensitivity task."""
        super().__init__(config)
        if config.task_type != TaskType.NOISE_SENSITIVITY:
            config.task_type = TaskType.NOISE_SENSITIVITY

    def evaluate(
        self,
        long_form_results: list[LongFormRow],
        truth_values: dict[str, float] | None = None,
    ) -> TaskOutput:
        """Evaluate noise sensitivity across noise profiles."""
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
        baseline_noise = self.config.additional_params.get(
            "baseline_noise_profile", "ideal"
        )

        by_noise: dict[str, list[LongFormRow]] = {}
        for row in long_form_results:
            by_noise.setdefault(row.noise_profile_id, []).append(row)

        n_star_by_noise: dict[str, int | None] = {}
        success_fraction_by_noise: dict[str, dict[int, float]] = {}

        for noise_profile, rows in by_noise.items():
            success_fraction = self._compute_success_fraction(rows, truth_values)
            success_fraction_by_noise[noise_profile] = success_fraction
            n_star_by_noise[noise_profile] = self._find_n_star(success_fraction)

        baseline_n_star = n_star_by_noise.get(baseline_noise)
        degradation = {
            noise_profile: (
                n_star_by_noise[noise_profile] / baseline_n_star
                if baseline_n_star
                and n_star_by_noise[noise_profile] is not None
                else None
            )
            for noise_profile in n_star_by_noise
        }

        failure_rate = float(
            np.mean([n_star is None for n_star in n_star_by_noise.values()])
        )

        return TaskOutput(
            task_id=self.task_id,
            task_type=self.task_type,
            protocol_id=protocol_id,
            circuit_id=circuit_id,
            metrics={
                "epsilon": self.config.epsilon,
                "delta": self.config.delta,
                "baseline_noise_profile": baseline_noise,
                "failure_rate": failure_rate,
            },
            details={
                "n_star_by_noise": n_star_by_noise,
                "success_fraction_by_noise": success_fraction_by_noise,
                "degradation_ratio": degradation,
            },
        )

    def check_criterion(
        self,
        estimates: Estimates,
        truth_values: dict[str, float] | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Check noise sensitivity against an allowed degradation ratio."""
        degradation_ratio = estimates.metadata.get("degradation_ratio")
        if degradation_ratio is None:
            return False, {"error": "Degradation ratio not available in estimates"}
        meets = degradation_ratio <= self.config.epsilon
        return meets, {"degradation_ratio": degradation_ratio, "threshold": self.config.epsilon}

    def _compute_success_fraction(
        self,
        rows: list[LongFormRow],
        truth_values: dict[str, float] | None,
    ) -> dict[int, float]:
        results_by_n = group_results_by_n(rows)
        success_fraction_by_n: dict[int, float] = {}

        for n, n_rows in results_by_n.items():
            replicate_groups = group_results_by_replicate(n_rows)
            replicate_quality = []

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

                if qualities:
                    replicate_quality.append(float(np.mean(qualities)))

            if replicate_quality:
                success_fraction_by_n[n] = float(
                    np.mean([q <= self.config.epsilon for q in replicate_quality])
                )
            else:
                success_fraction_by_n[n] = 0.0

        return success_fraction_by_n

    def _find_n_star(self, success_fraction_by_n: dict[int, float]) -> int | None:
        target = 1.0 - self.config.delta
        for n in sorted(success_fraction_by_n.keys()):
            if success_fraction_by_n[n] >= target:
                return n
        return None
