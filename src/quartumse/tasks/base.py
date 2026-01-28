"""Base classes for benchmark tasks (Measurements Bible §8).

This module defines the abstract base class for benchmark tasks and
common utilities used across all task implementations.

Tasks define decision problems that compute N*, curves, and comparisons
for evaluating measurement protocol performance.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ..io.schemas import LongFormRow, TaskResult
from ..protocols import Estimates


class TaskType(str, Enum):
    """Types of benchmark tasks."""

    WORST_CASE = "worst_case"  # Task 1
    AVERAGE_TARGET = "average_target"  # Task 2
    FIXED_BUDGET = "fixed_budget"  # Task 3
    DOMINANCE = "dominance"  # Task 4
    PILOT_SELECTION = "pilot_selection"  # Task 5
    BIAS_VARIANCE = "bias_variance"  # Task 6
    NOISE_SENSITIVITY = "noise_sensitivity"  # Task 7
    ADAPTIVE_EFFICIENCY = "adaptive_efficiency"  # Task 8


class CriterionType(str, Enum):
    """Types of stopping/success criteria."""

    CI_BASED = "ci_based"  # Based on confidence intervals
    TRUTH_BASED = "truth_based"  # Based on ground truth error


@dataclass
class TaskConfig:
    """Configuration for a benchmark task.

    Attributes:
        task_id: Unique identifier for the task.
        task_type: Type of task.
        epsilon: Target precision (for precision-based tasks).
        delta: Global failure probability.
        criterion_type: Type of criterion to use.
        fwer_method: FWER control method.
        n_grid: Shot budget grid to evaluate.
        n_replicates: Number of repetitions per configuration.
        baseline_protocol_id: Baseline protocol for SSF computation.
        additional_params: Task-specific additional parameters.
    """

    task_id: str
    task_type: TaskType
    epsilon: float = 0.01
    delta: float = 0.05
    criterion_type: CriterionType = CriterionType.CI_BASED
    fwer_method: str = "bonferroni"
    n_grid: list[int] = field(default_factory=lambda: [100, 500, 1000, 5000, 10000])
    n_replicates: int = 10
    baseline_protocol_id: str = "direct_grouped"
    additional_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskOutput:
    """Output from a benchmark task.

    Attributes:
        task_id: Task identifier.
        task_type: Type of task.
        protocol_id: Protocol evaluated.
        circuit_id: Circuit used.
        n_star: Shots-to-target (if applicable).
        ssf: Shot-savings factor vs baseline.
        metrics: Task-specific metrics.
        details: Detailed results per observable/replicate.
        metadata: Additional metadata.
    """

    task_id: str
    task_type: TaskType
    protocol_id: str
    circuit_id: str
    n_star: int | None = None
    ssf: float | None = None
    baseline_protocol_id: str | None = None
    worst_observable_id: str | None = None
    crossover_n: int | None = None
    selection_accuracy: float | None = None
    regret: float | None = None
    metrics: dict[str, float] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_task_result(self, run_id: str) -> TaskResult:
        """Convert to TaskResult schema."""
        return TaskResult(
            task_id=self.task_id,
            task_name=self.task_type.value,
            run_id=run_id,
            circuit_id=self.circuit_id,
            protocol_id=self.protocol_id,
            epsilon=self.metrics.get("epsilon"),
            delta=self.metrics.get("delta"),
            fwer_method=self.metrics.get("fwer_method"),
            N_star=self.n_star,
            ssf=self.ssf,
            baseline_protocol_id=self.baseline_protocol_id,
            worst_observable_id=self.worst_observable_id,
            crossover_N=self.crossover_n,
            selection_accuracy=self.selection_accuracy
            if self.selection_accuracy is not None
            else self.metrics.get("selection_accuracy"),
            regret=self.regret if self.regret is not None else self.metrics.get("regret"),
            outputs={
                "metrics": self.metrics,
                "details": self.details,
                "metadata": self.metadata,
            },
        )


class BenchmarkTask(ABC):
    """Abstract base class for benchmark tasks.

    Each task defines a decision problem for evaluating protocols.
    Tasks compute N* (shots-to-target), curves, and comparisons.
    """

    task_type: TaskType = TaskType.WORST_CASE

    def __init__(self, config: TaskConfig) -> None:
        """Initialize task with configuration.

        Args:
            config: Task configuration.
        """
        self.config = config

    @property
    def task_id(self) -> str:
        """Task identifier."""
        return self.config.task_id

    @abstractmethod
    def evaluate(
        self,
        long_form_results: list[LongFormRow],
        truth_values: dict[str, float] | None = None,
    ) -> TaskOutput:
        """Evaluate the task from long-form results.

        Args:
            long_form_results: Results from protocol execution.
            truth_values: Ground truth values (observable_id -> value).

        Returns:
            TaskOutput with evaluation results.
        """
        pass

    @abstractmethod
    def check_criterion(
        self,
        estimates: Estimates,
        truth_values: dict[str, float] | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Check if the task criterion is satisfied.

        Args:
            estimates: Protocol estimates for observables.
            truth_values: Ground truth values.

        Returns:
            Tuple of (criterion_satisfied, details_dict).
        """
        pass

    def compute_n_star(
        self,
        results_by_n: dict[int, list[LongFormRow]],
        truth_values: dict[str, float] | None = None,
    ) -> int | None:
        """Compute N* (minimum N that satisfies criterion).

        Args:
            results_by_n: Results grouped by shot budget N.
            truth_values: Ground truth values.

        Returns:
            Minimum N that satisfies criterion, or None if never satisfied.
        """
        sorted_ns = sorted(results_by_n.keys())

        for n in sorted_ns:
            rows = results_by_n[n]
            if self._check_criterion_from_rows(rows, truth_values):
                return n

        return None

    def _check_criterion_from_rows(
        self,
        rows: list[LongFormRow],
        truth_values: dict[str, float] | None = None,
    ) -> bool:
        """Check criterion from LongFormRows.

        Default implementation - subclasses may override.
        """
        # Extract estimates
        estimates = {}
        ses = {}
        ci_lows = {}
        ci_highs = {}

        for row in rows:
            obs_id = row.observable_id
            estimates[obs_id] = row.estimate
            ses[obs_id] = row.se
            if row.ci_low is not None:
                ci_lows[obs_id] = row.ci_low
            if row.ci_high is not None:
                ci_highs[obs_id] = row.ci_high

        # Use CI half-width as criterion (for CI-based tasks)
        if self.config.criterion_type == CriterionType.CI_BASED:
            for obs_id in estimates:
                if obs_id in ci_lows and obs_id in ci_highs:
                    half_width = (ci_highs[obs_id] - ci_lows[obs_id]) / 2
                    if half_width > self.config.epsilon:
                        return False
            return True

        # Use truth-based error (for truth-based tasks)
        elif self.config.criterion_type == CriterionType.TRUTH_BASED:
            if truth_values is None:
                raise ValueError("Truth values required for truth-based criterion")
            for obs_id, est in estimates.items():
                if obs_id in truth_values:
                    error = abs(est - truth_values[obs_id])
                    if error > self.config.epsilon:
                        return False
            return True

        return False

    def compute_ssf(
        self,
        n_star_protocol: int | None,
        n_star_baseline: int | None,
    ) -> float | None:
        """Compute shot-savings factor.

        SSF = N*_baseline / N*_protocol

        Args:
            n_star_protocol: N* for the protocol being evaluated.
            n_star_baseline: N* for the baseline protocol.

        Returns:
            SSF value, or None if either N* is None.
        """
        if n_star_protocol is None or n_star_baseline is None:
            return None
        if n_star_protocol == 0:
            return float("inf")
        return n_star_baseline / n_star_protocol


def group_results_by_n(rows: list[LongFormRow]) -> dict[int, list[LongFormRow]]:
    """Group long-form results by shot budget N.

    Args:
        rows: List of LongFormRow objects.

    Returns:
        Dict mapping N_total to list of rows.
    """
    result: dict[int, list[LongFormRow]] = {}
    for row in rows:
        if row.N_total not in result:
            result[row.N_total] = []
        result[row.N_total].append(row)
    return result


def group_results_by_replicate(
    rows: list[LongFormRow],
) -> dict[int, list[LongFormRow]]:
    """Group long-form results by replicate ID.

    Args:
        rows: List of LongFormRow objects.

    Returns:
        Dict mapping replicate_id to list of rows.
    """
    result: dict[int, list[LongFormRow]] = {}
    for row in rows:
        if row.replicate_id not in result:
            result[row.replicate_id] = []
        result[row.replicate_id].append(row)
    return result


def compute_attainment(
    rows: list[LongFormRow],
    epsilon: float,
    use_se: bool = True,
) -> float:
    """Compute attainment fraction at target precision.

    f(N;ε) = (1/M) × #{i : quality_i(N) ≤ ε}

    Args:
        rows: Results for a single N.
        epsilon: Target precision.
        use_se: If True, use SE; otherwise use CI half-width.

    Returns:
        Attainment fraction [0, 1].
    """
    if not rows:
        return 0.0

    attained = 0
    for row in rows:
        if use_se:
            quality = row.se
        else:
            if row.ci_low is not None and row.ci_high is not None:
                quality = (row.ci_high - row.ci_low) / 2
            else:
                quality = row.se

        if quality <= epsilon:
            attained += 1

    return attained / len(rows)
