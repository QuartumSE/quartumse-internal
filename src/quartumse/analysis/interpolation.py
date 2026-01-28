"""N* interpolation with power-law fitting.

Implements Benchmarking_Improvement.md enhancement:
- Fit power-law (SE ∝ N^{-0.5}) to avoid grid quantization
- Interpolate N* between grid points
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import curve_fit


@dataclass
class PowerLawFit:
    """Result of power-law fitting.

    Attributes:
        amplitude: Coefficient 'a' in SE = a * N^{exponent}
        exponent: Power-law exponent (should be ~-0.5 for SE)
        r_squared: Goodness of fit
        n_points: Number of data points used
        ns: Shot budgets used for fitting
        observed: Observed SE values
        predicted: Predicted SE values from fit
    """
    amplitude: float
    exponent: float
    r_squared: float
    n_points: int
    ns: list[int]
    observed: list[float]
    predicted: list[float]

    def predict(self, n: float) -> float:
        """Predict SE at shot budget n."""
        return self.amplitude * (n ** self.exponent)

    def to_dict(self) -> dict[str, Any]:
        return {
            "amplitude": self.amplitude,
            "exponent": self.exponent,
            "r_squared": self.r_squared,
            "n_points": self.n_points,
        }


def _power_law(n: np.ndarray, a: float, b: float) -> np.ndarray:
    """Power law function: SE = a * N^b"""
    return a * np.power(n.astype(float), b)


def fit_power_law(
    ns: list[int],
    se_values: list[float],
    initial_exponent: float = -0.5,
) -> PowerLawFit:
    """Fit power law SE = a * N^b to data.

    Args:
        ns: Shot budgets
        se_values: Corresponding SE values
        initial_exponent: Initial guess for exponent (default -0.5)

    Returns:
        PowerLawFit with fitted parameters
    """
    ns_arr = np.array(ns, dtype=float)
    se_arr = np.array(se_values, dtype=float)

    # Filter out invalid values
    valid = (ns_arr > 0) & (se_arr > 0) & np.isfinite(se_arr)
    ns_arr = ns_arr[valid]
    se_arr = se_arr[valid]

    if len(ns_arr) < 2:
        return PowerLawFit(
            amplitude=np.nan,
            exponent=np.nan,
            r_squared=0.0,
            n_points=len(ns_arr),
            ns=list(ns_arr.astype(int)),
            observed=list(se_arr),
            predicted=[],
        )

    # Initial guess: a = SE[0] * N[0]^0.5, b = -0.5
    a_init = se_arr[0] * np.sqrt(ns_arr[0])

    try:
        popt, _ = curve_fit(
            _power_law,
            ns_arr,
            se_arr,
            p0=[a_init, initial_exponent],
            bounds=([0, -2], [np.inf, 0]),
            maxfev=5000,
        )
        a, b = popt

        # Compute R²
        predicted = _power_law(ns_arr, a, b)
        ss_res = np.sum((se_arr - predicted) ** 2)
        ss_tot = np.sum((se_arr - np.mean(se_arr)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    except (RuntimeError, ValueError):
        # Fallback: assume exponent = -0.5 and fit amplitude only
        # SE = a / sqrt(N) => a = SE * sqrt(N)
        a = np.mean(se_arr * np.sqrt(ns_arr))
        b = -0.5
        predicted = _power_law(ns_arr, a, b)
        ss_res = np.sum((se_arr - predicted) ** 2)
        ss_tot = np.sum((se_arr - np.mean(se_arr)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    return PowerLawFit(
        amplitude=float(a),
        exponent=float(b),
        r_squared=float(r_squared),
        n_points=len(ns_arr),
        ns=list(ns_arr.astype(int)),
        observed=list(se_arr),
        predicted=list(predicted),
    )


def interpolate_n_star(
    ns: list[int],
    se_values: list[float],
    epsilon: float,
    method: str = "power_law",
) -> tuple[float | None, PowerLawFit | None]:
    """Interpolate N* (shots-to-target) using power-law fit.

    Instead of grid search, fits SE ∝ N^{-0.5} and solves for N* analytically.

    Args:
        ns: Shot budgets
        se_values: Corresponding SE values (mean or max)
        epsilon: Target SE threshold
        method: "power_law" or "linear" interpolation

    Returns:
        Tuple of (interpolated N*, PowerLawFit object or None)
    """
    if method == "power_law":
        fit = fit_power_law(ns, se_values)

        if np.isnan(fit.amplitude) or np.isnan(fit.exponent):
            return None, fit

        # Solve: epsilon = a * N^b => N = (epsilon / a)^(1/b)
        if fit.exponent >= 0:
            return None, fit

        n_star = (epsilon / fit.amplitude) ** (1 / fit.exponent)

        # Sanity check
        if n_star < 0 or not np.isfinite(n_star):
            return None, fit

        return float(n_star), fit

    elif method == "linear":
        # Linear interpolation between grid points
        ns_arr = np.array(ns)
        se_arr = np.array(se_values)

        # Sort by N
        order = np.argsort(ns_arr)
        ns_arr = ns_arr[order]
        se_arr = se_arr[order]

        # Find where SE crosses epsilon
        for i in range(len(ns_arr) - 1):
            if se_arr[i] > epsilon >= se_arr[i + 1]:
                # Handle case where consecutive SE values are equal (avoid division by zero)
                denom = se_arr[i] - se_arr[i + 1]
                if abs(denom) < 1e-12:
                    # SE values are effectively equal - return the lower N
                    n_star = float(ns_arr[i])
                else:
                    # Linear interpolation
                    frac = (se_arr[i] - epsilon) / denom
                    n_star = ns_arr[i] + frac * (ns_arr[i + 1] - ns_arr[i])
                return float(n_star), None

        # Check if already below threshold
        if se_arr[-1] <= epsilon:
            return float(ns_arr[-1]), None

        return None, None

    else:
        raise ValueError(f"Unknown method: {method}")


def compute_percentile_n_star(
    results_by_n: dict[int, list[float]],
    epsilon: float,
    percentile: float = 95,
) -> tuple[int | None, dict[int, float]]:
    """Compute N* using percentile instead of max.

    More robust than strict max (Benchmarking_Improvement.md enhancement).

    Args:
        results_by_n: Dict mapping N to list of SE values
        epsilon: Target threshold
        percentile: Percentile to use (default 95)

    Returns:
        Tuple of (N* or None, dict of percentile values by N)
    """
    percentile_by_n = {}

    for n in sorted(results_by_n.keys()):
        se_values = results_by_n[n]
        if se_values:
            percentile_by_n[n] = float(np.percentile(se_values, percentile))

    # Find N* where percentile meets threshold
    for n in sorted(percentile_by_n.keys()):
        if percentile_by_n[n] <= epsilon:
            return n, percentile_by_n

    return None, percentile_by_n
