"""Summary table aggregation (Measurements Bible §10.3).

This module provides utilities for computing summary statistics from
long-form results. The summary table aggregates across observables and
replicates for each (protocol, circuit, N) combination.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .long_form import LongFormResultSet
from .schemas import LongFormRow, SummaryRow


def compute_percentile(values: list[float], percentile: float) -> float:
    """Compute percentile of a list of values.

    Args:
        values: List of numeric values.
        percentile: Percentile to compute (0-100).

    Returns:
        Percentile value.
    """
    if not values:
        return 0.0
    return float(np.percentile(values, percentile))


def compute_rmse(errors: list[float]) -> float:
    """Compute root mean squared error.

    Args:
        errors: List of squared errors.

    Returns:
        RMSE value.
    """
    if not errors:
        return 0.0
    return float(np.sqrt(np.mean(errors)))


class SummaryAggregator:
    """Aggregator for computing summary statistics from long-form results.

    Example:
        aggregator = SummaryAggregator(result_set)
        summary_rows = aggregator.compute_summaries()
    """

    def __init__(
        self,
        result_set: LongFormResultSet,
        epsilon: float | None = None,
    ) -> None:
        """Initialize aggregator.

        Args:
            result_set: Collection of LongFormRow objects.
            epsilon: Target precision for attainment computation.
        """
        self.result_set = result_set
        self.epsilon = epsilon

    def compute_summaries(self) -> list[SummaryRow]:
        """Compute summary rows for all (protocol, circuit, N) combinations.

        Returns:
            List of SummaryRow objects.
        """
        if len(self.result_set) == 0:
            return []

        # Group by (protocol, circuit, N_total, noise_profile)
        groups: dict[tuple[str, str, int, str], list[LongFormRow]] = {}

        for row in self.result_set:
            key = (row.protocol_id, row.circuit_id, row.N_total, row.noise_profile_id)
            if key not in groups:
                groups[key] = []
            groups[key].append(row)

        # Compute summary for each group
        summaries = []
        for (protocol_id, circuit_id, N_total, noise_profile_id), rows in groups.items():
            summary = self._compute_group_summary(
                rows=rows,
                protocol_id=protocol_id,
                circuit_id=circuit_id,
                N_total=N_total,
                noise_profile_id=noise_profile_id,
            )
            summaries.append(summary)

        return summaries

    def _compute_group_summary(
        self,
        rows: list[LongFormRow],
        protocol_id: str,
        circuit_id: str,
        N_total: int,
        noise_profile_id: str,
    ) -> SummaryRow:
        """Compute summary for a single (protocol, circuit, N) group.

        Args:
            rows: Rows in this group.
            protocol_id: Protocol identifier.
            circuit_id: Circuit identifier.
            N_total: Total shots.
            noise_profile_id: Noise profile identifier.

        Returns:
            SummaryRow with aggregated statistics.
        """
        run_id = rows[0].run_id

        # Count unique observables and replicates
        observable_ids = set(row.observable_id for row in rows)
        replicate_ids = set(row.replicate_id for row in rows)

        n_observables = len(observable_ids)
        n_replicates = len(replicate_ids)

        # Collect SE values
        se_values = [row.se for row in rows]

        # SE statistics
        se_mean = float(np.mean(se_values))
        se_median = float(np.median(se_values))
        se_p90 = compute_percentile(se_values, 90)
        se_p95 = compute_percentile(se_values, 95)
        se_max = float(np.max(se_values))

        # Error statistics (if truth available)
        abs_err_mean = None
        abs_err_median = None
        abs_err_p90 = None
        abs_err_p95 = None
        abs_err_max = None
        rmse = None

        abs_errors = [row.abs_err for row in rows if row.abs_err is not None]
        sq_errors = [row.sq_err for row in rows if row.sq_err is not None]

        if abs_errors:
            abs_err_mean = float(np.mean(abs_errors))
            abs_err_median = float(np.median(abs_errors))
            abs_err_p90 = compute_percentile(abs_errors, 90)
            abs_err_p95 = compute_percentile(abs_errors, 95)
            abs_err_max = float(np.max(abs_errors))

        if sq_errors:
            rmse = compute_rmse(sq_errors)

        # Attainment (if epsilon specified)
        attainment_epsilon = None
        attainment_fraction = None

        if self.epsilon is not None:
            attainment_epsilon = self.epsilon
            attained = sum(1 for se in se_values if se <= self.epsilon)
            attainment_fraction = attained / len(se_values)

        # Coverage (if CIs available)
        coverage_per_observable = None
        coverage_family_wise = None

        rows_with_ci = [
            row
            for row in rows
            if row.ci_low is not None
            and row.ci_high is not None
            and row.truth_value is not None
        ]

        if rows_with_ci:
            # Per-observable coverage: fraction of CIs that contain truth
            covered = sum(
                1
                for row in rows_with_ci
                if row.ci_low <= row.truth_value <= row.ci_high
            )
            coverage_per_observable = covered / len(rows_with_ci)

            # Family-wise coverage: for each replicate, check if ALL CIs contain truth
            replicate_coverage = {}
            for row in rows_with_ci:
                if row.replicate_id not in replicate_coverage:
                    replicate_coverage[row.replicate_id] = []
                replicate_coverage[row.replicate_id].append(
                    row.ci_low <= row.truth_value <= row.ci_high
                )

            # Family-wise: fraction of replicates where all CIs contain truth
            family_covered = sum(
                1 for covers in replicate_coverage.values() if all(covers)
            )
            coverage_family_wise = family_covered / len(replicate_coverage)

        # Resource totals
        quantum_times = [row.time_quantum_s for row in rows if row.time_quantum_s is not None]
        classical_times = [row.time_classical_s for row in rows if row.time_classical_s is not None]

        total_quantum_time_s = sum(quantum_times) if quantum_times else None
        total_classical_time_s = sum(classical_times) if classical_times else None

        return SummaryRow(
            run_id=run_id,
            circuit_id=circuit_id,
            protocol_id=protocol_id,
            N_total=N_total,
            noise_profile_id=noise_profile_id,
            n_observables=n_observables,
            n_replicates=n_replicates,
            se_mean=se_mean,
            se_median=se_median,
            se_p90=se_p90,
            se_p95=se_p95,
            se_max=se_max,
            abs_err_mean=abs_err_mean,
            abs_err_median=abs_err_median,
            abs_err_p90=abs_err_p90,
            abs_err_p95=abs_err_p95,
            abs_err_max=abs_err_max,
            rmse=rmse,
            attainment_epsilon=attainment_epsilon,
            attainment_fraction=attainment_fraction,
            coverage_per_observable=coverage_per_observable,
            coverage_family_wise=coverage_family_wise,
            total_quantum_time_s=total_quantum_time_s,
            total_classical_time_s=total_classical_time_s,
        )


def compute_shot_savings_factor(
    summary_rows: list[SummaryRow],
    protocol_id: str,
    baseline_protocol_id: str,
    metric: str = "se_median",
) -> dict[str, float]:
    """Compute shot-savings factor (SSF) relative to a baseline.

    SSF = N_baseline / N_protocol at iso-precision.

    Args:
        summary_rows: List of summary rows.
        protocol_id: Protocol to compute SSF for.
        baseline_protocol_id: Baseline protocol for comparison.
        metric: Metric to use for precision comparison.

    Returns:
        Dict mapping circuit_id to SSF value.
    """
    # Group by circuit
    protocol_data: dict[str, list[SummaryRow]] = {}
    baseline_data: dict[str, list[SummaryRow]] = {}

    for row in summary_rows:
        if row.protocol_id == protocol_id:
            if row.circuit_id not in protocol_data:
                protocol_data[row.circuit_id] = []
            protocol_data[row.circuit_id].append(row)
        elif row.protocol_id == baseline_protocol_id:
            if row.circuit_id not in baseline_data:
                baseline_data[row.circuit_id] = []
            baseline_data[row.circuit_id].append(row)

    ssf_results = {}

    for circuit_id in protocol_data:
        if circuit_id not in baseline_data:
            continue

        # Get metric values by N
        protocol_by_N = {row.N_total: getattr(row, metric) for row in protocol_data[circuit_id]}
        baseline_by_N = {row.N_total: getattr(row, metric) for row in baseline_data[circuit_id]}

        # Find matching precision points
        # For each protocol N, find baseline N that gives same precision
        protocol_Ns = sorted(protocol_by_N.keys())
        baseline_Ns = sorted(baseline_by_N.keys())

        if not protocol_Ns or not baseline_Ns:
            continue

        # Use median N point for protocol
        protocol_N = protocol_Ns[len(protocol_Ns) // 2]
        target_precision = protocol_by_N[protocol_N]

        # Find baseline N that achieves similar precision (interpolate)
        baseline_N_for_precision = _interpolate_N_for_precision(
            baseline_by_N, target_precision
        )

        if baseline_N_for_precision is not None:
            ssf_results[circuit_id] = baseline_N_for_precision / protocol_N

    return ssf_results


def _interpolate_N_for_precision(
    N_to_precision: dict[int, float],
    target_precision: float,
) -> float | None:
    """Interpolate to find N that achieves target precision.

    Args:
        N_to_precision: Mapping from N to precision metric.
        target_precision: Target precision value.

    Returns:
        Interpolated N value, or None if out of range.
    """
    sorted_items = sorted(N_to_precision.items())
    Ns = [n for n, _ in sorted_items]
    precisions = [p for _, p in sorted_items]

    # Precision typically decreases with N
    # Find bracketing points
    for i in range(len(precisions) - 1):
        if (precisions[i] >= target_precision >= precisions[i + 1]) or (
            precisions[i] <= target_precision <= precisions[i + 1]
        ):
            # Linear interpolation
            frac = (target_precision - precisions[i]) / (precisions[i + 1] - precisions[i])
            return Ns[i] + frac * (Ns[i + 1] - Ns[i])

    # Extrapolate if precision is better than all points
    if target_precision < min(precisions):
        # Need fewer shots - extrapolate down
        return None  # Can't determine

    # Need more shots than available
    return None


def compute_crossover_point(
    summary_rows: list[SummaryRow],
    protocol_a: str,
    protocol_b: str,
    circuit_id: str,
    metric: str = "se_median",
) -> int | None:
    """Find N where protocol_a becomes better than protocol_b.

    Args:
        summary_rows: List of summary rows.
        protocol_a: First protocol.
        protocol_b: Second protocol.
        circuit_id: Circuit to analyze.
        metric: Metric to compare.

    Returns:
        Crossover N value, or None if no crossover found.
    """
    a_data = {
        row.N_total: getattr(row, metric)
        for row in summary_rows
        if row.protocol_id == protocol_a and row.circuit_id == circuit_id
    }
    b_data = {
        row.N_total: getattr(row, metric)
        for row in summary_rows
        if row.protocol_id == protocol_b and row.circuit_id == circuit_id
    }

    common_Ns = sorted(set(a_data.keys()) & set(b_data.keys()))

    if not common_Ns:
        return None

    # Find where a becomes better (lower metric) than b
    for i, N in enumerate(common_Ns):
        if a_data[N] < b_data[N]:
            if i == 0:
                return N  # Already better at smallest N
            # Crossover happened between previous N and this N
            return common_Ns[i - 1]

    return None  # No crossover found
