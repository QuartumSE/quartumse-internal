"""Task 6: Bias-variance decomposition (Measurements Bible §8, Task 6).

Objective: Separate systematic bias from variance.

Required in simulation, recommended otherwise.

For each observable:
- Bias across repetitions
- Variance across repetitions
- RMSE

Aggregate:
- Mean/max bias, distribution of biases
- Bias-vs-noise-level curves
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
    group_results_by_n,
)


@dataclass
class BiasVarianceStats:
    """Bias-variance decomposition for an observable.

    Attributes:
        observable_id: Observable identifier.
        truth_value: Ground truth value.
        mean_estimate: Mean estimate across replicates.
        bias: Mean estimate - truth.
        variance: Variance of estimates.
        mse: Mean squared error.
        rmse: Root mean squared error.
        std: Standard deviation of estimates.
        n_replicates: Number of replicates.
    """

    observable_id: str
    truth_value: float
    mean_estimate: float
    bias: float
    variance: float
    mse: float
    rmse: float
    std: float
    n_replicates: int

    @classmethod
    def compute(
        cls,
        observable_id: str,
        estimates: list[float],
        truth_value: float,
    ) -> BiasVarianceStats:
        """Compute bias-variance statistics.

        Args:
            observable_id: Observable identifier.
            estimates: List of estimates across replicates.
            truth_value: Ground truth value.

        Returns:
            BiasVarianceStats with decomposition.
        """
        estimates_arr = np.array(estimates)
        mean_est = float(np.mean(estimates_arr))
        bias = mean_est - truth_value
        variance = float(np.var(estimates_arr, ddof=1))
        std = float(np.std(estimates_arr, ddof=1))

        # MSE = bias^2 + variance
        # Or equivalently: MSE = E[(est - truth)^2]
        squared_errors = (estimates_arr - truth_value) ** 2
        mse = float(np.mean(squared_errors))
        rmse = float(np.sqrt(mse))

        return cls(
            observable_id=observable_id,
            truth_value=truth_value,
            mean_estimate=mean_est,
            bias=bias,
            variance=variance,
            mse=mse,
            rmse=rmse,
            std=std,
            n_replicates=len(estimates),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "observable_id": self.observable_id,
            "truth_value": self.truth_value,
            "mean_estimate": self.mean_estimate,
            "bias": self.bias,
            "variance": self.variance,
            "mse": self.mse,
            "rmse": self.rmse,
            "std": self.std,
            "n_replicates": self.n_replicates,
        }


class BiasVarianceTask(BenchmarkTask):
    """Task 6: Bias-variance decomposition.

    Separates systematic bias from variance in protocol estimates.
    Requires multiple replicates and ground truth values.
    """

    task_type: TaskType = TaskType.BIAS_VARIANCE

    def __init__(self, config: TaskConfig) -> None:
        """Initialize bias-variance task."""
        super().__init__(config)
        if config.task_type != TaskType.BIAS_VARIANCE:
            config.task_type = TaskType.BIAS_VARIANCE

    def evaluate(
        self,
        long_form_results: list[LongFormRow],
        truth_values: dict[str, float] | None = None,
    ) -> TaskOutput:
        """Evaluate bias-variance decomposition.

        Args:
            long_form_results: Results from protocol execution.
            truth_values: Ground truth values (required).

        Returns:
            TaskOutput with bias-variance analysis.
        """
        if not long_form_results:
            return TaskOutput(
                task_id=self.task_id,
                task_type=self.task_type,
                protocol_id="unknown",
                circuit_id="unknown",
                metrics={"error": "No results provided"},
            )

        if not truth_values:
            return TaskOutput(
                task_id=self.task_id,
                task_type=self.task_type,
                protocol_id=long_form_results[0].protocol_id,
                circuit_id=long_form_results[0].circuit_id,
                metrics={"error": "Truth values required for bias-variance analysis"},
            )

        protocol_id = long_form_results[0].protocol_id
        circuit_id = long_form_results[0].circuit_id

        # Group by N
        results_by_n = group_results_by_n(long_form_results)

        # Compute bias-variance at each N
        analysis_by_n = {}

        for n, rows in results_by_n.items():
            # Group estimates by observable
            estimates_by_obs: dict[str, list[float]] = {}
            for row in rows:
                if row.observable_id not in estimates_by_obs:
                    estimates_by_obs[row.observable_id] = []
                estimates_by_obs[row.observable_id].append(row.estimate)

            # Compute stats for each observable
            per_obs_stats = []
            for obs_id, estimates in estimates_by_obs.items():
                if obs_id in truth_values:
                    stats = BiasVarianceStats.compute(
                        obs_id, estimates, truth_values[obs_id]
                    )
                    per_obs_stats.append(stats)

            # Aggregate statistics
            if per_obs_stats:
                biases = [s.bias for s in per_obs_stats]
                variances = [s.variance for s in per_obs_stats]
                rmses = [s.rmse for s in per_obs_stats]

                aggregate = {
                    "mean_bias": float(np.mean(biases)),
                    "max_bias": float(np.max(np.abs(biases))),
                    "mean_abs_bias": float(np.mean(np.abs(biases))),
                    "mean_variance": float(np.mean(variances)),
                    "max_variance": float(np.max(variances)),
                    "mean_rmse": float(np.mean(rmses)),
                    "max_rmse": float(np.max(rmses)),
                    "bias_std": float(np.std(biases)),
                    "n_observables": len(per_obs_stats),
                }

                # Distribution of biases
                bias_distribution = {
                    "p10": float(np.percentile(biases, 10)),
                    "p25": float(np.percentile(biases, 25)),
                    "median": float(np.median(biases)),
                    "p75": float(np.percentile(biases, 75)),
                    "p90": float(np.percentile(biases, 90)),
                }

                analysis_by_n[n] = {
                    "aggregate": aggregate,
                    "bias_distribution": bias_distribution,
                    "per_observable": [s.to_dict() for s in per_obs_stats],
                }

        # Compute overall summary
        all_biases = []
        all_variances = []
        all_rmses = []
        for n_data in analysis_by_n.values():
            for obs_data in n_data["per_observable"]:
                all_biases.append(obs_data["bias"])
                all_variances.append(obs_data["variance"])
                all_rmses.append(obs_data["rmse"])

        overall_summary = {
            "overall_mean_bias": float(np.mean(all_biases)) if all_biases else 0,
            "overall_max_bias": float(np.max(np.abs(all_biases))) if all_biases else 0,
            "overall_mean_rmse": float(np.mean(all_rmses)) if all_rmses else 0,
            "bias_decreases_with_n": self._check_bias_trend(analysis_by_n),
        }

        return TaskOutput(
            task_id=self.task_id,
            task_type=self.task_type,
            protocol_id=protocol_id,
            circuit_id=circuit_id,
            metrics=overall_summary,
            details={
                "analysis_by_n": analysis_by_n,
                "n_evaluated": sorted(results_by_n.keys()),
            },
        )

    def check_criterion(
        self,
        estimates: Estimates,
        truth_values: dict[str, float] | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """Check if bias is within acceptable bounds.

        Args:
            estimates: Protocol estimates.
            truth_values: Ground truth values.

        Returns:
            Tuple of (bias_acceptable, details).
        """
        if not truth_values:
            return False, {"error": "Truth values required"}

        max_allowed_bias = self.config.additional_params.get("max_bias", 0.01)

        biases = []
        for est in estimates.estimates:
            if est.observable_id in truth_values:
                bias = est.estimate - truth_values[est.observable_id]
                biases.append(bias)

        if not biases:
            return False, {"error": "No matching observables"}

        max_bias = max(abs(b) for b in biases)
        mean_bias = np.mean(biases)

        acceptable = max_bias <= max_allowed_bias

        return acceptable, {
            "max_bias": max_bias,
            "mean_bias": mean_bias,
            "max_allowed": max_allowed_bias,
            "n_observables": len(biases),
        }

    def _check_bias_trend(
        self,
        analysis_by_n: dict[int, dict],
    ) -> bool:
        """Check if bias decreases with increasing N.

        Returns True if bias generally decreases with N.
        """
        if len(analysis_by_n) < 2:
            return True

        sorted_ns = sorted(analysis_by_n.keys())
        biases = [
            abs(analysis_by_n[n]["aggregate"]["mean_bias"])
            for n in sorted_ns
        ]

        # Check if generally decreasing (allowing some noise)
        decreasing_count = sum(
            1 for i in range(1, len(biases)) if biases[i] <= biases[i - 1] * 1.1
        )

        return decreasing_count >= len(biases) // 2

    def compute_bias_vs_noise(
        self,
        results_by_noise: dict[str, list[LongFormRow]],
        truth_values: dict[str, float],
    ) -> dict[str, dict[str, float]]:
        """Compute bias as a function of noise level.

        Args:
            results_by_noise: Results grouped by noise profile ID.
            truth_values: Ground truth values.

        Returns:
            Dict mapping noise_profile_id to bias statistics.
        """
        bias_vs_noise = {}

        for noise_id, rows in results_by_noise.items():
            # Compute bias for each observable
            estimates_by_obs: dict[str, list[float]] = {}
            for row in rows:
                if row.observable_id not in estimates_by_obs:
                    estimates_by_obs[row.observable_id] = []
                estimates_by_obs[row.observable_id].append(row.estimate)

            biases = []
            for obs_id, estimates in estimates_by_obs.items():
                if obs_id in truth_values:
                    mean_est = np.mean(estimates)
                    bias = mean_est - truth_values[obs_id]
                    biases.append(bias)

            if biases:
                bias_vs_noise[noise_id] = {
                    "mean_bias": float(np.mean(biases)),
                    "max_bias": float(np.max(np.abs(biases))),
                    "bias_std": float(np.std(biases)),
                }

        return bias_vs_noise
