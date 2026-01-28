"""Task 5: Pilot-based selection and regret (Measurements Bible §8, Task 5)."""

from __future__ import annotations

from collections import Counter
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


class PilotSelectionTask(BenchmarkTask):
    """Task 5: Pilot-based protocol selection."""

    task_type: TaskType = TaskType.PILOT_SELECTION

    def __init__(self, config: TaskConfig) -> None:
        """Initialize pilot selection task."""
        super().__init__(config)
        if config.task_type != TaskType.PILOT_SELECTION:
            config.task_type = TaskType.PILOT_SELECTION

    def evaluate(
        self,
        long_form_results: list[LongFormRow],
        truth_values: dict[str, float] | None = None,
    ) -> TaskOutput:
        """Evaluate pilot-based selection accuracy and regret."""
        if not long_form_results:
            return TaskOutput(
                task_id=self.task_id,
                task_type=self.task_type,
                protocol_id="multiple",
                circuit_id="unknown",
                metrics={"error": "No results provided"},
            )

        circuit_id = long_form_results[0].circuit_id
        by_protocol: dict[str, list[LongFormRow]] = {}
        for row in long_form_results:
            by_protocol.setdefault(row.protocol_id, []).append(row)

        pilot_n, target_n = self._resolve_budgets(long_form_results)

        selection_results = []
        selection_counts: Counter[str] = Counter()

        replicate_ids = self._common_replicates(by_protocol, pilot_n, target_n)

        for replicate_id in replicate_ids:
            pilot_quality = {}
            target_quality = {}
            for protocol_id, rows in by_protocol.items():
                pilot_rows = [
                    row
                    for row in rows
                    if row.N_total == pilot_n and row.replicate_id == replicate_id
                ]
                target_rows = [
                    row
                    for row in rows
                    if row.N_total == target_n and row.replicate_id == replicate_id
                ]
                pilot_quality[protocol_id] = self._compute_quality(pilot_rows, truth_values)
                target_quality[protocol_id] = self._compute_quality(target_rows, truth_values)

            selected_protocol = min(pilot_quality, key=pilot_quality.get)
            oracle_protocol = min(target_quality, key=target_quality.get)
            selection_counts[selected_protocol] += 1

            selection_results.append(
                {
                    "replicate_id": replicate_id,
                    "selected_protocol": selected_protocol,
                    "oracle_protocol": oracle_protocol,
                    "selected_quality": pilot_quality[selected_protocol],
                    "oracle_quality": target_quality[oracle_protocol],
                    "target_quality_selected": target_quality[selected_protocol],
                }
            )

        selection_accuracy = float(
            np.mean([r["selected_protocol"] == r["oracle_protocol"] for r in selection_results])
        )
        regret = float(
            np.mean([r["target_quality_selected"] - r["oracle_quality"] for r in selection_results])
        )

        return TaskOutput(
            task_id=self.task_id,
            task_type=self.task_type,
            protocol_id="pilot_selection",
            circuit_id=circuit_id,
            selection_accuracy=selection_accuracy,
            regret=regret,
            metrics={
                "pilot_n": pilot_n,
                "target_n": target_n,
                "selection_accuracy": selection_accuracy,
                "regret": regret,
                "criterion_type": self.config.criterion_type.value,
            },
            details={
                "selection_counts": dict(selection_counts),
                "selection_results": selection_results,
                "protocols": sorted(by_protocol.keys()),
            },
        )

    def check_criterion(
        self,
        estimates: Estimates,
        truth_values: dict[str, float] | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Check if selection accuracy meets the target."""
        selection_accuracy = estimates.metadata.get("selection_accuracy")
        if selection_accuracy is None:
            return False, {"error": "Selection accuracy not available in estimates"}
        target = self.config.additional_params.get(
            "selection_accuracy_target", 1.0 - self.config.delta
        )
        return selection_accuracy >= target, {
            "selection_accuracy": selection_accuracy,
            "target": target,
        }

    def _resolve_budgets(self, rows: list[LongFormRow]) -> tuple[int, int]:
        pilot_n = self.config.additional_params.get("pilot_n")
        target_n = self.config.additional_params.get("target_n")
        n_values = sorted({row.N_total for row in rows})
        if pilot_n is None:
            pilot_n = n_values[0]
        if target_n is None:
            target_n = n_values[-1]
        return int(pilot_n), int(target_n)

    def _common_replicates(
        self,
        by_protocol: dict[str, list[LongFormRow]],
        pilot_n: int,
        target_n: int,
    ) -> list[int]:
        common_replicates: set[int] | None = None
        for rows in by_protocol.values():
            by_n = group_results_by_n(rows)
            pilot_reps = {
                row.replicate_id for row in by_n.get(pilot_n, []) if row.N_total == pilot_n
            }
            target_reps = {
                row.replicate_id for row in by_n.get(target_n, []) if row.N_total == target_n
            }
            reps = pilot_reps & target_reps
            if common_replicates is None:
                common_replicates = set(reps)
            else:
                common_replicates &= reps
        return sorted(common_replicates or [])

    def _compute_quality(
        self,
        rows: list[LongFormRow],
        truth_values: dict[str, float] | None,
    ) -> float:
        if not rows:
            return float("inf")
        if self.config.criterion_type == CriterionType.CI_BASED:
            return float(np.mean([row.se for row in rows]))
        if truth_values is None:
            return float("inf")
        errors = []
        for row in rows:
            if row.observable_id in truth_values:
                errors.append(abs(row.estimate - truth_values[row.observable_id]))
        return float(np.mean(errors)) if errors else float("inf")
