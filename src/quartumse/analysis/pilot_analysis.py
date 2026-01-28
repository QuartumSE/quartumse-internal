"""Multi-pilot fraction analysis.

Implements Benchmarking_Improvement.md enhancement:
- Multiple pilot fractions (2%, 5%, 10%, 20%)
- Selection accuracy at each fraction
- Regret analysis
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ..io.schemas import LongFormRow


@dataclass
class PilotFractionResult:
    """Result for a specific pilot fraction.

    Attributes:
        pilot_fraction: Fraction of budget used for pilot (e.g., 0.05)
        pilot_n: Actual pilot shot count
        target_n: Target shot count for final evaluation
        selection_accuracy: Fraction of times correct protocol selected
        mean_regret: Mean extra error from wrong selection
        max_regret: Maximum regret observed
        protocol_selections: Counter of which protocols were selected
        per_replicate: Detailed results per replicate
    """
    pilot_fraction: float
    pilot_n: int
    target_n: int
    selection_accuracy: float
    mean_regret: float
    max_regret: float
    protocol_selections: dict[str, int]
    per_replicate: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pilot_fraction": self.pilot_fraction,
            "pilot_n": self.pilot_n,
            "target_n": self.target_n,
            "selection_accuracy": self.selection_accuracy,
            "mean_regret": self.mean_regret,
            "max_regret": self.max_regret,
            "protocol_selections": self.protocol_selections,
        }


@dataclass
class MultiPilotAnalysis:
    """Complete multi-pilot fraction analysis.

    Attributes:
        target_n: Final shot budget
        fractions: List of pilot fractions analyzed
        results: Results per fraction
        optimal_fraction: Fraction with best accuracy-cost tradeoff
        summary: Summary statistics
    """
    target_n: int
    fractions: list[float]
    results: dict[float, PilotFractionResult]
    optimal_fraction: float | None
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_n": self.target_n,
            "fractions": self.fractions,
            "results": {f: r.to_dict() for f, r in self.results.items()},
            "optimal_fraction": self.optimal_fraction,
            "summary": self.summary,
        }

    def to_dataframe(self):
        """Convert to pandas DataFrame for easy viewing."""
        import pandas as pd
        rows = []
        for frac, result in sorted(self.results.items()):
            rows.append({
                "pilot_fraction": frac,
                "pilot_n": result.pilot_n,
                "selection_accuracy": result.selection_accuracy,
                "mean_regret": result.mean_regret,
                "max_regret": result.max_regret,
            })
        return pd.DataFrame(rows)


def _compute_quality(
    rows: list[LongFormRow],
    metric: str = "mean_se",
) -> float:
    """Compute quality metric from rows."""
    if not rows:
        return float('inf')

    se_values = [r.se for r in rows]

    if metric == "mean_se":
        return float(np.mean(se_values))
    elif metric == "median_se":
        return float(np.median(se_values))
    elif metric == "max_se":
        return float(np.max(se_values))
    else:
        return float(np.mean(se_values))


def multi_pilot_analysis(
    long_form_results: list[LongFormRow],
    target_n: int | None = None,
    pilot_fractions: list[float] | None = None,
    metric: str = "mean_se",
) -> MultiPilotAnalysis:
    """Analyze pilot-based selection across multiple pilot fractions.

    Args:
        long_form_results: Long-form benchmark results
        target_n: Final shot budget (None = use max)
        pilot_fractions: List of pilot fractions to test
        metric: Quality metric ("mean_se", "median_se", "max_se")

    Returns:
        MultiPilotAnalysis with results for each fraction
    """
    if pilot_fractions is None:
        pilot_fractions = [0.02, 0.05, 0.10, 0.20]

    # Determine target N
    all_ns = sorted({r.N_total for r in long_form_results})
    if target_n is None:
        target_n = all_ns[-1]

    # Group by protocol
    by_protocol: dict[str, list[LongFormRow]] = defaultdict(list)
    for row in long_form_results:
        by_protocol[row.protocol_id].append(row)

    protocols = list(by_protocol.keys())

    # Get available N values
    available_ns = set()
    for rows in by_protocol.values():
        available_ns.update(r.N_total for r in rows)
    available_ns = sorted(available_ns)

    results = {}

    for frac in pilot_fractions:
        # Find closest available N to pilot fraction
        ideal_pilot_n = int(frac * target_n)
        pilot_n = min(available_ns, key=lambda x: abs(x - ideal_pilot_n))

        if pilot_n >= target_n:
            # Skip if pilot >= target
            continue

        # Group by replicate
        replicate_ids = set()
        for rows in by_protocol.values():
            for row in rows:
                if row.N_total in [pilot_n, target_n]:
                    replicate_ids.add(row.replicate_id)

        selection_results = []
        selections: Counter[str] = Counter()

        for rep_id in sorted(replicate_ids):
            # Get pilot quality for each protocol
            pilot_quality = {}
            target_quality = {}

            for protocol_id, rows in by_protocol.items():
                pilot_rows = [r for r in rows if r.N_total == pilot_n and r.replicate_id == rep_id]
                target_rows = [r for r in rows if r.N_total == target_n and r.replicate_id == rep_id]

                pilot_quality[protocol_id] = _compute_quality(pilot_rows, metric)
                target_quality[protocol_id] = _compute_quality(target_rows, metric)

            if not pilot_quality or not target_quality:
                continue

            # Select best protocol based on pilot
            selected = min(pilot_quality, key=pilot_quality.get)
            # Oracle: best at target
            oracle = min(target_quality, key=target_quality.get)

            selections[selected] += 1

            # Compute regret
            regret = target_quality[selected] - target_quality[oracle]

            selection_results.append({
                "replicate_id": rep_id,
                "selected": selected,
                "oracle": oracle,
                "correct": selected == oracle,
                "regret": regret,
                "pilot_quality": pilot_quality,
                "target_quality": target_quality,
            })

        if not selection_results:
            continue

        accuracy = float(np.mean([r["correct"] for r in selection_results]))
        regrets = [r["regret"] for r in selection_results]

        results[frac] = PilotFractionResult(
            pilot_fraction=frac,
            pilot_n=pilot_n,
            target_n=target_n,
            selection_accuracy=accuracy,
            mean_regret=float(np.mean(regrets)),
            max_regret=float(np.max(regrets)),
            protocol_selections=dict(selections),
            per_replicate=selection_results,
        )

    # Find optimal fraction (highest accuracy with reasonable cost)
    if results:
        # Simple heuristic: highest accuracy
        optimal = max(results.keys(), key=lambda f: results[f].selection_accuracy)
    else:
        optimal = None

    # Summary
    summary = {
        "n_protocols": len(protocols),
        "protocols": protocols,
        "n_replicates": len(replicate_ids) if 'replicate_ids' in dir() else 0,
        "accuracy_by_fraction": {f: r.selection_accuracy for f, r in results.items()},
        "regret_by_fraction": {f: r.mean_regret for f, r in results.items()},
    }

    return MultiPilotAnalysis(
        target_n=target_n,
        fractions=pilot_fractions,
        results=results,
        optimal_fraction=optimal,
        summary=summary,
    )


def pilot_cost_benefit(
    analysis: MultiPilotAnalysis,
) -> dict[str, Any]:
    """Analyze cost-benefit tradeoff for pilot selection.

    Args:
        analysis: MultiPilotAnalysis results

    Returns:
        Cost-benefit analysis
    """
    rows = []
    for frac, result in sorted(analysis.results.items()):
        # Pilot cost as fraction of total budget
        pilot_cost_frac = frac

        # Expected quality improvement from correct selection
        # (simplified: assume accuracy translates to quality)
        expected_benefit = result.selection_accuracy

        # Net benefit: accuracy - pilot cost
        net_benefit = expected_benefit - pilot_cost_frac

        rows.append({
            "pilot_fraction": frac,
            "pilot_cost": pilot_cost_frac,
            "selection_accuracy": result.selection_accuracy,
            "mean_regret": result.mean_regret,
            "net_benefit": net_benefit,
        })

    # Find breakeven point
    breakeven = None
    for row in rows:
        if row["net_benefit"] > 0:
            breakeven = row["pilot_fraction"]
            break

    return {
        "analysis": rows,
        "breakeven_fraction": breakeven,
        "best_fraction": max(rows, key=lambda x: x["net_benefit"])["pilot_fraction"] if rows else None,
    }
