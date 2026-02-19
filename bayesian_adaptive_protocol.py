"""Bayesian adaptive protocol selection simulation.

Incrementally allocates batches of shots to all protocols and uses Bayesian
posterior estimation to decide *when* to commit to a single protocol — no
pre-chosen pilot fraction.  After commitment, remaining budget goes entirely
to the selected protocol.

Usage:
    python bayesian_adaptive_protocol.py --data-dir pilot_analysis_noise/ideal/<run>/base
    python bayesian_adaptive_protocol.py --data-dir pilot_analysis_noise/ideal/<run>/base --batch-size 200 --thresholds 0.80,0.90,0.95,0.99
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
sys.path.insert(0, "src")

from pilot_posthoc_analysis import (
    BASIS_MAP,
    SHORT,
    _estimate_direct_observable,
    _estimate_shadows_observable,
    build_obs_registry,
)

# ---------------------------------------------------------------------------
# Step 1 — Load and parse benchmark data
# ---------------------------------------------------------------------------

def load_and_parse(base_dir: Path) -> dict:
    """Load raw shots, long-form, and ground truth from a benchmark base/ dir.

    Returns a dict with keys:
        raw_lookup, group_to_obs, obs_registry, obs_ids, ground_truth,
        n_budget, n_reps, replicates, protocols
    """
    raw_df = pd.read_parquet(base_dir / "raw_shots" / "data.parquet")
    lf_df = pd.read_parquet(base_dir / "long_form" / "data.parquet")
    with open(base_dir / "ground_truth.json") as f:
        gt = json.load(f)
    truth = gt["truth_values"]

    n_budget = int(raw_df["N_total"].max())
    raw_df = raw_df[raw_df["N_total"] == n_budget].copy()
    lf_df = lf_df[lf_df["N_total"] == n_budget].copy()

    protocols = sorted(raw_df["protocol_id"].unique())
    replicates = sorted(raw_df["replicate_id"].unique())

    n_qubits = gt.get("n_qubits", 4)
    obs_reg = build_obs_registry(n_qubits)

    lf_obs_ids = set(lf_df["observable_id"].unique())
    matched = lf_obs_ids & set(obs_reg.keys())
    if not matched:
        sys.exit("ERROR: no observable IDs match between long-form and registry")
    obs_ids = sorted(matched)

    # group_id → [observable_id] mapping (for direct protocols)
    group_to_obs: dict[str, list[str]] = {}
    for _, row in lf_df[lf_df["protocol_id"] == "direct_grouped"].drop_duplicates(
        subset=["observable_id", "group_id"]
    ).iterrows():
        oid = row["observable_id"]
        gid = row["group_id"]
        if oid in matched and gid is not None:
            group_to_obs.setdefault(gid, []).append(oid)

    # Parse raw shot data into fast lookup
    raw_lookup: dict[tuple, tuple] = {}
    for _, row in raw_df.iterrows():
        key = (row["protocol_id"], row["replicate_id"], row["setting_id"])
        bs = json.loads(row["bitstrings"])
        mb = json.loads(row["measurement_bases"]) if pd.notna(row.get("measurement_bases")) else None
        raw_lookup[key] = (bs, mb)

    # Full-budget MAE per protocol per replicate (for oracle comparison)
    full_mae: dict[str, dict[int, float]] = {}  # protocol → replicate → MAE
    for pid in protocols:
        full_mae[pid] = {}
        for rid in replicates:
            sub = lf_df[(lf_df["protocol_id"] == pid) & (lf_df["replicate_id"] == rid)]
            sub = sub[sub["observable_id"].isin(matched)]
            if len(sub) == 0:
                continue
            if "abs_err" in sub.columns:
                full_mae[pid][rid] = float(sub["abs_err"].mean())
            else:
                errs = [abs(r["estimate"] - truth.get(r["observable_id"], 0))
                        for _, r in sub.iterrows()]
                full_mae[pid][rid] = float(np.mean(errs))

    return {
        "raw_lookup": raw_lookup,
        "group_to_obs": group_to_obs,
        "obs_registry": obs_reg,
        "obs_ids": obs_ids,
        "ground_truth": truth,
        "n_budget": n_budget,
        "n_reps": len(replicates),
        "replicates": replicates,
        "protocols": protocols,
        "full_mae": full_mae,
    }


# ---------------------------------------------------------------------------
# Step 2 — Estimate per-observable errors for a protocol at n_shots
# ---------------------------------------------------------------------------

def estimate_protocol_errors(
    raw_lookup: dict[tuple, tuple],
    protocol: str,
    replicate: int,
    n_shots: int,
    n_budget: int,
    obs_registry: dict[str, dict],
    obs_ids: list[str],
    group_to_obs: dict[str, list[str]],
    ground_truth: dict[str, float],
) -> dict[str, float]:
    """Subsample from raw shots proportionally, re-estimate, return abs errors.

    n_shots is the total budget allocated to this protocol. For direct
    protocols the per-group subsample is proportional: each group gets
    ceil(n_shots / n_budget * n_group_shots_at_full_budget).  For shadows
    the single setting is subsampled directly.

    Returns dict[obs_id -> absolute_error].
    """
    frac = min(n_shots / n_budget, 1.0)
    errors: dict[str, float] = {}

    if protocol in ("direct_grouped", "direct_optimized"):
        for gid, obs_list in group_to_obs.items():
            key = (protocol, replicate, gid)
            if key not in raw_lookup:
                continue
            bs_all, _ = raw_lookup[key]
            n_sub = max(1, math.ceil(frac * len(bs_all)))
            bs_sub = bs_all[:n_sub]

            for oid in obs_list:
                if oid not in obs_registry or oid not in ground_truth:
                    continue
                info = obs_registry[oid]
                est, _ = _estimate_direct_observable(
                    bs_sub, info["support"], info["coefficient"]
                )
                if not np.isnan(est):
                    errors[oid] = abs(est - ground_truth[oid])

    elif protocol == "classical_shadows_v0":
        key = (protocol, replicate, "shadows_random_local_clifford")
        if key not in raw_lookup:
            return errors
        bs_all, mb_all = raw_lookup[key]
        n_sub = max(1, int(frac * len(bs_all)))

        outcomes = np.array(
            [[int(c) for c in s] for s in bs_all[:n_sub]], dtype=np.int8
        )
        bases = np.array(mb_all[:n_sub], dtype=np.int8)

        for oid in obs_ids:
            if oid not in obs_registry or oid not in ground_truth:
                continue
            info = obs_registry[oid]
            est, _ = _estimate_shadows_observable(
                outcomes, bases,
                info["pauli_string"], info["coefficient"], info["support"],
            )
            if not np.isnan(est):
                errors[oid] = abs(est - ground_truth[oid])

    return errors


# ---------------------------------------------------------------------------
# Step 3 — Bayesian P(best) via Monte Carlo
# ---------------------------------------------------------------------------

def bayesian_p_best(
    protocol_errors: dict[str, np.ndarray],
    n_mc: int = 10000,
    rng: np.random.Generator | None = None,
) -> dict[str, float]:
    """Compute P(protocol is best) via MC draws from t-distribution posteriors.

    Parameters
    ----------
    protocol_errors : dict mapping protocol_id → 1-D array of per-observable
        absolute errors at current exploration budget.
    n_mc : number of Monte Carlo samples.
    rng : optional numpy random generator for reproducibility.

    Returns
    -------
    dict[str, float] mapping protocol_id → P(best).
    """
    if rng is None:
        rng = np.random.default_rng()

    protos = list(protocol_errors.keys())
    n_protos = len(protos)
    draws = np.empty((n_mc, n_protos))

    for j, pid in enumerate(protos):
        errs = protocol_errors[pid]
        m = len(errs)
        if m < 2:
            # Not enough data — draw from a very wide distribution
            draws[:, j] = rng.standard_t(df=1, size=n_mc) * 10 + (errs.mean() if m > 0 else 1.0)
            continue

        x_bar = errs.mean()
        s = errs.std(ddof=1) / math.sqrt(m)
        df = m - 1

        # Draw from t(df, loc=x_bar, scale=s)
        draws[:, j] = rng.standard_t(df=df, size=n_mc) * s + x_bar

    # P(best) = fraction of draws where protocol has the LOWEST MAE
    best_idx = draws.argmin(axis=1)
    counts = np.bincount(best_idx, minlength=n_protos)
    p_best = {pid: float(counts[j] / n_mc) for j, pid in enumerate(protos)}
    return p_best


# ---------------------------------------------------------------------------
# Step 4 — Simulate one replicate of the adaptive process
# ---------------------------------------------------------------------------

def simulate_one_replicate(
    raw_lookup: dict[tuple, tuple],
    replicate_id: int,
    protocols: list[str],
    obs_registry: dict[str, dict],
    obs_ids: list[str],
    group_to_obs: dict[str, list[str]],
    ground_truth: dict[str, float],
    n_budget: int,
    batch_size: int,
    threshold: float,
    n_mc: int,
    rng: np.random.Generator | None = None,
) -> dict:
    """Run the Bayesian adaptive loop for a single replicate.

    Returns dict with:
        committed_step, selected_protocol, p_best_at_commit,
        exploration_shots_per_proto, final_shots, final_mae, trajectory
    """
    if rng is None:
        rng = np.random.default_rng()

    K = len(protocols)
    max_steps = n_budget // (K * batch_size)
    if max_steps < 1:
        max_steps = 1

    trajectory: list[dict] = []
    selected = None
    commit_step = None
    p_best_at_commit = None

    for step in range(1, max_steps + 1):
        n_shots_so_far = step * batch_size

        # Estimate errors for each protocol at current exploration budget
        protocol_errors: dict[str, np.ndarray] = {}
        for pid in protocols:
            errs = estimate_protocol_errors(
                raw_lookup, pid, replicate_id, n_shots_so_far, n_budget,
                obs_registry, obs_ids, group_to_obs, ground_truth,
            )
            protocol_errors[pid] = np.array(list(errs.values())) if errs else np.array([np.nan])

        # Bayesian comparison
        p_best = bayesian_p_best(protocol_errors, n_mc=n_mc, rng=rng)

        step_record = {"step": step, "shots_per_proto": n_shots_so_far}
        step_record.update({f"p_best_{SHORT.get(p, p)}": p_best[p] for p in protocols})
        step_record["committed"] = False
        trajectory.append(step_record)

        # Check commitment
        best_p = max(p_best, key=p_best.get)
        if p_best[best_p] >= threshold:
            selected = best_p
            commit_step = step
            p_best_at_commit = p_best[best_p]
            step_record["committed"] = True
            break

    # If never committed, force-select
    if selected is None:
        last_p_best = {p: trajectory[-1][f"p_best_{SHORT.get(p, p)}"] for p in protocols}
        selected = max(last_p_best, key=last_p_best.get)
        commit_step = max_steps
        p_best_at_commit = last_p_best[selected]
        trajectory[-1]["committed"] = True

    exploration_shots_per_proto = commit_step * batch_size
    total_exploration = K * exploration_shots_per_proto
    remaining = n_budget - total_exploration
    final_shots_for_selected = exploration_shots_per_proto + remaining

    # Compute final MAE using the selected protocol with its final shot count
    final_errors = estimate_protocol_errors(
        raw_lookup, selected, replicate_id, final_shots_for_selected, n_budget,
        obs_registry, obs_ids, group_to_obs, ground_truth,
    )
    final_mae = float(np.mean(list(final_errors.values()))) if final_errors else np.nan

    return {
        "committed_step": commit_step,
        "selected_protocol": selected,
        "p_best_at_commit": p_best_at_commit,
        "exploration_shots_per_proto": exploration_shots_per_proto,
        "total_exploration": total_exploration,
        "final_shots": final_shots_for_selected,
        "final_mae": final_mae,
        "trajectory": trajectory,
    }


# ---------------------------------------------------------------------------
# Step 5 — Run full adaptive simulation
# ---------------------------------------------------------------------------

def run_adaptive_simulation(
    base_dir: Path,
    batch_size: int = 200,
    thresholds: list[float] | None = None,
    n_mc: int = 10000,
):
    """Outer loop: load data, sweep thresholds, print results."""
    if thresholds is None:
        thresholds = [0.80, 0.90, 0.95, 0.99]

    print(f"Loading data from {base_dir} ...")
    data = load_and_parse(base_dir)

    raw_lookup = data["raw_lookup"]
    group_to_obs = data["group_to_obs"]
    obs_reg = data["obs_registry"]
    obs_ids = data["obs_ids"]
    truth = data["ground_truth"]
    n_budget = data["n_budget"]
    replicates = data["replicates"]
    protocols = data["protocols"]
    full_mae = data["full_mae"]
    n_reps = data["n_reps"]

    # Oracle: which protocol is truly best at full budget?
    oracle_mean_mae = {}
    for pid in protocols:
        maes = [full_mae[pid][r] for r in replicates if r in full_mae[pid]]
        oracle_mean_mae[pid] = float(np.mean(maes)) if maes else np.nan
    oracle_protocol = min(oracle_mean_mae, key=oracle_mean_mae.get)

    K = len(protocols)
    print(f"\n{'='*80}")
    print("BAYESIAN ADAPTIVE PROTOCOL SELECTION")
    print(f"{'='*80}")
    print(f"Total budget: {n_budget}, Batch size: {batch_size}, Protocols: {K}")
    print(f"Observables: {len(obs_ids)}, Replicates: {n_reps}")
    print(f"Oracle winner: {SHORT.get(oracle_protocol, oracle_protocol)} "
          f"(MAE={oracle_mean_mae[oracle_protocol]:.5f})")

    # ---- Sweep thresholds ---------------------------------------------------
    all_threshold_results: list[dict] = []

    for thresh in thresholds:
        rep_results: list[dict] = []
        rng = np.random.default_rng(42)

        for rid in replicates:
            res = simulate_one_replicate(
                raw_lookup, rid, protocols, obs_reg, obs_ids,
                group_to_obs, truth, n_budget, batch_size, thresh, n_mc, rng,
            )
            res["replicate_id"] = rid
            res["oracle_mae"] = full_mae.get(oracle_protocol, {}).get(rid, np.nan)
            res["correct"] = (res["selected_protocol"] == oracle_protocol)
            rep_results.append(res)

        # Aggregate
        commit_steps = [r["committed_step"] for r in rep_results]
        expl_shots = [r["total_exploration"] for r in rep_results]
        final_shots = [r["final_shots"] for r in rep_results]
        final_maes = [r["final_mae"] for r in rep_results]
        oracle_maes = [r["oracle_mae"] for r in rep_results]
        accuracy = sum(1 for r in rep_results if r["correct"]) / n_reps
        selections = Counter(r["selected_protocol"] for r in rep_results)

        sel_str = ", ".join(
            f"{SHORT.get(p, p)}:{c}" for p, c in selections.most_common()
        )

        all_threshold_results.append({
            "threshold": thresh,
            "mean_commit_step": np.mean(commit_steps),
            "std_commit_step": np.std(commit_steps),
            "mean_expl_shots": np.mean(expl_shots),
            "mean_final_shots": np.mean(final_shots),
            "selection_str": sel_str,
            "accuracy": accuracy,
            "mean_oracle_mae": np.mean(oracle_maes),
            "mean_adaptive_mae": np.mean(final_maes),
            "mean_regret": np.mean(final_maes) - np.mean(oracle_maes),
            "rep_results": rep_results,
        })

    # ---- Table 1: Adaptive Results per Threshold ----------------------------
    print(f"\n{'Threshold':>9}  {'Commit Step':>12}  {'Expl Shots':>10}  "
          f"{'Final Shots':>11}  {'Selected':<18}  {'Accuracy':>8}  "
          f"{'Oracle MAE':>10}  {'Adapt MAE':>10}  {'Regret':>8}")
    print("-" * 115)
    for tr in all_threshold_results:
        print(f"  {tr['threshold']:5.0%}    "
              f"{tr['mean_commit_step']:5.1f} +/- {tr['std_commit_step']:3.1f}  "
              f"{tr['mean_expl_shots']:10.0f}  "
              f"{tr['mean_final_shots']:11.0f}  "
              f"{tr['selection_str']:<18}  "
              f"{tr['accuracy']:7.0%}   "
              f"{tr['mean_oracle_mae']:10.5f}  "
              f"{tr['mean_adaptive_mae']:10.5f}  "
              f"{tr['mean_regret']:+8.5f}")

    # ---- Table 2: Exploration Trajectory (for the threshold closest to 95%) --
    default_idx = min(range(len(thresholds)), key=lambda i: abs(thresholds[i] - 0.95))
    default_tr = all_threshold_results[default_idx]
    # Show trajectory for the first replicate
    rep0 = default_tr["rep_results"][0]

    short_names = [SHORT.get(p, p) for p in protocols]
    print(f"\n{'='*80}")
    print(f"EXPLORATION TRAJECTORY (threshold={default_tr['threshold']:.0%}, replicate 0)")
    print(f"{'='*80}")
    header = f"{'Step':>4}  {'Shots/proto':>11}"
    for sn in short_names:
        header += f"  {sn+' P(best)':>16}"
    header += f"  {'Committed?':>10}"
    print(header)
    print("-" * len(header))

    for rec in rep0["trajectory"]:
        line = f"{rec['step']:4d}  {rec['shots_per_proto']:11d}"
        for pid in protocols:
            key = f"p_best_{SHORT.get(pid, pid)}"
            line += f"  {rec[key]:16.3f}"
        if rec["committed"]:
            line += f"  -> {SHORT.get(rep0['selected_protocol'], rep0['selected_protocol'])}"
        else:
            line += f"  {'':>10}"
        print(line)

    # ---- Table 3: Per-Replicate Detail (for default threshold) ---------------
    print(f"\n{'='*80}")
    print(f"PER-REPLICATE DETAIL (threshold={default_tr['threshold']:.0%})")
    print(f"{'='*80}")
    print(f"{'Replicate':>9}  {'Commit Step':>11}  {'Selected':<12}  "
          f"{'Final MAE':>10}  {'Oracle MAE':>10}  {'Correct?':>8}")
    print("-" * 72)
    for r in default_tr["rep_results"]:
        print(f"{r['replicate_id']:9d}  {r['committed_step']:11d}  "
              f"{SHORT.get(r['selected_protocol'], r['selected_protocol']):<12}  "
              f"{r['final_mae']:10.5f}  {r['oracle_mae']:10.5f}  "
              f"{'Yes' if r['correct'] else 'NO':>8}")

    # ---- Table 4: Comparison to Fixed-Fraction Pilot -------------------------
    print(f"\n{'='*80}")
    print("COMPARISON TO FIXED-FRACTION PILOT")
    print(f"{'='*80}")
    print(f"{'Strategy':<24}  {'Expl Budget':>11}  {'Final MAE':>10}  {'Accuracy':>8}")
    print("-" * 60)

    # Simulate fixed-fraction pilots for comparison
    for frac_label, frac in [("Fixed 1% pilot", 0.01), ("Fixed 5% pilot", 0.05)]:
        n_pilot = int(frac * n_budget)
        correct = 0
        final_maes_fixed = []
        for rid in replicates:
            pilot_maes = {}
            for pid in protocols:
                errs = estimate_protocol_errors(
                    raw_lookup, pid, rid, n_pilot, n_budget,
                    obs_reg, obs_ids, group_to_obs, truth,
                )
                pilot_maes[pid] = float(np.mean(list(errs.values()))) if errs else np.nan

            selected_pid = min(
                (p for p in pilot_maes if not np.isnan(pilot_maes[p])),
                key=lambda p: pilot_maes[p],
                default=protocols[0],
            )
            if selected_pid == oracle_protocol:
                correct += 1

            # Final MAE: selected protocol uses remaining budget
            remaining_fixed = n_budget - K * n_pilot
            final_shots_fixed = n_pilot + remaining_fixed
            errs_final = estimate_protocol_errors(
                raw_lookup, selected_pid, rid, final_shots_fixed, n_budget,
                obs_reg, obs_ids, group_to_obs, truth,
            )
            final_maes_fixed.append(
                float(np.mean(list(errs_final.values()))) if errs_final else np.nan
            )

        acc_fixed = correct / n_reps
        print(f"{frac_label:<24}  {K * n_pilot:11d}  "
              f"{np.nanmean(final_maes_fixed):10.5f}  {acc_fixed:7.0%}")

    # Adaptive rows
    for tr in all_threshold_results:
        label = f"Adaptive ({tr['threshold']:.0%})"
        print(f"{label:<24}  {tr['mean_expl_shots']:11.0f}  "
              f"{tr['mean_adaptive_mae']:10.5f}  {tr['accuracy']:7.0%}")

    # Oracle row
    print(f"{'Full oracle':<24}  {'0':>11}  "
          f"{oracle_mean_mae[oracle_protocol]:10.5f}  {'100%':>8}")

    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Bayesian adaptive protocol selection simulation"
    )
    parser.add_argument(
        "--data-dir", type=str, required=True,
        help="Path to benchmark base/ directory with raw_shots/, long_form/, ground_truth.json",
    )
    parser.add_argument(
        "--batch-size", type=int, default=200,
        help="Shots per protocol per exploration step (default: 200)",
    )
    parser.add_argument(
        "--thresholds", type=str, default="0.80,0.90,0.95,0.99",
        help="Comma-separated P(best) thresholds to sweep (default: 0.80,0.90,0.95,0.99)",
    )
    parser.add_argument(
        "--n-mc", type=int, default=10000,
        help="Monte Carlo samples for posterior (default: 10000)",
    )
    args = parser.parse_args()

    base_dir = Path(args.data_dir)
    # Accept either base/ dir or its parent
    if not (base_dir / "raw_shots" / "data.parquet").exists():
        if (base_dir / "base" / "raw_shots" / "data.parquet").exists():
            base_dir = base_dir / "base"
        else:
            sys.exit(f"ERROR: no raw_shots/data.parquet found under {base_dir}")

    thresholds = [float(x.strip()) for x in args.thresholds.split(",")]

    run_adaptive_simulation(
        base_dir=base_dir,
        batch_size=args.batch_size,
        thresholds=thresholds,
        n_mc=args.n_mc,
    )


if __name__ == "__main__":
    main()
