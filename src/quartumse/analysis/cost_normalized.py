"""Cost-normalized benchmark comparisons.

Implements Benchmarking_Improvement.md enhancement:
- Account for circuit depth overhead in comparisons
- Penalize protocols with deeper circuits (more noise sensitivity)
- Compare error / effective_cost, not just error / shots
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import numpy as np

from ..io.schemas import LongFormRow


@dataclass
class CostModel:
    """Model for computing effective cost of measurements.

    Cost factors:
    - shots: Base cost (number of circuit executions)
    - depth_penalty: Multiplier per unit circuit depth
    - gate_penalty: Multiplier per 2-qubit gate
    - noise_factor: Additional noise-based multiplier

    Effective cost = shots * (1 + depth_penalty * depth) * (1 + gate_penalty * gates) * noise_factor
    """
    depth_penalty: float = 0.01  # 1% per depth unit
    gate_penalty: float = 0.005  # 0.5% per 2-qubit gate
    noise_factor: float = 1.0
    include_classical_time: bool = False
    classical_time_weight: float = 0.001  # Weight for classical compute time

    def compute_cost(
        self,
        n_shots: int,
        circuit_depth: int = 0,
        twoq_gates: int = 0,
        classical_time_s: float = 0.0,
    ) -> float:
        """Compute effective cost for a measurement configuration.

        Args:
            n_shots: Number of shots
            circuit_depth: Circuit depth
            twoq_gates: Number of 2-qubit gates
            classical_time_s: Classical processing time in seconds

        Returns:
            Effective cost value
        """
        base_cost = n_shots
        depth_mult = 1 + self.depth_penalty * circuit_depth
        gate_mult = 1 + self.gate_penalty * twoq_gates

        cost = base_cost * depth_mult * gate_mult * self.noise_factor

        if self.include_classical_time:
            cost += self.classical_time_weight * classical_time_s

        return cost

    def to_dict(self) -> dict[str, float]:
        return {
            "depth_penalty": self.depth_penalty,
            "gate_penalty": self.gate_penalty,
            "noise_factor": self.noise_factor,
            "include_classical_time": self.include_classical_time,
            "classical_time_weight": self.classical_time_weight,
        }


@dataclass
class CostNormalizedResult:
    """Result of cost-normalized analysis for a protocol.

    Attributes:
        protocol_id: Protocol identifier
        n_total: Shot budget
        raw_metrics: Original metrics (SE, error)
        cost: Effective cost
        cost_normalized_se: SE / sqrt(effective_cost)
        cost_normalized_error: Error / sqrt(effective_cost)
        circuit_depth: Mean circuit depth
        twoq_gates: Mean 2-qubit gate count
    """
    protocol_id: str
    n_total: int
    raw_metrics: dict[str, float]
    cost: float
    cost_normalized_se: float
    cost_normalized_error: float | None
    circuit_depth: float
    twoq_gates: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_id": self.protocol_id,
            "n_total": self.n_total,
            "raw_metrics": self.raw_metrics,
            "cost": self.cost,
            "cost_normalized_se": self.cost_normalized_se,
            "cost_normalized_error": self.cost_normalized_error,
            "circuit_depth": self.circuit_depth,
            "twoq_gates": self.twoq_gates,
        }


def compute_cost_normalized_metrics(
    long_form_results: list[LongFormRow],
    cost_model: CostModel | None = None,
    truth_values: dict[str, float] | None = None,
) -> dict[str, dict[int, CostNormalizedResult]]:
    """Compute cost-normalized metrics for all protocols.

    Args:
        long_form_results: Long-form benchmark results
        cost_model: Cost model to use (default: CostModel())
        truth_values: Ground truth for error computation

    Returns:
        Dict: protocol_id -> {N -> CostNormalizedResult}
    """
    if cost_model is None:
        cost_model = CostModel()

    # Group by protocol and N
    by_protocol_n: dict[str, dict[int, list[LongFormRow]]] = defaultdict(lambda: defaultdict(list))
    for row in long_form_results:
        by_protocol_n[row.protocol_id][row.N_total].append(row)

    results: dict[str, dict[int, CostNormalizedResult]] = {}

    for protocol_id, by_n in by_protocol_n.items():
        results[protocol_id] = {}

        for n, rows in by_n.items():
            # Compute means
            se_values = [r.se for r in rows]
            mean_se = float(np.mean(se_values))

            # Circuit metrics (may not be available for all rows)
            depths = [r.circuit_depth for r in rows if hasattr(r, 'circuit_depth') and r.circuit_depth]
            gates = [r.twoq_gate_count for r in rows if hasattr(r, 'twoq_gate_count') and r.twoq_gate_count]
            times = [r.time_classical_s for r in rows if hasattr(r, 'time_classical_s') and r.time_classical_s]

            mean_depth = float(np.mean(depths)) if depths else 0.0
            mean_gates = float(np.mean(gates)) if gates else 0.0
            mean_time = float(np.mean(times)) if times else 0.0

            # Compute cost
            cost = cost_model.compute_cost(
                n_shots=n,
                circuit_depth=int(mean_depth),
                twoq_gates=int(mean_gates),
                classical_time_s=mean_time,
            )

            # Cost-normalized SE (SE scales as 1/sqrt(N), so normalize by sqrt(cost))
            cost_normalized_se = mean_se * np.sqrt(cost) / np.sqrt(n) if n > 0 else float('inf')

            # Error if truth available
            cost_normalized_error = None
            if truth_values:
                errors = []
                for row in rows:
                    if row.observable_id in truth_values:
                        errors.append(abs(row.estimate - truth_values[row.observable_id]))
                if errors:
                    mean_error = float(np.mean(errors))
                    cost_normalized_error = mean_error * np.sqrt(cost) / np.sqrt(n) if n > 0 else float('inf')

            results[protocol_id][n] = CostNormalizedResult(
                protocol_id=protocol_id,
                n_total=n,
                raw_metrics={
                    "mean_se": mean_se,
                    "median_se": float(np.median(se_values)),
                    "max_se": float(np.max(se_values)),
                },
                cost=cost,
                cost_normalized_se=cost_normalized_se,
                cost_normalized_error=cost_normalized_error,
                circuit_depth=mean_depth,
                twoq_gates=mean_gates,
            )

    return results


def compare_cost_normalized(
    results: dict[str, dict[int, CostNormalizedResult]],
    n_total: int,
) -> dict[str, Any]:
    """Compare protocols at specific N using cost-normalized metrics.

    Args:
        results: Output from compute_cost_normalized_metrics
        n_total: Shot budget to compare

    Returns:
        Comparison results
    """
    comparison = []

    for protocol_id, by_n in results.items():
        if n_total in by_n:
            result = by_n[n_total]
            comparison.append({
                "protocol_id": protocol_id,
                "raw_se": result.raw_metrics["mean_se"],
                "cost": result.cost,
                "cost_normalized_se": result.cost_normalized_se,
                "circuit_depth": result.circuit_depth,
                "twoq_gates": result.twoq_gates,
            })

    # Sort by cost-normalized SE
    comparison.sort(key=lambda x: x["cost_normalized_se"])

    # Determine winner
    if comparison:
        winner_raw = min(comparison, key=lambda x: x["raw_se"])["protocol_id"]
        winner_cost = comparison[0]["protocol_id"]

        return {
            "n_total": n_total,
            "protocols": comparison,
            "winner_raw_se": winner_raw,
            "winner_cost_normalized": winner_cost,
            "ranking_changed": winner_raw != winner_cost,
        }

    return {"error": "No results at specified N"}


def compute_cost_efficiency_curve(
    results: dict[str, dict[int, CostNormalizedResult]],
) -> dict[str, list[dict[str, float]]]:
    """Compute cost-efficiency curves for Pareto analysis.

    Args:
        results: Output from compute_cost_normalized_metrics

    Returns:
        Dict: protocol_id -> list of (cost, se) points
    """
    curves = {}

    for protocol_id, by_n in results.items():
        points = []
        for n, result in sorted(by_n.items()):
            points.append({
                "n_total": n,
                "cost": result.cost,
                "se": result.raw_metrics["mean_se"],
                "cost_normalized_se": result.cost_normalized_se,
            })
        curves[protocol_id] = points

    return curves


def find_pareto_frontier(
    curves: dict[str, list[dict[str, float]]],
) -> list[dict[str, Any]]:
    """Find Pareto-optimal points across all protocols.

    A point is Pareto-optimal if no other point has both lower cost AND lower SE.

    Args:
        curves: Output from compute_cost_efficiency_curve

    Returns:
        List of Pareto-optimal points with protocol attribution
    """
    # Collect all points
    all_points = []
    for protocol_id, points in curves.items():
        for point in points:
            all_points.append({
                "protocol_id": protocol_id,
                "cost": point["cost"],
                "se": point["se"],
                "n_total": point["n_total"],
            })

    # Find Pareto frontier
    pareto = []
    for point in all_points:
        dominated = False
        for other in all_points:
            if other["cost"] < point["cost"] and other["se"] < point["se"]:
                dominated = True
                break
        if not dominated:
            pareto.append(point)

    # Sort by cost
    pareto.sort(key=lambda x: x["cost"])

    return pareto
