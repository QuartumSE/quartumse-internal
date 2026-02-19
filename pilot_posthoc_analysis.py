"""Post-hoc pilot analysis from stored raw shots.

Loads raw shot data from a benchmark run and simulates what would happen
if only a fraction of shots were used as a pilot to select the best
protocol. Auto-detects N from the data.

Usage:
    python pilot_posthoc_analysis.py                   # generate + analyse
    python pilot_posthoc_analysis.py --data-dir PATH   # analyse existing run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "src")

# -- Constants ----------------------------------------------------------------
PILOT_FRACTIONS = [0.01, 0.02, 0.05, 0.10, 0.20, 0.50]
N_BUDGET = 5000
N_REPLICATES = 10
PROTOCOLS = ["direct_grouped", "direct_optimized", "classical_shadows_v0"]
SHORT = {
    "direct_grouped": "grouped",
    "direct_optimized": "optimized",
    "classical_shadows_v0": "shadows",
}
BASIS_MAP = {"X": 1, "Y": 2, "Z": 0}  # matches shadows protocol encoding


# -- Step 0: Generate benchmark data -----------------------------------------
def build_h2_circuit():
    from qiskit import QuantumCircuit

    qc = QuantumCircuit(4)
    qc.x(0)
    qc.x(1)
    qc.ry(np.pi / 6, 2)
    qc.cx(2, 3)
    qc.cx(1, 2)
    qc.ry(-np.pi / 8, 1)
    qc.cx(0, 1)
    return qc


def build_merged_observable_set():
    from quartumse.observables.core import ObservableSet
    from quartumse.observables.suites import make_chemistry_suites

    suites = make_chemistry_suites(4)
    pauli_to_obs: dict = {}
    for suite in suites.values():
        for obs in suite.observables:
            if obs.pauli_string not in pauli_to_obs:
                pauli_to_obs[obs.pauli_string] = obs
    merged = list(pauli_to_obs.values())
    return ObservableSet(
        observables=merged,
        observable_set_id="C-H2_merged",
        generator_id="suite_merger",
        generator_version="1.0.0",
    )


def generate_data(cache_dir: Path) -> Path:
    """Run benchmark and return the base/ directory containing results."""
    from quartumse import BenchmarkMode, BenchmarkSuiteConfig, run_benchmark_suite

    qc = build_h2_circuit()
    obs_set = build_merged_observable_set()
    loc_map = {o.observable_id: o.locality for o in obs_set.observables}

    config = BenchmarkSuiteConfig(
        mode=BenchmarkMode.BASIC,  # fastest mode — we only need raw shots
        n_shots_grid=[N_BUDGET],
        n_replicates=N_REPLICATES,
        seed=42,
        epsilon=0.05,
        delta=0.05,
        shadows_protocol_id="classical_shadows_v0",
        baseline_protocol_id="direct_grouped",
        output_base_dir=str(cache_dir),
    )

    t0 = time.perf_counter()
    result = run_benchmark_suite(
        circuit=qc,
        observable_set=obs_set,
        circuit_id="C-H2_pilot",
        config=config,
        locality_map=loc_map,
    )
    elapsed = time.perf_counter() - t0
    print(f"Benchmark completed in {elapsed:.1f}s")
    return result.output_dir / "base"


def find_or_generate(data_dir: str | None) -> Path:
    """Return path to the base/ directory with raw_shots, long_form, etc."""
    if data_dir is not None:
        p = Path(data_dir)
        # Accept either the base/ dir directly or its parent
        if (p / "raw_shots" / "data.parquet").exists():
            return p
        if (p / "base" / "raw_shots" / "data.parquet").exists():
            return p / "base"
        sys.exit(f"ERROR: no raw_shots/data.parquet found under {p}")

    # Look for any cached run
    cache_root = Path("pilot_analysis_cache")
    for child in sorted(cache_root.glob("C-H2_pilot_*")) if cache_root.exists() else []:
        base = child / "base"
        if (base / "raw_shots" / "data.parquet").exists():
            print(f"Using cached data: {base}")
            return base

    print("No cached data found — generating benchmark …")
    return generate_data(cache_root)


# -- Step 1: Build observable registry ----------------------------------------
def build_obs_registry() -> dict[str, dict]:
    """Map observable_id → {pauli_string, coefficient, support, locality}."""
    obs_set = build_merged_observable_set()
    registry: dict[str, dict] = {}
    for obs in obs_set.observables:
        registry[obs.observable_id] = {
            "pauli_string": obs.pauli_string,
            "coefficient": obs.coefficient,
            "support": [i for i, c in enumerate(obs.pauli_string) if c != "I"],
            "locality": obs.locality,
        }
    return registry


def _safe_nanmean(values: list[float]) -> float:
    """nanmean that returns nan for all-nan / empty lists without warning."""
    a = np.array(values)
    valid = a[~np.isnan(a)]
    return float(valid.mean()) if len(valid) > 0 else np.nan


# -- Step 2: Re-estimation helpers --------------------------------------------
def _estimate_direct_observable(
    bitstrings: list[str],
    support: list[int],
    coefficient: float,
) -> tuple[float, float]:
    """Re-estimate a single observable from direct-measurement bitstrings.

    Returns (estimate, se).
    """
    n = len(bitstrings)
    if n == 0:
        return np.nan, np.nan

    eigenvalues = np.empty(n)
    for i, bs in enumerate(bitstrings):
        parity = sum(int(bs[q]) for q in support) % 2
        eigenvalues[i] = 1.0 - 2.0 * parity  # (-1)^parity

    est = coefficient * eigenvalues.mean()
    se = abs(coefficient) * eigenvalues.std(ddof=1) / math.sqrt(n) if n > 1 else np.nan
    return est, se


def _estimate_shadows_observable(
    outcomes: np.ndarray,
    bases: np.ndarray,
    pauli_string: str,
    coefficient: float,
    support: list[int],
) -> tuple[float, float]:
    """Re-estimate a single observable from classical-shadow data.

    outcomes : (n_shots, n_qubits) int array of measurement results
    bases    : (n_shots, n_qubits) int array, 0=Z 1=X 2=Y

    Returns (estimate, se).
    """
    n_shots = outcomes.shape[0]
    if n_shots == 0:
        return np.nan, np.nan

    k = len(support)
    required_bases = np.array([BASIS_MAP[pauli_string[i]] for i in support])

    # Boolean mask: shot is compatible iff ALL support qubits match
    compatible = np.all(bases[:, support] == required_bases[None, :], axis=1)

    # Per-shot estimator: 3^k * prod(1 - 2*b_i) if compatible, else 0
    sign_product = np.prod(1 - 2 * outcomes[:, support], axis=1)  # (n_shots,)
    per_shot = np.where(compatible, (3 ** k) * coefficient * sign_product, 0.0)

    est = per_shot.mean()
    se = per_shot.std(ddof=1) / math.sqrt(n_shots) if n_shots > 1 else np.nan
    return est, se


# -- Step 3: Core pilot loop -------------------------------------------------
def run_pilot_analysis(base_dir: Path):
    """Main analysis: load data, subsample, compare."""

    # -- Load data --------------------------------------------------------
    raw_df = pd.read_parquet(base_dir / "raw_shots" / "data.parquet")
    lf_df = pd.read_parquet(base_dir / "long_form" / "data.parquet")
    with open(base_dir / "ground_truth.json") as f:
        gt = json.load(f)
    truth = gt["truth_values"]

    print(f"Loaded: {len(raw_df)} raw-shot rows, {len(lf_df)} long-form rows, "
          f"{len(truth)} ground-truth values")

    # Auto-detect N: use the maximum N_total in the raw data
    n_budget = int(raw_df["N_total"].max())

    # Filter to n_budget
    raw_df = raw_df[raw_df["N_total"] == n_budget].copy()
    lf_df = lf_df[lf_df["N_total"] == n_budget].copy()

    protocols_present = sorted(raw_df["protocol_id"].unique())
    replicates = sorted(raw_df["replicate_id"].unique())
    n_reps = len(replicates)
    print(f"Protocols: {protocols_present}")
    print(f"Replicates: {n_reps}, N={n_budget}")

    # -- Build observable registry ----------------------------------------
    obs_reg = build_obs_registry()
    # Verify all long-form obs_ids are in registry
    lf_obs_ids = set(lf_df["observable_id"].unique())
    reg_ids = set(obs_reg.keys())
    matched = lf_obs_ids & reg_ids
    if not matched:
        sys.exit("ERROR: no observable IDs match between long-form and registry")
    if len(matched) < len(lf_obs_ids):
        print(f"  WARNING: {len(lf_obs_ids) - len(matched)} long-form obs not in registry")
    obs_ids = sorted(matched)
    print(f"Observables: {len(obs_ids)} matched")

    # -- Build group_id → [observable_id] mapping (for direct protocols) --
    group_to_obs: dict[str, list[str]] = {}
    for _, row in lf_df[lf_df["protocol_id"] == "direct_grouped"].drop_duplicates(
        subset=["observable_id", "group_id"]
    ).iterrows():
        oid = row["observable_id"]
        gid = row["group_id"]
        if oid in matched and gid is not None:
            group_to_obs.setdefault(gid, []).append(oid)

    print(f"Groups (direct_grouped): {len(group_to_obs)}")

    # -- Full-budget estimates from long-form (for comparison) ------------
    full_budget: dict[str, dict[str, dict]] = {}  # protocol → obs_id → {est, se, abs_err}
    for _, row in lf_df.iterrows():
        pid = row["protocol_id"]
        oid = row["observable_id"]
        rid = row["replicate_id"]
        if oid not in matched:
            continue
        full_budget.setdefault(pid, {}).setdefault(rid, {})[oid] = {
            "estimate": row["estimate"],
            "se": row["se"],
            "abs_err": row["abs_err"] if "abs_err" in row.index else abs(row["estimate"] - truth.get(oid, 0)),
        }

    # Compute full-budget per-protocol mean metrics (averaged over reps)
    full_metrics: dict[str, dict[str, float]] = {}
    for pid in protocols_present:
        maes, ses = [], []
        for rid in replicates:
            rep_data = full_budget.get(pid, {}).get(rid, {})
            if not rep_data:
                continue
            maes.append(np.mean([v["abs_err"] for v in rep_data.values()]))
            ses.append(np.mean([v["se"] for v in rep_data.values()]))
        full_metrics[pid] = {"mae": np.mean(maes), "se": np.mean(ses)}

    full_winner_mae = min(protocols_present, key=lambda p: full_metrics[p]["mae"])
    full_winner_se = min(protocols_present, key=lambda p: full_metrics[p]["se"])

    print(f"\n{'='*72}")
    print("FULL-BUDGET (N={}) RESULTS".format(n_budget))
    print(f"{'='*72}")
    print(f"{'Protocol':<28} {'Mean MAE':>10} {'Mean SE':>10}")
    print("-" * 50)
    for pid in protocols_present:
        tag = ""
        if pid == full_winner_mae:
            tag += " *MAE"
        if pid == full_winner_se:
            tag += " *SE"
        print(f"{SHORT.get(pid, pid):<28} {full_metrics[pid]['mae']:10.5f} "
              f"{full_metrics[pid]['se']:10.5f}{tag}")

    # -- Pre-parse raw shot data into fast lookup -------------------------
    # raw_lookup[(protocol_id, replicate_id, setting_id)] = (bitstrings, bases_or_None)
    print("\nParsing raw shot data …")
    raw_lookup: dict[tuple, tuple] = {}
    for _, row in raw_df.iterrows():
        key = (row["protocol_id"], row["replicate_id"], row["setting_id"])
        bs = json.loads(row["bitstrings"])
        mb = json.loads(row["measurement_bases"]) if pd.notna(row["measurement_bases"]) else None
        raw_lookup[key] = (bs, mb)
    print(f"  {len(raw_lookup)} raw-shot entries parsed")

    # -- Pilot loop -------------------------------------------------------
    # For each fraction, replicate, protocol: re-estimate, score, pick winner
    print(f"\n{'='*72}")
    print("PILOT ANALYSIS")
    print(f"{'='*72}\n")

    # Collect results per fraction
    all_results: list[dict] = []

    for frac in PILOT_FRACTIONS:
        n_pilot = int(frac * n_budget)
        # per-replicate: pilot_estimates[rep][protocol] = {obs_id: (est, se)}
        pilot_estimates: dict[int, dict[str, dict[str, tuple]]] = {}

        for rid in replicates:
            pilot_estimates[rid] = {}

            for pid in protocols_present:
                est_map: dict[str, tuple[float, float]] = {}

                if pid in ("direct_grouped", "direct_optimized"):
                    # Process each group
                    for gid, obs_list in group_to_obs.items():
                        key = (pid, rid, gid)
                        if key not in raw_lookup:
                            continue
                        bs_all, _ = raw_lookup[key]
                        n_sub = max(1, math.ceil(frac * len(bs_all)))
                        bs_sub = bs_all[:n_sub]

                        for oid in obs_list:
                            if oid not in obs_reg:
                                continue
                            info = obs_reg[oid]
                            est, se = _estimate_direct_observable(
                                bs_sub, info["support"], info["coefficient"]
                            )
                            est_map[oid] = (est, se)

                elif pid == "classical_shadows_v0":
                    key = (pid, rid, "shadows_random_local_clifford")
                    if key not in raw_lookup:
                        continue
                    bs_all, mb_all = raw_lookup[key]
                    n_sub = max(1, int(frac * len(bs_all)))

                    # Convert to arrays once
                    outcomes = np.array(
                        [[int(c) for c in s] for s in bs_all[:n_sub]], dtype=np.int8
                    )
                    bases = np.array(mb_all[:n_sub], dtype=np.int8)

                    for oid in obs_ids:
                        info = obs_reg[oid]
                        est, se = _estimate_shadows_observable(
                            outcomes, bases,
                            info["pauli_string"], info["coefficient"], info["support"],
                        )
                        est_map[oid] = (est, se)

                pilot_estimates[rid][pid] = est_map

        # -- Score each replicate -----------------------------------------
        rep_winners_mae: list[str] = []
        rep_winners_se: list[str] = []
        per_protocol_mae: dict[str, list[float]] = {p: [] for p in protocols_present}
        per_protocol_se: dict[str, list[float]] = {p: [] for p in protocols_present}

        for rid in replicates:
            for pid in protocols_present:
                emap = pilot_estimates[rid].get(pid, {})
                if not emap:
                    per_protocol_mae[pid].append(np.nan)
                    per_protocol_se[pid].append(np.nan)
                    continue
                abs_errs = [
                    abs(emap[oid][0] - truth[oid])
                    for oid in emap
                    if oid in truth and not np.isnan(emap[oid][0])
                ]
                ses = [
                    emap[oid][1]
                    for oid in emap
                    if not np.isnan(emap[oid][1])
                ]
                per_protocol_mae[pid].append(np.mean(abs_errs) if abs_errs else np.nan)
                per_protocol_se[pid].append(np.mean(ses) if ses else np.nan)

            # Pick winner for this replicate
            rep_mae = {p: per_protocol_mae[p][-1] for p in protocols_present}
            rep_se = {p: per_protocol_se[p][-1] for p in protocols_present}

            valid_mae = {p: v for p, v in rep_mae.items() if not np.isnan(v)}
            valid_se = {p: v for p, v in rep_se.items() if not np.isnan(v)}

            rep_winners_mae.append(
                min(valid_mae, key=valid_mae.get) if valid_mae else ""
            )
            rep_winners_se.append(
                min(valid_se, key=valid_se.get) if valid_se else ""
            )

        # -- Aggregate ----------------------------------------------------
        acc_mae = sum(1 for w in rep_winners_mae if w == full_winner_mae) / n_reps
        acc_se = sum(1 for w in rep_winners_se if w == full_winner_se) / n_reps

        # Mean regret (MAE): full-budget MAE of pilot-selected minus oracle
        regrets_mae = []
        for w in rep_winners_mae:
            if w and w in full_metrics:
                regrets_mae.append(full_metrics[w]["mae"] - full_metrics[full_winner_mae]["mae"])
        mean_regret_mae = np.mean(regrets_mae) if regrets_mae else np.nan

        regrets_se = []
        for w in rep_winners_se:
            if w and w in full_metrics:
                regrets_se.append(full_metrics[w]["se"] - full_metrics[full_winner_se]["se"])
        mean_regret_se = np.mean(regrets_se) if regrets_se else np.nan

        row_result = {
            "frac": frac,
            "n_pilot": n_pilot,
            "acc_mae": acc_mae,
            "acc_se": acc_se,
            "mean_regret_mae": mean_regret_mae,
            "mean_regret_se": mean_regret_se,
            "winners_mae": rep_winners_mae,
            "winners_se": rep_winners_se,
            "per_protocol_mae": {
                p: _safe_nanmean(per_protocol_mae[p]) for p in protocols_present
            },
            "per_protocol_se": {
                p: _safe_nanmean(per_protocol_se[p]) for p in protocols_present
            },
        }
        all_results.append(row_result)

    # -- Print summary table ----------------------------------------------
    print(f"Full-budget winner (MAE): {SHORT.get(full_winner_mae, full_winner_mae)} "
          f"({full_metrics[full_winner_mae]['mae']:.5f})")
    print(f"Full-budget winner (SE):  {SHORT.get(full_winner_se, full_winner_se)} "
          f"({full_metrics[full_winner_se]['se']:.5f})")

    # -- Table 1: Selection accuracy by pilot fraction --------------------
    print(f"\n{'-'*72}")
    print("Selection Accuracy (MAE criterion)")
    print(f"{'-'*72}")
    print(f"{'Pilot%':>7} {'Shots':>6}  {'Winner distribution':<36} {'Acc':>5} {'Regret':>8}")
    print("-" * 72)

    for r in all_results:
        # Count winners
        from collections import Counter
        counts = Counter(r["winners_mae"])
        dist_parts = [f"{SHORT.get(p,p)}:{c}" for p, c in counts.most_common()]
        dist_str = ", ".join(dist_parts)
        print(f"{r['frac']:6.0%} {r['n_pilot']:6d}  {dist_str:<36} "
              f"{r['acc_mae']:5.0%} {r['mean_regret_mae']:8.5f}")

    print(f"\n{'-'*72}")
    print("Selection Accuracy (SE criterion)")
    print(f"{'-'*72}")
    print(f"{'Pilot%':>7} {'Shots':>6}  {'Winner distribution':<36} {'Acc':>5} {'Regret':>8}")
    print("-" * 72)

    for r in all_results:
        from collections import Counter
        counts = Counter(r["winners_se"])
        dist_parts = [f"{SHORT.get(p,p)}:{c}" for p, c in counts.most_common()]
        dist_str = ", ".join(dist_parts)
        print(f"{r['frac']:6.0%} {r['n_pilot']:6d}  {dist_str:<36} "
              f"{r['acc_se']:5.0%} {r['mean_regret_se']:8.5f}")

    # -- Table 2: Per-protocol metrics at each pilot level ----------------
    print(f"\n{'-'*72}")
    print("Per-Protocol Metrics at Each Pilot Level")
    print(f"{'-'*72}")
    header = f"{'Pilot%':>7}"
    for pid in protocols_present:
        name = SHORT.get(pid, pid)
        header += f"  {name+' MAE':>14} {name+' SE':>12}"
    print(header)
    print("-" * len(header))

    for r in all_results:
        line = f"{r['frac']:6.0%}"
        for pid in protocols_present:
            mae_val = r["per_protocol_mae"].get(pid, np.nan)
            se_val = r["per_protocol_se"].get(pid, np.nan)
            line += f"  {mae_val:14.5f} {se_val:12.5f}"
        print(line)

    # Full budget row for comparison
    line = f"{'100%':>7}"
    for pid in protocols_present:
        line += f"  {full_metrics[pid]['mae']:14.5f} {full_metrics[pid]['se']:12.5f}"
    print(line + "  (full budget)")

    # -- Verification: compare 100% re-estimate to stored values ----------
    print(f"\n{'-'*72}")
    print("Verification: 100% Re-estimate vs Stored Full-Budget")
    print(f"{'-'*72}")

    # Run re-estimation at fraction=1.0 for one replicate
    rid0 = replicates[0]
    for pid in protocols_present:
        est_map: dict[str, tuple[float, float]] = {}

        if pid in ("direct_grouped", "direct_optimized"):
            for gid, obs_list in group_to_obs.items():
                key = (pid, rid0, gid)
                if key not in raw_lookup:
                    continue
                bs_all, _ = raw_lookup[key]
                for oid in obs_list:
                    if oid not in obs_reg:
                        continue
                    info = obs_reg[oid]
                    est, se = _estimate_direct_observable(
                        bs_all, info["support"], info["coefficient"]
                    )
                    est_map[oid] = (est, se)

        elif pid == "classical_shadows_v0":
            key = (pid, rid0, "shadows_random_local_clifford")
            if key not in raw_lookup:
                continue
            bs_all, mb_all = raw_lookup[key]
            outcomes = np.array(
                [[int(c) for c in s] for s in bs_all], dtype=np.int8
            )
            bases = np.array(mb_all, dtype=np.int8)
            for oid in obs_ids:
                info = obs_reg[oid]
                est, se = _estimate_shadows_observable(
                    outcomes, bases,
                    info["pauli_string"], info["coefficient"], info["support"],
                )
                est_map[oid] = (est, se)

        # Compare to stored
        stored = full_budget.get(pid, {}).get(rid0, {})
        diffs_est, diffs_se = [], []
        for oid in est_map:
            if oid in stored:
                diffs_est.append(abs(est_map[oid][0] - stored[oid]["estimate"]))
                if not np.isnan(est_map[oid][1]) and not np.isnan(stored[oid]["se"]):
                    diffs_se.append(abs(est_map[oid][1] - stored[oid]["se"]))

        if diffs_est:
            print(f"  {SHORT.get(pid, pid):<12}: "
                  f"max|est diff|={max(diffs_est):.2e}, "
                  f"mean|est diff|={np.mean(diffs_est):.2e}, "
                  f"max|SE diff|={max(diffs_se):.2e}" if diffs_se else "")
        else:
            print(f"  {SHORT.get(pid, pid):<12}: no overlapping observables to compare")

    print("\nDone.")


# -- CLI ----------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post-hoc pilot analysis from raw shots")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Path to existing benchmark base/ directory with raw_shots/",
    )
    args = parser.parse_args()

    base_dir = find_or_generate(args.data_dir)
    run_pilot_analysis(base_dir)
