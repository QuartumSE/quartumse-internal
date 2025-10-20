"""
Key QuartumSE metrics: SSR and RMSE@$.

These metrics quantify cost-for-accuracy improvements.
"""

import numpy as np
from typing import Optional


def compute_ssr(
    baseline_shots: int,
    quartumse_shots: int,
    baseline_precision: Optional[float] = None,
    quartumse_precision: Optional[float] = None,
) -> float:
    """
    Compute Shot-Savings Ratio (SSR).

    SSR = baseline_shots / quartumse_shots (at equal precision)

    If precisions differ, normalize by variance ratio.

    Args:
        baseline_shots: Shots used by baseline method
        quartumse_shots: Shots used by QuartumSE
        baseline_precision: Optional precision (variance or CI width)
        quartumse_precision: Optional QuartumSE precision

    Returns:
        SSR value (>1 means QuartumSE saves shots)
    """
    if baseline_precision is not None and quartumse_precision is not None:
        # Normalize by precision ratio (variance scales as 1/shots)
        precision_ratio = (baseline_precision / quartumse_precision) ** 2
        return (baseline_shots / quartumse_shots) * precision_ratio
    else:
        return baseline_shots / quartumse_shots


def compute_rmse_at_cost(
    rmse: float,
    cost_usd: float,
) -> float:
    """
    Compute RMSE@$ metric.

    This is the cost (in dollars) to achieve a given RMSE.

    Args:
        rmse: Root mean squared error achieved
        cost_usd: Cost in USD for the experiment

    Returns:
        Cost per unit RMSE (lower is better)
    """
    return cost_usd / rmse if rmse > 0 else float("inf")


def estimate_gate_error_rate(backend_properties: dict) -> dict:
    """
    Extract gate error rates from backend properties.

    Returns dict of gate -> error rate.
    """
    # TODO: Parse backend properties
    return {}
