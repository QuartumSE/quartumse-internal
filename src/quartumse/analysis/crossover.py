"""Per-observable crossover analysis.

Implements Benchmarking_Improvement.md enhancement:
- Per-observable crossover points
- Identify which observables are easy/hard for each protocol
- Soft dominance (wins on X% of observables)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ..io.schemas import LongFormRow
from .interpolation import PowerLawFit, fit_power_law


@dataclass
class ObservableCrossover:
    """Crossover analysis for a single observable.

    Attributes:
        observable_id: Observable identifier
        pauli_string: Pauli string representation
        locality: Pauli weight (number of non-I)
        crossover_n: N where protocol A beats B (None if never)
        a_always_better: True if A always better
        b_always_better: True if B always better
        se_ratio_by_n: Ratio SE_A / SE_B at each N
        fit_a: Power-law fit for protocol A
        fit_b: Power-law fit for protocol B
    """

    observable_id: str
    pauli_string: str | None
    locality: int
    crossover_n: float | None
    a_always_better: bool
    b_always_better: bool
    se_ratio_by_n: dict[int, float]
    fit_a: PowerLawFit | None = None
    fit_b: PowerLawFit | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "observable_id": self.observable_id,
            "pauli_string": self.pauli_string,
            "locality": self.locality,
            "crossover_n": self.crossover_n,
            "a_always_better": self.a_always_better,
            "b_always_better": self.b_always_better,
            "se_ratio_by_n": self.se_ratio_by_n,
        }


@dataclass
class CrossoverAnalysis:
    """Complete per-observable crossover analysis.

    Attributes:
        protocol_a: Protocol A identifier (candidate)
        protocol_b: Protocol B identifier (baseline)
        metric: Metric used (se, error, etc.)
        per_observable: Per-observable crossover results
        summary: Aggregate summary statistics
    """

    protocol_a: str
    protocol_b: str
    metric: str
    per_observable: list[ObservableCrossover]
    summary: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.summary:
            self._compute_summary()

    def _compute_summary(self):
        """Compute summary statistics."""
        n_obs = len(self.per_observable)
        if n_obs == 0:
            self.summary = {"error": "No observables"}
            return

        a_wins = sum(1 for o in self.per_observable if o.a_always_better)
        b_wins = sum(1 for o in self.per_observable if o.b_always_better)
        has_crossover = sum(1 for o in self.per_observable if o.crossover_n is not None)
        crossover_ns = [o.crossover_n for o in self.per_observable if o.crossover_n is not None]

        self.summary = {
            "n_observables": n_obs,
            "a_always_wins": a_wins,
            "b_always_wins": b_wins,
            "has_crossover": has_crossover,
            "a_win_fraction": a_wins / n_obs,
            "b_win_fraction": b_wins / n_obs,
            "crossover_fraction": has_crossover / n_obs,
            "mean_crossover_n": float(np.mean(crossover_ns)) if crossover_ns else None,
            "median_crossover_n": float(np.median(crossover_ns)) if crossover_ns else None,
            "min_crossover_n": float(min(crossover_ns)) if crossover_ns else None,
            "max_crossover_n": float(max(crossover_ns)) if crossover_ns else None,
        }

    def get_easy_observables(self, for_protocol: str = "a") -> list[ObservableCrossover]:
        """Get observables that are easy for the specified protocol."""
        if for_protocol == "a":
            return [o for o in self.per_observable if o.a_always_better]
        else:
            return [o for o in self.per_observable if o.b_always_better]

    def get_hard_observables(self, for_protocol: str = "a") -> list[ObservableCrossover]:
        """Get observables that are hard for the specified protocol."""
        if for_protocol == "a":
            return [o for o in self.per_observable if o.b_always_better]
        else:
            return [o for o in self.per_observable if o.a_always_better]

    def soft_dominance(self, threshold: float = 0.9) -> dict[str, Any]:
        """Check soft dominance (wins on X% of observables).

        Args:
            threshold: Fraction required for soft dominance (default 90%)

        Returns:
            Dict with soft dominance analysis
        """
        return {
            "threshold": threshold,
            "a_soft_dominates": self.summary["a_win_fraction"] >= threshold,
            "b_soft_dominates": self.summary["b_win_fraction"] >= threshold,
            "a_win_fraction": self.summary["a_win_fraction"],
            "b_win_fraction": self.summary["b_win_fraction"],
        }

    def by_locality(self) -> dict[int, dict[str, float]]:
        """Group results by observable locality."""
        by_loc: dict[int, list[ObservableCrossover]] = {}
        for obs in self.per_observable:
            if obs.locality not in by_loc:
                by_loc[obs.locality] = []
            by_loc[obs.locality].append(obs)

        result = {}
        for loc, obs_list in sorted(by_loc.items()):
            a_wins = sum(1 for o in obs_list if o.a_always_better)
            b_wins = sum(1 for o in obs_list if o.b_always_better)
            n = len(obs_list)
            result[loc] = {
                "n_observables": n,
                "a_win_fraction": a_wins / n if n > 0 else 0,
                "b_win_fraction": b_wins / n if n > 0 else 0,
            }
        return result

    def to_dataframe(self):
        """Convert to pandas DataFrame for easy viewing."""
        import pandas as pd

        return pd.DataFrame([o.to_dict() for o in self.per_observable])


def per_observable_crossover(
    results_a: list[LongFormRow],
    results_b: list[LongFormRow],
    metric: str = "se",
    interpolate: bool = True,
) -> CrossoverAnalysis:
    """Compute per-observable crossover analysis.

    For each observable, finds at what N protocol A beats protocol B.

    Args:
        results_a: Long-form results from protocol A
        results_b: Long-form results from protocol B
        metric: "se" or "error"
        interpolate: Whether to interpolate crossover using power-law

    Returns:
        CrossoverAnalysis with per-observable results
    """
    protocol_a = results_a[0].protocol_id if results_a else "unknown"
    protocol_b = results_b[0].protocol_id if results_b else "unknown"

    # Group by observable and N
    def group_by_obs_n(rows: list[LongFormRow]) -> dict[str, dict[int, list[float]]]:
        result: dict[str, dict[int, list[float]]] = {}
        for row in rows:
            obs_id = row.observable_id
            n = row.N_total
            if obs_id not in result:
                result[obs_id] = {}
            if n not in result[obs_id]:
                result[obs_id][n] = []

            if metric == "se":
                result[obs_id][n].append(row.se)
            else:
                # Would need truth values for error
                result[obs_id][n].append(row.se)  # Fallback to SE

        return result

    grouped_a = group_by_obs_n(results_a)
    grouped_b = group_by_obs_n(results_b)

    # Get Pauli strings from results
    pauli_strings = {}
    for row in results_a + results_b:
        if hasattr(row, "pauli_string") and row.pauli_string:
            pauli_strings[row.observable_id] = row.pauli_string

    common_obs = set(grouped_a.keys()) & set(grouped_b.keys())

    per_obs_results = []

    for obs_id in sorted(common_obs):
        data_a = grouped_a[obs_id]
        data_b = grouped_b[obs_id]
        common_ns = sorted(set(data_a.keys()) & set(data_b.keys()))

        if not common_ns:
            continue

        # Compute mean metric at each N
        mean_a = {n: np.mean(data_a[n]) for n in common_ns}
        mean_b = {n: np.mean(data_b[n]) for n in common_ns}

        # Compute SE ratio
        se_ratio = {n: mean_a[n] / mean_b[n] if mean_b[n] > 0 else float("inf") for n in common_ns}

        # Determine crossover
        a_better_at = [n for n in common_ns if mean_a[n] < mean_b[n]]
        b_better_at = [n for n in common_ns if mean_b[n] < mean_a[n]]

        a_always_better = len(b_better_at) == 0 and len(a_better_at) > 0
        b_always_better = len(a_better_at) == 0 and len(b_better_at) > 0

        crossover_n = None

        # Find crossover point
        if a_better_at and b_better_at:
            # There's a crossover somewhere
            for i in range(len(common_ns) - 1):
                n1, n2 = common_ns[i], common_ns[i + 1]
                # A was worse, now better
                if mean_a[n1] >= mean_b[n1] and mean_a[n2] < mean_b[n2]:
                    if interpolate:
                        # Linear interpolation
                        ratio1 = mean_a[n1] / mean_b[n1] if mean_b[n1] > 0 else float("inf")
                        ratio2 = mean_a[n2] / mean_b[n2] if mean_b[n2] > 0 else float("inf")
                        denom = ratio2 - ratio1
                        # Check for valid interpolation (finite denominator, not too small)
                        if np.isfinite(ratio1) and np.isfinite(ratio2) and abs(denom) > 1e-12:
                            frac = (1 - ratio1) / denom
                            crossover_n = n1 + frac * (n2 - n1)
                        else:
                            # Fallback to midpoint if interpolation not possible
                            crossover_n = (n1 + n2) / 2
                    else:
                        crossover_n = n2
                    break

        # Get Pauli string and locality
        pauli = pauli_strings.get(obs_id, None)
        locality = sum(1 for c in pauli if c != "I") if pauli else 0

        # Fit power laws if interpolating
        fit_a = None
        fit_b = None
        if interpolate and len(common_ns) >= 3:
            fit_a = fit_power_law(common_ns, [mean_a[n] for n in common_ns])
            fit_b = fit_power_law(common_ns, [mean_b[n] for n in common_ns])

        per_obs_results.append(
            ObservableCrossover(
                observable_id=obs_id,
                pauli_string=pauli,
                locality=locality,
                crossover_n=crossover_n,
                a_always_better=a_always_better,
                b_always_better=b_always_better,
                se_ratio_by_n=se_ratio,
                fit_a=fit_a,
                fit_b=fit_b,
            )
        )

    return CrossoverAnalysis(
        protocol_a=protocol_a,
        protocol_b=protocol_b,
        metric=metric,
        per_observable=per_obs_results,
    )
