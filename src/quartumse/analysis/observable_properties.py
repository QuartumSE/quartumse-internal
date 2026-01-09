"""Observable property analysis.

Implements Benchmarking_Improvement.md enhancement:
- Analyze performance as function of observable properties
- Locality (Pauli weight) correlation
- Commutation structure analysis
- Coefficient magnitude effects
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from collections import defaultdict

import numpy as np

from ..io.schemas import LongFormRow


@dataclass
class LocalityGroup:
    """Statistics for a group of observables with same locality.

    Attributes:
        locality: Pauli weight (number of non-I operators)
        n_observables: Number of observables in group
        observable_ids: IDs of observables in group
        mean_se: Mean SE across observables
        median_se: Median SE
        std_se: Standard deviation of SE
        min_se: Minimum SE
        max_se: Maximum SE
        theoretical_variance_factor: 3^locality for shadows
    """
    locality: int
    n_observables: int
    observable_ids: list[str]
    mean_se: float
    median_se: float
    std_se: float
    min_se: float
    max_se: float
    theoretical_variance_factor: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "locality": self.locality,
            "n_observables": self.n_observables,
            "mean_se": self.mean_se,
            "median_se": self.median_se,
            "std_se": self.std_se,
            "min_se": self.min_se,
            "max_se": self.max_se,
            "theoretical_variance_factor": self.theoretical_variance_factor,
        }


@dataclass
class PropertyAnalysis:
    """Complete observable property analysis.

    Attributes:
        protocol_id: Protocol analyzed
        n_total: Shot budget for analysis
        by_locality: Results grouped by Pauli weight
        locality_correlation: Correlation between locality and SE
        locality_regression: Linear regression coefficients
    """
    protocol_id: str
    n_total: int
    by_locality: dict[int, LocalityGroup]
    locality_correlation: float
    locality_regression: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_id": self.protocol_id,
            "n_total": self.n_total,
            "by_locality": {k: v.to_dict() for k, v in self.by_locality.items()},
            "locality_correlation": self.locality_correlation,
            "locality_regression": self.locality_regression,
        }

    def to_dataframe(self):
        """Convert to pandas DataFrame."""
        import pandas as pd
        rows = []
        for loc, group in sorted(self.by_locality.items()):
            row = group.to_dict()
            rows.append(row)
        return pd.DataFrame(rows)


def _get_pauli_weight(pauli_string: str) -> int:
    """Compute Pauli weight (number of non-identity operators)."""
    return sum(1 for c in pauli_string if c != 'I')


def _extract_locality_from_rows(rows: list[LongFormRow]) -> dict[str, int]:
    """Extract locality for each observable from rows."""
    locality_map = {}
    for row in rows:
        if row.observable_id not in locality_map:
            # Try to get from pauli_string if available
            if hasattr(row, 'pauli_string') and row.pauli_string:
                locality_map[row.observable_id] = _get_pauli_weight(row.pauli_string)
            else:
                # Default to 0 if unknown
                locality_map[row.observable_id] = 0
    return locality_map


def analyze_by_locality(
    long_form_results: list[LongFormRow],
    n_total: int | None = None,
    locality_map: dict[str, int] | None = None,
) -> dict[str, PropertyAnalysis]:
    """Analyze protocol performance grouped by observable locality.

    Args:
        long_form_results: Long-form benchmark results
        n_total: Specific shot budget to analyze (None = use max)
        locality_map: Map observable_id -> locality (auto-extracted if None)

    Returns:
        Dict mapping protocol_id to PropertyAnalysis
    """
    if not long_form_results:
        return {}

    # Extract locality if not provided
    if locality_map is None:
        locality_map = _extract_locality_from_rows(long_form_results)

    # Group by protocol
    by_protocol: dict[str, list[LongFormRow]] = defaultdict(list)
    for row in long_form_results:
        by_protocol[row.protocol_id].append(row)

    # Determine N to analyze
    if n_total is None:
        n_total = max(row.N_total for row in long_form_results)

    results = {}

    for protocol_id, rows in by_protocol.items():
        # Filter to specific N
        rows_at_n = [r for r in rows if r.N_total == n_total]
        if not rows_at_n:
            continue

        # Group by locality
        by_locality: dict[int, list[LongFormRow]] = defaultdict(list)
        for row in rows_at_n:
            locality = locality_map.get(row.observable_id, 0)
            by_locality[locality].append(row)

        # Compute statistics per locality group
        locality_groups = {}
        all_localities = []
        all_ses = []

        for locality, loc_rows in sorted(by_locality.items()):
            se_values = [r.se for r in loc_rows]
            obs_ids = list(set(r.observable_id for r in loc_rows))

            locality_groups[locality] = LocalityGroup(
                locality=locality,
                n_observables=len(obs_ids),
                observable_ids=obs_ids,
                mean_se=float(np.mean(se_values)),
                median_se=float(np.median(se_values)),
                std_se=float(np.std(se_values)) if len(se_values) > 1 else 0.0,
                min_se=float(np.min(se_values)),
                max_se=float(np.max(se_values)),
                theoretical_variance_factor=3 ** locality,
            )

            # Collect for correlation
            for se in se_values:
                all_localities.append(locality)
                all_ses.append(se)

        # Compute correlation between locality and SE
        if len(all_localities) > 1 and len(set(all_localities)) > 1:
            correlation = float(np.corrcoef(all_localities, all_ses)[0, 1])

            # Linear regression: SE = a + b * locality
            X = np.array(all_localities)
            y = np.array(all_ses)
            X_mean = np.mean(X)
            y_mean = np.mean(y)
            b = np.sum((X - X_mean) * (y - y_mean)) / np.sum((X - X_mean) ** 2)
            a = y_mean - b * X_mean

            regression = {
                "intercept": float(a),
                "slope": float(b),
                "r_squared": correlation ** 2,
            }
        else:
            correlation = 0.0
            regression = {"intercept": 0.0, "slope": 0.0, "r_squared": 0.0}

        results[protocol_id] = PropertyAnalysis(
            protocol_id=protocol_id,
            n_total=n_total,
            by_locality=locality_groups,
            locality_correlation=correlation,
            locality_regression=regression,
        )

    return results


def analyze_by_commutation(
    long_form_results: list[LongFormRow],
    commutation_groups: dict[str, int] | None = None,
    n_total: int | None = None,
) -> dict[str, dict[str, Any]]:
    """Analyze performance by commutation group.

    Observables that commute can be measured together in direct methods.
    Shadows don't care about commutation structure.

    Args:
        long_form_results: Long-form results
        commutation_groups: Map observable_id -> group_id (None = compute)
        n_total: Shot budget to analyze

    Returns:
        Analysis by commutation structure
    """
    if not long_form_results:
        return {}

    # Group by protocol
    by_protocol: dict[str, list[LongFormRow]] = defaultdict(list)
    for row in long_form_results:
        by_protocol[row.protocol_id].append(row)

    if n_total is None:
        n_total = max(row.N_total for row in long_form_results)

    results = {}

    for protocol_id, rows in by_protocol.items():
        rows_at_n = [r for r in rows if r.N_total == n_total]
        if not rows_at_n:
            continue

        # If commutation groups provided, analyze by group
        if commutation_groups:
            by_group: dict[int, list[float]] = defaultdict(list)
            for row in rows_at_n:
                group_id = commutation_groups.get(row.observable_id, -1)
                by_group[group_id].append(row.se)

            group_stats = {}
            for group_id, se_values in by_group.items():
                group_stats[str(group_id)] = {
                    "n_observables": len(se_values),
                    "mean_se": float(np.mean(se_values)),
                    "std_se": float(np.std(se_values)) if len(se_values) > 1 else 0.0,
                }

            results[protocol_id] = {
                "n_groups": len(by_group),
                "by_group": group_stats,
            }
        else:
            # Just report overall statistics
            se_values = [r.se for r in rows_at_n]
            results[protocol_id] = {
                "n_observables": len(se_values),
                "mean_se": float(np.mean(se_values)),
                "std_se": float(np.std(se_values)) if len(se_values) > 1 else 0.0,
            }

    return results


def compare_locality_performance(
    analysis_a: PropertyAnalysis,
    analysis_b: PropertyAnalysis,
) -> dict[str, Any]:
    """Compare two protocols' performance by locality.

    Args:
        analysis_a: Analysis for protocol A
        analysis_b: Analysis for protocol B

    Returns:
        Comparison statistics
    """
    common_localities = set(analysis_a.by_locality.keys()) & set(analysis_b.by_locality.keys())

    comparison = []
    for loc in sorted(common_localities):
        group_a = analysis_a.by_locality[loc]
        group_b = analysis_b.by_locality[loc]

        ratio = group_a.mean_se / group_b.mean_se if group_b.mean_se > 0 else float('inf')
        winner = analysis_a.protocol_id if ratio < 1 else analysis_b.protocol_id

        comparison.append({
            "locality": loc,
            "variance_factor": 3 ** loc,
            "se_a": group_a.mean_se,
            "se_b": group_b.mean_se,
            "ratio_a_over_b": ratio,
            "winner": winner,
        })

    # Summary
    a_wins = sum(1 for c in comparison if c["winner"] == analysis_a.protocol_id)
    b_wins = len(comparison) - a_wins

    return {
        "protocol_a": analysis_a.protocol_id,
        "protocol_b": analysis_b.protocol_id,
        "by_locality": comparison,
        "a_wins_localities": a_wins,
        "b_wins_localities": b_wins,
        "crossover_locality": next(
            (c["locality"] for i, c in enumerate(comparison[1:], 1)
             if comparison[i-1]["winner"] != c["winner"]),
            None
        ),
    }
