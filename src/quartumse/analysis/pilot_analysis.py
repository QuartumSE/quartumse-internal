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
        degenerate: True if all fractions snapped to the same grid point
        unique_pilot_ns: Number of distinct pilot_n values across fractions
    """

    target_n: int
    fractions: list[float]
    results: dict[float, PilotFractionResult]
    optimal_fraction: float | None
    summary: dict[str, Any]
    degenerate: bool = False
    unique_pilot_ns: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_n": self.target_n,
            "fractions": self.fractions,
            "results": {f: r.to_dict() for f, r in self.results.items()},
            "optimal_fraction": self.optimal_fraction,
            "summary": self.summary,
            "degenerate": self.degenerate,
            "unique_pilot_ns": self.unique_pilot_ns,
        }

    def to_dataframe(self):
        """Convert to pandas DataFrame for easy viewing."""
        import pandas as pd

        rows = []
        for frac, result in sorted(self.results.items()):
            rows.append(
                {
                    "pilot_fraction": frac,
                    "pilot_n": result.pilot_n,
                    "selection_accuracy": result.selection_accuracy,
                    "mean_regret": result.mean_regret,
                    "max_regret": result.max_regret,
                }
            )
        return pd.DataFrame(rows)


def _compute_quality(
    rows: list[LongFormRow],
    metric: str = "mean_se",
) -> float:
    """Compute quality metric from rows."""
    if not rows:
        return float("inf")

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
                target_rows = [
                    r for r in rows if r.N_total == target_n and r.replicate_id == rep_id
                ]

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

            selection_results.append(
                {
                    "replicate_id": rep_id,
                    "selected": selected,
                    "oracle": oracle,
                    "correct": selected == oracle,
                    "regret": regret,
                    "pilot_quality": pilot_quality,
                    "target_quality": target_quality,
                }
            )

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

    # Detect degeneracy: all fractions snapped to the same grid point
    pilot_n_values = [r.pilot_n for r in results.values()]
    unique_ns = len(set(pilot_n_values)) if pilot_n_values else 0
    is_degenerate = unique_ns < len(pilot_fractions) and unique_ns <= 1

    # Find optimal fraction (highest accuracy with reasonable cost)
    if results and not is_degenerate:
        # Simple heuristic: highest accuracy
        optimal = max(results.keys(), key=lambda f: results[f].selection_accuracy)
    else:
        optimal = None

    # Summary
    summary = {
        "n_protocols": len(protocols),
        "protocols": protocols,
        "n_replicates": len(replicate_ids) if "replicate_ids" in dir() else 0,
        "accuracy_by_fraction": {f: r.selection_accuracy for f, r in results.items()},
        "regret_by_fraction": {f: r.mean_regret for f, r in results.items()},
    }
    if is_degenerate:
        summary["degenerate_warning"] = (
            f"All {len(pilot_fractions)} pilot fractions snapped to pilot_n="
            f"{pilot_n_values[0] if pilot_n_values else '?'}. "
            f"Results are meaningless — use interpolated_pilot_analysis() instead."
        )

    return MultiPilotAnalysis(
        target_n=target_n,
        fractions=pilot_fractions,
        results=results,
        optimal_fraction=optimal,
        summary=summary,
        degenerate=is_degenerate,
        unique_pilot_ns=unique_ns,
    )


def interpolated_pilot_analysis(
    long_form_results: list[LongFormRow],
    target_n: int | None = None,
    pilot_fractions: list[float] | None = None,
    metric: str = "mae",
) -> MultiPilotAnalysis:
    """Pilot analysis using power-law interpolation instead of grid snapping.

    Fits MAE(N) = a * N^b per protocol using available grid points, then
    interpolates to the actual pilot shot count (e.g., 2% of 20000 = 400).
    This avoids the degeneracy problem where all fractions snap to the same
    grid point.

    Args:
        long_form_results: Long-form benchmark results (must have abs_err).
        target_n: Final shot budget (None = use max).
        pilot_fractions: List of pilot fractions to test.
        metric: Quality metric ("mae" uses mean absolute error).

    Returns:
        MultiPilotAnalysis with interpolated results.
    """
    from .interpolation import fit_power_law

    if pilot_fractions is None:
        pilot_fractions = [0.02, 0.05, 0.10, 0.20]

    # Determine target N and grid
    all_ns = sorted({r.N_total for r in long_form_results})
    if target_n is None:
        target_n = all_ns[-1]

    # Group by (protocol, replicate, N_total) -> list of abs_err
    by_proto: dict[str, dict[int, dict[int, list[float]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    for row in long_form_results:
        ae = row.abs_err
        if ae is None:
            # Fall back to SE if abs_err not available
            ae = row.se
        by_proto[row.protocol_id][row.replicate_id][row.N_total].append(ae)

    protocols = list(by_proto.keys())
    replicate_ids = sorted(
        {r.replicate_id for r in long_form_results if r.N_total == target_n}
    )

    if len(all_ns) < 2:
        # Can't fit power law with < 2 grid points
        return MultiPilotAnalysis(
            target_n=target_n,
            fractions=pilot_fractions,
            results={},
            optimal_fraction=None,
            summary={"error": "Need at least 2 grid points for interpolation"},
            degenerate=False,
            unique_pilot_ns=0,
        )

    # Step 1: Fit power law per (protocol, replicate) so each replicate can
    #         select a different protocol at different pilot budgets.
    # fits[pid][rid] = PowerLawFit or None
    fits: dict[str, dict[int, Any]] = defaultdict(dict)
    for pid in protocols:
        for rid in replicate_ids:
            ns_for_fit = []
            maes_for_fit = []
            for n in all_ns:
                errs = by_proto[pid][rid][n]
                if errs:
                    ns_for_fit.append(n)
                    maes_for_fit.append(float(np.mean(errs)))
            if len(ns_for_fit) >= 2:
                fits[pid][rid] = fit_power_law(ns_for_fit, maes_for_fit)
            else:
                fits[pid][rid] = None

    # Also compute protocol-level fits for summary reporting
    proto_fits: dict[str, Any] = {}
    for pid in protocols:
        ns_for_fit = []
        maes_for_fit = []
        for n in all_ns:
            rep_maes = []
            for rid in replicate_ids:
                errs = by_proto[pid][rid][n]
                if errs:
                    rep_maes.append(float(np.mean(errs)))
            if rep_maes:
                ns_for_fit.append(n)
                maes_for_fit.append(float(np.mean(rep_maes)))
        if len(ns_for_fit) >= 2:
            proto_fits[pid] = fit_power_law(ns_for_fit, maes_for_fit)

    # Step 2: For each replicate, compute MAE at target_n (for oracle)
    target_mae: dict[str, dict[int, float]] = defaultdict(dict)
    for pid in protocols:
        for rid in replicate_ids:
            errs = by_proto[pid][rid][target_n]
            if errs:
                target_mae[pid][rid] = float(np.mean(errs))

    results = {}

    for frac in pilot_fractions:
        pilot_n = int(frac * target_n)
        if pilot_n >= target_n or pilot_n <= 0:
            continue

        selection_results = []
        selections: Counter[str] = Counter()

        for rid in replicate_ids:
            # Interpolate MAE for each protocol at pilot_n using per-replicate fits
            interp_mae: dict[str, float] = {}
            for pid in protocols:
                fit = fits.get(pid, {}).get(rid)
                if fit is not None and not np.isnan(fit.amplitude):
                    interp_mae[pid] = fit.predict(pilot_n)
                else:
                    # Fallback: use nearest grid point for this replicate
                    nearest_n = min(all_ns, key=lambda x: abs(x - pilot_n))
                    errs = by_proto[pid][rid][nearest_n]
                    interp_mae[pid] = float(np.mean(errs)) if errs else float("inf")

            if not interp_mae:
                continue

            # Select best protocol based on interpolated MAE
            selected = min(interp_mae, key=interp_mae.get)
            # Oracle: best at target_n for this replicate
            rep_target = {
                pid: target_mae[pid].get(rid, float("inf")) for pid in protocols
            }
            oracle = min(rep_target, key=rep_target.get)

            selections[selected] += 1
            regret = rep_target[selected] - rep_target[oracle]

            selection_results.append(
                {
                    "replicate_id": rid,
                    "selected": selected,
                    "oracle": oracle,
                    "correct": selected == oracle,
                    "regret": regret,
                    "interpolated_mae": interp_mae,
                    "target_mae": dict(rep_target),
                }
            )

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

    # Find optimal fraction
    if results:
        optimal = max(results.keys(), key=lambda f: results[f].selection_accuracy)
    else:
        optimal = None

    # Unique pilot_n values (should all be different now)
    pilot_n_values = [r.pilot_n for r in results.values()]
    unique_ns = len(set(pilot_n_values))

    # Power-law fit quality summary (protocol-level averages for reporting)
    fit_summary = {}
    for pid, fit in proto_fits.items():
        if fit is not None and not np.isnan(fit.amplitude):
            fit_summary[pid] = {
                "amplitude": fit.amplitude,
                "exponent": fit.exponent,
                "r_squared": fit.r_squared,
            }

    summary = {
        "n_protocols": len(protocols),
        "protocols": protocols,
        "n_replicates": len(replicate_ids),
        "method": "power_law_interpolation",
        "accuracy_by_fraction": {f: r.selection_accuracy for f, r in results.items()},
        "regret_by_fraction": {f: r.mean_regret for f, r in results.items()},
        "power_law_fits": fit_summary,
    }

    return MultiPilotAnalysis(
        target_n=target_n,
        fractions=pilot_fractions,
        results=results,
        optimal_fraction=optimal,
        summary=summary,
        degenerate=False,
        unique_pilot_ns=unique_ns,
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

        rows.append(
            {
                "pilot_fraction": frac,
                "pilot_cost": pilot_cost_frac,
                "selection_accuracy": result.selection_accuracy,
                "mean_regret": result.mean_regret,
                "net_benefit": net_benefit,
            }
        )

    # Find breakeven point
    breakeven = None
    for row in rows:
        if row["net_benefit"] > 0:
            breakeven = row["pilot_fraction"]
            break

    return {
        "analysis": rows,
        "breakeven_fraction": breakeven,
        "best_fraction": (
            max(rows, key=lambda x: x["net_benefit"])["pilot_fraction"] if rows else None
        ),
    }
