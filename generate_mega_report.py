"""Generate a self-contained HTML mega-report for all QuartumSE benchmark results.

Discovers and loads analysis.json from merged + noise benchmark runs,
computes Bayesian P(best) from long_form parquet data, optionally runs
Bayesian adaptive protocol selection on compatible circuits, and
produces a single mega_benchmark_report.html.

Usage:
    python generate_mega_report.py
    python generate_mega_report.py --skip-adaptive   # skip slow Bayesian adaptive
    python generate_mega_report.py --skip-pbest      # skip P(best) from parquet
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
BENCHMARK_DIR = ROOT / "notebooks" / "benchmark_results"
NOISE_DIR = ROOT / "notebooks" / "benchmark_results_noise"

CIRCUITS = {
    "S-BELL-2":  {"family": "Stabilizer",    "qubits": 2},
    "S-BELL-3":  {"family": "Stabilizer",    "qubits": 3},
    "S-GHZ-4":   {"family": "Stabilizer",    "qubits": 4},
    "S-GHZ-5":   {"family": "Stabilizer",    "qubits": 5},
    "S-ISING-4": {"family": "Stabilizer",    "qubits": 4},
    "S-ISING-6": {"family": "Stabilizer",    "qubits": 6},
    "C-H2":      {"family": "Chemistry",     "qubits": 4},
    "C-LiH":     {"family": "Chemistry",     "qubits": 4},
    "O-QAOA-5":  {"family": "Optimization",  "qubits": 5},
    "O-QAOA-7":  {"family": "Optimization",  "qubits": 7},
    "M-PHASE-3": {"family": "Metrology",     "qubits": 3},
    "M-PHASE-4": {"family": "Metrology",     "qubits": 4},
}

NOISE_PROFILES = ["ideal", "readout_1e-2", "depol_low"]

SHORT = {
    "direct_grouped": "grouped",
    "direct_optimized": "optimized",
    "classical_shadows_v0": "shadows",
}

# Bayesian adaptive directories: circuit_key -> (base_dir_name, prefix in dir name)
ADAPTIVE_CIRCUITS = {
    "C-H2":   ("pilot_analysis_noise",      "C-H2"),
    "S-GHZ-4": ("pilot_analysis_noise_ghz",  "GHZ4"),
    "S-GHZ-5": ("pilot_analysis_noise_ghz5", "GHZ5"),
}


# ---------------------------------------------------------------------------
# Data discovery
# ---------------------------------------------------------------------------

def _parse_timestamp(dirname: str) -> str | None:
    """Extract YYYYMMDD_HHMMSS timestamp from a run directory name."""
    m = re.search(r"(\d{8}_\d{6})_", dirname)
    return m.group(1) if m else None


def find_latest_run(
    base_dir: Path,
    prefix: str,
    require_analysis: bool = True,
) -> Path | None:
    """Find the latest run directory matching prefix under base_dir."""
    if not base_dir.exists():
        return None
    candidates = []
    for d in base_dir.iterdir():
        if d.is_dir() and d.name.startswith(prefix):
            ts = _parse_timestamp(d.name)
            if ts is None:
                continue
            if require_analysis and not (d / "analysis.json").exists():
                continue
            candidates.append((ts, d))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def discover_all_runs() -> dict:
    """Discover latest merged + noise runs for every circuit.

    Returns dict[circuit_id] -> {
        "merged": Path | None,
        "ideal": Path | None,
        "readout_1e-2": Path | None,
        "depol_low": Path | None,
    }
    """
    result = {}
    for cid in CIRCUITS:
        entry = {"merged": None}
        # Merged
        entry["merged"] = find_latest_run(BENCHMARK_DIR, f"{cid}__merged_")
        # Noise profiles
        for profile in NOISE_PROFILES:
            entry[profile] = find_latest_run(
                NOISE_DIR / profile, f"{cid}__{profile}_"
            )
        result[cid] = entry
    return result


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_analysis(run_dir: Path) -> dict | None:
    """Load analysis.json from a run directory."""
    fp = run_dir / "analysis.json"
    if not fp.exists():
        return None
    with open(fp) as f:
        return json.load(f)


def load_long_form(run_dir: Path) -> pd.DataFrame | None:
    """Load long_form/data.parquet from a run's base/ directory."""
    fp = run_dir / "base" / "long_form" / "data.parquet"
    if not fp.exists():
        return None
    # Try pyarrow first, fall back to fastparquet (pyarrow has version issues)
    for engine in ("pyarrow", "fastparquet"):
        try:
            return pd.read_parquet(fp, engine=engine)
        except Exception:
            continue
    return None


def load_ground_truth(run_dir: Path) -> dict | None:
    """Load ground_truth.json from a run's base/ directory."""
    fp = run_dir / "base" / "ground_truth.json"
    if not fp.exists():
        return None
    with open(fp) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Bayesian P(best) from long_form data
# ---------------------------------------------------------------------------

def compute_p_best_from_longform(
    lf_df: pd.DataFrame,
    gt_dict: dict,
    n_mc: int = 10_000,
    seed: int = 42,
) -> dict:
    """Compute P(best protocol) at each shot budget from long-form data.

    Returns dict[N_total -> dict[protocol_id -> P(best)]].
    """
    truth = gt_dict.get("truth_values", {})
    rng = np.random.default_rng(seed)

    # If abs_err is present use it; otherwise compute from estimate + truth
    if "abs_err" not in lf_df.columns:
        lf_df = lf_df.copy()
        lf_df["abs_err"] = lf_df.apply(
            lambda r: abs(r["estimate"] - truth.get(r["observable_id"], np.nan)),
            axis=1,
        )

    result = {}
    for n_total, grp_n in lf_df.groupby("N_total"):
        # MAE per (protocol, replicate)
        mae_df = (
            grp_n.groupby(["protocol_id", "replicate_id"])["abs_err"]
            .mean()
            .reset_index()
            .rename(columns={"abs_err": "mae"})
        )

        protocols = sorted(mae_df["protocol_id"].unique())
        n_protos = len(protocols)
        draws = np.empty((n_mc, n_protos))

        for j, pid in enumerate(protocols):
            maes = mae_df.loc[mae_df["protocol_id"] == pid, "mae"].values
            m = len(maes)
            if m < 2:
                draws[:, j] = (
                    rng.standard_t(df=1, size=n_mc) * 10
                    + (maes.mean() if m > 0 else 1.0)
                )
                continue
            x_bar = maes.mean()
            s = maes.std(ddof=1) / math.sqrt(m)
            df = m - 1
            draws[:, j] = rng.standard_t(df=df, size=n_mc) * s + x_bar

        best_idx = draws.argmin(axis=1)
        counts = np.bincount(best_idx, minlength=n_protos)
        p_best = {pid: float(counts[j] / n_mc) for j, pid in enumerate(protocols)}
        result[int(n_total)] = p_best

    return result



# ---------------------------------------------------------------------------
# Extended metrics: percentile + locality breakdown
# ---------------------------------------------------------------------------

def compute_extended_metrics(lf_df: pd.DataFrame, gt_dict: dict) -> dict:
    """Compute percentile and locality breakdown metrics from long-form data.

    Returns {"percentiles": {...}, "locality": {...}} where:
      - percentiles[metric_name] = {protocol_id: value, ..., "winner": pid}
      - locality[weight] = {"n_obs": int, protocols: {pid: {"mean": .., "median": .., "max": ..}}, "winner": pid}
    """
    truth = gt_dict.get("truth_values", {})

    # Ensure se column exists
    if "se" not in lf_df.columns:
        return {"percentiles": {}, "locality": {}}

    # Filter to max N_total
    max_n = lf_df["N_total"].max()
    df = lf_df[lf_df["N_total"] == max_n].copy()

    if df.empty:
        return {"percentiles": {}, "locality": {}}

    # --- Percentile metrics ---
    # Mean SE across replicates per (protocol, observable)
    per_obs = (
        df.groupby(["protocol_id", "observable_id"])["se"]
        .mean()
        .reset_index()
        .rename(columns={"se": "mean_se"})
    )

    protocols = sorted(per_obs["protocol_id"].unique())
    metric_names = ["mean", "p25", "median", "p75", "max"]
    percentiles_result = {"max_n": int(max_n), "protocols": protocols, "metrics": {}}

    for pid in protocols:
        vals = per_obs.loc[per_obs["protocol_id"] == pid, "mean_se"].values
        if len(vals) == 0:
            continue
        percentiles_result["metrics"].setdefault("mean", {})[pid] = float(np.mean(vals))
        percentiles_result["metrics"].setdefault("p25", {})[pid] = float(np.percentile(vals, 25))
        percentiles_result["metrics"].setdefault("median", {})[pid] = float(np.median(vals))
        percentiles_result["metrics"].setdefault("p75", {})[pid] = float(np.percentile(vals, 75))
        percentiles_result["metrics"].setdefault("max", {})[pid] = float(np.max(vals))

    # Determine winner (lowest value) at each metric level
    for mname in metric_names:
        mdata = percentiles_result["metrics"].get(mname, {})
        if mdata:
            winner = min(mdata, key=mdata.get)
            mdata["_winner"] = winner

    # --- Locality breakdown ---
    locality_result = {}
    has_locality = (
        "locality" in df.columns
        and df["locality"].notna().any()
        and (df["locality"] != 0).any()
    )

    if has_locality:
        # Mean SE across replicates per (protocol, locality, observable)
        per_obs_loc = (
            df.groupby(["protocol_id", "locality", "observable_id"])["se"]
            .mean()
            .reset_index()
            .rename(columns={"se": "mean_se"})
        )

        for weight, grp in per_obs_loc.groupby("locality"):
            weight_int = int(weight)
            n_obs = grp["observable_id"].nunique()
            proto_stats = {}
            for pid in protocols:
                pvals = grp.loc[grp["protocol_id"] == pid, "mean_se"].values
                if len(pvals) == 0:
                    continue
                proto_stats[pid] = {
                    "mean": float(np.mean(pvals)),
                    "median": float(np.median(pvals)),
                    "max": float(np.max(pvals)),
                }
            # Winner by mean SE
            if proto_stats:
                winner = min(proto_stats, key=lambda p: proto_stats[p]["mean"])
            else:
                winner = None
            locality_result[weight_int] = {
                "n_obs": n_obs,
                "protocols": proto_stats,
                "winner": winner,
            }

    return {"percentiles": percentiles_result, "locality": locality_result}


# ---------------------------------------------------------------------------
# Bayesian adaptive protocol selection (3 circuits)
# ---------------------------------------------------------------------------

def run_bayesian_adaptive_for_report(skip: bool = False) -> dict:
    """Run Bayesian adaptive simulation on compatible circuits.

    Returns dict[circuit_id][noise_profile] -> adaptive_results dict, or
    empty dict if skipped / unavailable.
    """
    if skip:
        return {}

    try:
        sys.path.insert(0, str(ROOT / "src"))
        sys.path.insert(0, str(ROOT))
        from bayesian_adaptive_protocol import load_and_parse, simulate_one_replicate
        from bayesian_adaptive_protocol import bayesian_p_best as _bp  # noqa: F401
    except ImportError as e:
        print(f"  [WARN] Cannot import bayesian_adaptive_protocol: {e}")
        return {}

    results = {}
    thresholds = [0.80, 0.90, 0.95, 0.99]

    for cid, (base_dir_name, prefix) in ADAPTIVE_CIRCUITS.items():
        results[cid] = {}
        for profile in NOISE_PROFILES:
            pdir = ROOT / base_dir_name / profile
            run_dir = find_latest_run(pdir, f"{prefix}__{profile}_", require_analysis=False)
            if run_dir is None:
                run_dir = find_latest_run(pdir, f"{prefix}_", require_analysis=False)
            if run_dir is None:
                continue

            base = run_dir / "base"
            if not (base / "raw_shots" / "data.parquet").exists():
                if (run_dir / "raw_shots" / "data.parquet").exists():
                    base = run_dir
                else:
                    continue

            print(f"  Bayesian adaptive: {cid} / {profile} ...")
            try:
                data = load_and_parse(base)
            except Exception as e:
                print(f"    [WARN] Failed to load {base}: {e}")
                continue

            protocols = data["protocols"]
            replicates = data["replicates"]
            n_budget = data["n_budget"]
            full_mae = data["full_mae"]
            K = len(protocols)

            # Oracle
            oracle_mean_mae = {}
            for pid in protocols:
                maes = [full_mae[pid][r] for r in replicates if r in full_mae[pid]]
                oracle_mean_mae[pid] = float(np.mean(maes)) if maes else np.nan
            oracle_protocol = min(oracle_mean_mae, key=oracle_mean_mae.get)

            threshold_results = []
            for thresh in thresholds:
                rng = np.random.default_rng(42)
                rep_results = []
                for rid in replicates:
                    res = simulate_one_replicate(
                        data["raw_lookup"], rid, protocols,
                        data["obs_registry"], data["obs_ids"],
                        data["group_to_obs"], data["ground_truth"],
                        n_budget, 200, thresh, 10000, rng,
                    )
                    res["replicate_id"] = rid
                    res["oracle_mae"] = full_mae.get(oracle_protocol, {}).get(rid, np.nan)
                    res["correct"] = (res["selected_protocol"] == oracle_protocol)
                    rep_results.append(res)

                n_reps = len(replicates)
                accuracy = sum(1 for r in rep_results if r["correct"]) / max(n_reps, 1)
                commit_steps = [r["committed_step"] for r in rep_results]
                expl_shots = [r["total_exploration"] for r in rep_results]
                final_maes = [r["final_mae"] for r in rep_results]
                oracle_maes = [r["oracle_mae"] for r in rep_results]

                threshold_results.append({
                    "threshold": thresh,
                    "mean_commit_step": float(np.mean(commit_steps)),
                    "mean_expl_shots": float(np.mean(expl_shots)),
                    "accuracy": accuracy,
                    "mean_adaptive_mae": float(np.mean(final_maes)),
                    "mean_oracle_mae": float(np.mean(oracle_maes)),
                    "mean_regret": float(np.mean(final_maes) - np.mean(oracle_maes)),
                    "rep_results": rep_results,
                })

            # Trajectory from the 95% threshold
            idx95 = min(range(len(thresholds)), key=lambda i: abs(thresholds[i] - 0.95))
            trajectory = threshold_results[idx95]["rep_results"][0].get("trajectory", [])

            results[cid][profile] = {
                "oracle_protocol": SHORT.get(oracle_protocol, oracle_protocol),
                "oracle_mae": oracle_mean_mae[oracle_protocol],
                "n_budget": n_budget,
                "threshold_results": threshold_results,
                "trajectory": trajectory,
                "protocols": [SHORT.get(p, p) for p in protocols],
            }

    return results


# ---------------------------------------------------------------------------
# HTML generation helpers
# ---------------------------------------------------------------------------

def _esc(s) -> str:
    """HTML-escape a string."""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _fmt(v, fmt=".4f") -> str:
    """Format a number or return '—' for None/NaN."""
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "&mdash;"
    return format(v, fmt)


def _ratio_color(ratio: float | None) -> str:
    """Return CSS color class for a shadows-vs-baseline ratio."""
    if ratio is None or math.isnan(ratio):
        return "#94a3b8"  # gray
    if ratio < 0.90:
        return "#16a34a"  # green — shadows much better
    if ratio < 0.98:
        return "#65a30d"  # lime
    if ratio < 1.02:
        return "#d97706"  # amber — roughly equal
    return "#dc2626"  # red — baseline better


def _winner_tag(winner: str | None) -> str:
    """Return HTML tag for winner protocol."""
    if winner is None:
        return '<span class="tag" style="background:#f1f5f9;color:#64748b;">N/A</span>'
    short = SHORT.get(winner, winner)
    colors = {
        "shadows": ("var(--green-bg)", "var(--green)"),
        "optimized": ("var(--accent-light)", "var(--accent)"),
        "grouped": ("var(--amber-bg)", "var(--amber)"),
    }
    bg, fg = colors.get(short, ("#f1f5f9", "#64748b"))
    return f'<span class="tag" style="background:{bg};color:{fg};">{_esc(short)}</span>'


# ---------------------------------------------------------------------------
# HTML sections
# ---------------------------------------------------------------------------

def _section_executive_summary(all_data: dict, adaptive_data: dict) -> str:
    """Section 1: Executive summary."""
    n_circuits = len(all_data)
    n_runs = sum(
        1 for cid in all_data for cond in all_data[cid]
        if all_data[cid][cond].get("analysis") is not None
    )
    # Count shadows wins
    shadows_wins = 0
    total_compared = 0
    ratios = []
    for cid in all_data:
        for cond in all_data[cid]:
            a = all_data[cid][cond].get("analysis")
            if a and "summary" in a:
                s = a["summary"]
                r = s.get("shadows_vs_baseline_ratio")
                if r is not None and not math.isnan(r):
                    ratios.append(r)
                    total_compared += 1
                    if r < 1.0:
                        shadows_wins += 1

    mean_ratio = np.mean(ratios) if ratios else float("nan")
    median_ratio = np.median(ratios) if ratios else float("nan")

    return f"""
    <div class="card card-accent">
      <h3>Executive Summary</h3>
      <p><strong>Report generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
      <p><strong>Circuits benchmarked:</strong> {n_circuits} &nbsp;|&nbsp;
         <strong>Total analysis runs:</strong> {n_runs}</p>
      <p><strong>Conditions:</strong> merged (noiseless baseline) + 3 noise profiles
         (ideal simulator, readout 1e-2, depolarizing low)</p>
      <hr style="margin:0.8rem 0;border-color:var(--border);">
      <p><strong>Shadows vs. grouped baseline ratio:</strong>
         mean = <code>{_fmt(mean_ratio)}</code>,
         median = <code>{_fmt(median_ratio)}</code></p>
      <p>Shadows wins in <strong>{shadows_wins}/{total_compared}</strong> conditions
         (ratio &lt; 1.0 means shadows has lower MAE).</p>
      <p>{"Classical shadows generally outperforms the grouped direct baseline across most circuits and noise conditions."
         if shadows_wins >= 0.65 * total_compared
         else "Performance is mixed — protocol advantage depends on circuit and noise profile."}</p>
    </div>
    """


def _overview_cell(analysis: dict | None, ext: dict | None) -> str:
    """Build a single overview cell with median winner + median/max SE ratios.

    Prefers extended-metrics (percentile) data when available, falls back
    to analysis.json summary.
    """
    pct = (ext or {}).get("percentiles", {})
    metrics = pct.get("metrics", {})
    protocols = pct.get("protocols", [])

    # Try to get shadows SE at median and max from extended metrics
    median_m = metrics.get("median", {})
    max_m = metrics.get("max", {})
    shadows_pid = next((p for p in protocols if SHORT.get(p, p) == "shadows"), None)
    grouped_pid = next((p for p in protocols if SHORT.get(p, p) == "grouped"), None)

    if shadows_pid and grouped_pid and shadows_pid in median_m and grouped_pid in median_m:
        median_winner = median_m.get("_winner")
        median_ratio = median_m[shadows_pid] / median_m[grouped_pid] if median_m[grouped_pid] else None
        max_ratio = (
            max_m.get(shadows_pid, 0) / max_m[grouped_pid]
            if grouped_pid in max_m and max_m[grouped_pid]
            else None
        )
        median_color = _ratio_color(median_ratio)
        max_color = _ratio_color(max_ratio)
        return (
            f'<td style="text-align:center;">'
            f'{_winner_tag(median_winner)}<br>'
            f'<small style="color:{median_color};font-weight:600;">'
            f'med {_fmt(median_ratio, ".3f")}</small> '
            f'<small style="color:{max_color};">'
            f'max {_fmt(max_ratio, ".3f")}</small></td>'
        )

    # Fallback: analysis.json summary
    if analysis and "summary" in analysis:
        s = analysis["summary"]
        winner = s.get("winner_at_max_n")
        ratio = s.get("shadows_vs_baseline_ratio")
        color = _ratio_color(ratio)
        return (
            f'<td style="text-align:center;">'
            f'{_winner_tag(winner)}<br>'
            f'<small style="color:{color};font-weight:600;">'
            f'{_fmt(ratio, ".3f")}</small></td>'
        )

    return '<td style="text-align:center;color:var(--muted);">&mdash;</td>'


def _section_overview_table(all_data: dict, extended_metrics: dict | None = None) -> str:
    """Section 2: Circuit overview heatmap table."""
    if extended_metrics is None:
        extended_metrics = {}
    conditions = ["merged"] + NOISE_PROFILES
    cond_labels = {
        "merged": "Merged",
        "ideal": "Ideal",
        "readout_1e-2": "Readout",
        "depol_low": "Depol",
    }
    rows = []
    for cid in CIRCUITS:
        info = CIRCUITS[cid]
        cells = f'<td><strong>{_esc(cid)}</strong></td>'
        cells += f'<td>{_esc(info["family"])}</td>'
        cells += f'<td class="num">{info["qubits"]}</td>'
        for cond in conditions:
            entry = all_data.get(cid, {}).get(cond, {})
            a = entry.get("analysis")
            ext = extended_metrics.get(cid, {}).get(cond)
            cells += _overview_cell(a, ext)
        rows.append(f"<tr>{cells}</tr>")

    return f"""
    <h2>2. Circuit Overview</h2>
    <p>Median-SE winner and shadows/grouped SE ratios at maximum shot budget.
       <em>med</em> = median SE ratio, <em>max</em> = max SE ratio.
       Ratio &lt; 1 means shadows outperforms the grouped baseline.</p>
    <div style="overflow-x:auto;">
    <table>
      <thead><tr>
        <th>Circuit</th><th>Family</th><th>Qubits</th>
        {"".join(f'<th style="text-align:center;">{cond_labels[c]}</th>' for c in conditions)}
      </tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
    </div>
    """


def _percentile_comparison_table(ext_by_cond: dict) -> str:
    """Generate percentile comparison table across conditions."""
    cond_labels = {"merged": "Merged", "ideal": "Ideal", "readout_1e-2": "Readout", "depol_low": "Depol"}
    metric_labels = {"mean": "Mean SE", "p25": "P25 SE", "median": "Median SE", "p75": "P75 SE", "max": "Max SE"}
    metric_order = ["mean", "p25", "median", "p75", "max"]

    # Collect all protocols across conditions
    all_protos = set()
    for cond_ext in ext_by_cond.values():
        pct = cond_ext.get("percentiles", {})
        all_protos.update(pct.get("protocols", []))
    if not all_protos:
        return ""
    proto_list = sorted(all_protos, key=lambda p: SHORT.get(p, p))

    header = "<tr><th>Condition</th><th class='num'>N</th><th>Metric</th>"
    for pid in proto_list:
        header += f"<th class='num'>{_esc(SHORT.get(pid, pid))}</th>"
    header += "<th>Winner</th></tr>"

    rows = []
    for cond in ["merged"] + NOISE_PROFILES:
        cond_ext = ext_by_cond.get(cond, {})
        pct = cond_ext.get("percentiles", {})
        if not pct or not pct.get("metrics"):
            continue
        max_n = pct.get("max_n", "")
        for i, mname in enumerate(metric_order):
            mdata = pct["metrics"].get(mname, {})
            if not mdata:
                continue
            winner = mdata.get("_winner")
            # Show condition + N only on first row of each condition block
            if i == 0:
                cond_cell = f'<td rowspan="{len(metric_order)}">{cond_labels.get(cond, cond)}</td>'
                n_cell = f'<td rowspan="{len(metric_order)}" class="num">{max_n:,}</td>'
            else:
                cond_cell = ""
                n_cell = ""
            row = f"{cond_cell}{n_cell}<td>{metric_labels[mname]}</td>"
            for pid in proto_list:
                v = mdata.get(pid)
                bold = " font-weight:700;" if pid == winner else ""
                row += f'<td class="num" style="{bold}">{_fmt(v)}</td>'
            row += f"<td>{_winner_tag(winner)}</td>"
            rows.append(f"<tr>{row}</tr>")

    if not rows:
        return ""
    return (
        "<h4>Percentile Comparison at Max N</h4>"
        f"<table><thead>{header}</thead><tbody>{''.join(rows)}</tbody></table>"
    )


def _locality_breakdown_table(ext_by_cond: dict) -> str:
    """Generate locality (Pauli weight) breakdown table across conditions."""
    cond_labels = {"merged": "Merged", "ideal": "Ideal", "readout_1e-2": "Readout", "depol_low": "Depol"}

    # Collect all protocols and weights
    all_protos = set()
    all_weights = set()
    for cond_ext in ext_by_cond.values():
        loc = cond_ext.get("locality", {})
        for w, wdata in loc.items():
            all_weights.add(w)
            all_protos.update(wdata.get("protocols", {}).keys())
    if not all_protos or not all_weights:
        return ""
    proto_list = sorted(all_protos, key=lambda p: SHORT.get(p, p))
    weight_list = sorted(all_weights)

    header = "<tr><th>Condition</th><th class='num'>Weight</th><th class='num'># Obs</th>"
    for pid in proto_list:
        header += f"<th class='num'>{_esc(SHORT.get(pid, pid))} SE</th>"
    header += "<th>Winner</th></tr>"

    rows = []
    for cond in ["merged"] + NOISE_PROFILES:
        cond_ext = ext_by_cond.get(cond, {})
        loc = cond_ext.get("locality", {})
        if not loc:
            continue
        cond_weights = sorted(w for w in weight_list if w in loc)
        for i, w in enumerate(cond_weights):
            wdata = loc[w]
            # Show condition only on first row
            if i == 0:
                cond_cell = f'<td rowspan="{len(cond_weights)}">{cond_labels.get(cond, cond)}</td>'
            else:
                cond_cell = ""
            winner = wdata.get("winner")
            row = f'{cond_cell}<td class="num">{w}</td><td class="num">{wdata["n_obs"]}</td>'
            for pid in proto_list:
                pstats = wdata.get("protocols", {}).get(pid, {})
                v = pstats.get("mean")
                bold = " font-weight:700;" if pid == winner else ""
                row += f'<td class="num" style="{bold}">{_fmt(v)}</td>'
            row += f"<td>{_winner_tag(winner)}</td>"
            rows.append(f"<tr>{row}</tr>")

    if not rows:
        return ""
    return (
        "<h4>Locality Breakdown (by Pauli Weight)</h4>"
        "<p><small>Mean SE per protocol at each observable locality (Pauli weight). "
        "Classical shadows have 3<sup>k</sup> variance scaling, so advantage depends on weight.</small></p>"
        f"<table><thead>{header}</thead><tbody>{''.join(rows)}</tbody></table>"
    )


def _section_circuit_detail(cid: str, data_by_cond: dict, p_best_data: dict, ext_by_cond: dict | None = None) -> str:
    """Section 3: Per-circuit detail card (collapsible)."""
    if ext_by_cond is None:
        ext_by_cond = {}
    info = CIRCUITS[cid]
    parts = []
    cond_labels = {"merged": "Merged", "ideal": "Ideal", "readout_1e-2": "Readout", "depol_low": "Depol"}

    # Collect all protocols seen across conditions (needed by multiple sub-tables)
    all_protocols_seen = set()
    for cond, entry in data_by_cond.items():
        a = entry.get("analysis")
        if a and "task_analyses" in a and "task3_distribution" in a["task_analyses"]:
            dists = a["task_analyses"]["task3_distribution"]["base_results"].get("distributions", {})
            all_protocols_seen.update(dists.keys())
    proto_list = sorted(all_protocols_seen, key=lambda p: SHORT.get(p, p))

    # --- Percentile comparison at max N ---
    pct_html = _percentile_comparison_table(ext_by_cond)
    if pct_html:
        parts.append(pct_html)
    else:
        # Fallback: old-style protocol comparison from analysis.json
        parts.append("<h4>Protocol Comparison at Max N</h4>")
        header_row = "<tr><th>Condition</th><th>N</th>"
        for pid in proto_list:
            header_row += f"<th class='num'>{_esc(SHORT.get(pid, pid))} MAE</th>"
        header_row += "</tr>"
        table_rows = []
        for cond in ["merged"] + NOISE_PROFILES:
            entry = data_by_cond.get(cond, {})
            a = entry.get("analysis")
            if not a or "task_analyses" not in a:
                continue
            t3 = a["task_analyses"].get("task3_distribution", {}).get("base_results", {}).get("distributions", {})
            n_shots = a.get("n_shots_grid", [])
            max_n = max(n_shots) if n_shots else None
            row = f'<td>{cond_labels.get(cond, cond)}</td><td class="num">{_fmt(max_n, ".0f")}</td>'
            for pid in proto_list:
                pdist = t3.get(pid, {})
                if max_n and str(max_n) in pdist:
                    row += f'<td class="num">{_fmt(pdist[str(max_n)].get("mean"), ".5f")}</td>'
                elif max_n and max_n in pdist:
                    row += f'<td class="num">{_fmt(pdist[max_n].get("mean"), ".5f")}</td>'
                else:
                    row += '<td class="num">&mdash;</td>'
            table_rows.append(f"<tr>{row}</tr>")
        if table_rows:
            parts.append(f"<table><thead>{header_row}</thead><tbody>{''.join(table_rows)}</tbody></table>")

    # --- Locality breakdown ---
    loc_html = _locality_breakdown_table(ext_by_cond)
    if loc_html:
        parts.append(loc_html)

    # --- Interpolated N* ---
    parts.append("<h4>Interpolated N* (Power-Law Fit)</h4>")
    nstar_rows = []
    for cond in ["merged"] + NOISE_PROFILES:
        entry = data_by_cond.get(cond, {})
        a = entry.get("analysis")
        if not a or "interpolated_n_star" not in a:
            continue
        ns = a["interpolated_n_star"]
        row = f'<td>{cond_labels.get(cond, cond)}</td>'
        for pid in proto_list:
            pns = ns.get(pid, {})
            n_star = pns.get("n_star_interpolated")
            r2 = pns.get("r_squared")
            row += f'<td class="num">{_fmt(n_star, ".0f")}</td>'
            row += f'<td class="num">{_fmt(r2, ".4f")}</td>'
        nstar_rows.append(f"<tr>{row}</tr>")
    if nstar_rows:
        nstar_header = "<tr><th>Condition</th>"
        for pid in proto_list:
            nstar_header += f"<th class='num'>{_esc(SHORT.get(pid, pid))} N*</th><th class='num'>R&sup2;</th>"
        nstar_header += "</tr>"
        parts.append(f"<table><thead>{nstar_header}</thead><tbody>{''.join(nstar_rows)}</tbody></table>")

    # --- Crossover analysis ---
    parts.append("<h4>Crossover Analysis</h4>")
    cross_rows = []
    for cond in ["merged"] + NOISE_PROFILES:
        entry = data_by_cond.get(cond, {})
        a = entry.get("analysis")
        if not a or "crossover_analysis" not in a:
            continue
        ca = a["crossover_analysis"]
        row = (
            f'<td>{cond_labels.get(cond, cond)}</td>'
            f'<td class="num">{ca.get("n_observables", "—")}</td>'
            f'<td class="num">{_fmt(ca.get("a_win_fraction"), ".1%")}</td>'
            f'<td class="num">{_fmt(ca.get("b_win_fraction"), ".1%")}</td>'
            f'<td class="num">{_fmt(ca.get("crossover_fraction"), ".1%")}</td>'
        )
        cross_rows.append(f"<tr>{row}</tr>")
    if cross_rows:
        parts.append(
            "<table><thead><tr>"
            "<th>Condition</th><th class='num'>N Obs</th>"
            "<th class='num'>Shadows Wins</th><th class='num'>Baseline Wins</th>"
            "<th class='num'>Crossover</th>"
            "</tr></thead><tbody>" + "".join(cross_rows) + "</tbody></table>"
        )

    # --- Locality correlation ---
    parts.append("<h4>Locality Correlation</h4>")
    loc_rows = []
    for cond in ["merged"] + NOISE_PROFILES:
        entry = data_by_cond.get(cond, {})
        a = entry.get("analysis")
        if not a or "locality_analysis" not in a:
            continue
        la = a["locality_analysis"]
        row = f'<td>{cond_labels.get(cond, cond)}</td>'
        for pid in proto_list:
            pla = la.get(pid, {})
            corr = pla.get("locality_correlation")
            reg = pla.get("locality_regression", {})
            row += f'<td class="num">{_fmt(corr, ".3f")}</td>'
            row += f'<td class="num">{_fmt(reg.get("slope"), ".4f")}</td>'
        loc_rows.append(f"<tr>{row}</tr>")
    if loc_rows:
        loc_header = "<tr><th>Condition</th>"
        for pid in proto_list:
            loc_header += f"<th class='num'>{_esc(SHORT.get(pid, pid))} corr</th><th class='num'>slope</th>"
        loc_header += "</tr>"
        parts.append(f"<table><thead>{loc_header}</thead><tbody>{''.join(loc_rows)}</tbody></table>")

    # --- Bayesian P(best) ---
    pb = p_best_data.get(cid, {})
    if pb:
        parts.append("<h4>Bayesian P(best)</h4>")
        # Collect all shot budgets and protocols
        all_n = set()
        all_pb_protos = set()
        for cond_pb in pb.values():
            for n_total, proto_pb in cond_pb.items():
                all_n.add(n_total)
                all_pb_protos.update(proto_pb.keys())
        all_n = sorted(all_n)
        all_pb_protos = sorted(all_pb_protos, key=lambda p: SHORT.get(p, p))

        pb_header = "<tr><th>Condition</th><th class='num'>N</th>"
        for pid in all_pb_protos:
            pb_header += f"<th class='num'>P({_esc(SHORT.get(pid, pid))})</th>"
        pb_header += "</tr>"

        pb_rows = []
        for cond in ["merged"] + NOISE_PROFILES:
            cond_pb = pb.get(cond, {})
            for n_total in all_n:
                proto_pb = cond_pb.get(n_total, {})
                if not proto_pb:
                    continue
                row = f'<td>{cond_labels.get(cond, cond)}</td><td class="num">{n_total:,}</td>'
                for pid in all_pb_protos:
                    v = proto_pb.get(pid)
                    style = ""
                    if v is not None and v > 0.5:
                        style = ' style="font-weight:700;color:var(--green);"'
                    row += f'<td class="num"{style}>{_fmt(v, ".3f")}</td>'
                pb_rows.append(f"<tr>{row}</tr>")
        if pb_rows:
            parts.append(f"<table><thead>{pb_header}</thead><tbody>{''.join(pb_rows)}</tbody></table>")

    inner = "\n".join(parts)
    return f"""
    <details class="card">
      <summary style="cursor:pointer;font-weight:600;font-size:1.05rem;">
        {_esc(cid)} &mdash; {_esc(info['family'])} ({info['qubits']}q)
      </summary>
      <div style="padding-top:0.8rem;">
        {inner}
      </div>
    </details>
    """


def _section_noise_impact(all_data: dict) -> str:
    """Section 4: Noise impact analysis."""
    # Gather ratio per circuit per condition
    cond_labels = {"merged": "Merged", "ideal": "Ideal", "readout_1e-2": "Readout", "depol_low": "Depol"}
    conditions = ["merged"] + NOISE_PROFILES
    rows = []
    circuit_sensitivities = []

    for cid in CIRCUITS:
        ratios_for_cid = {}
        for cond in conditions:
            entry = all_data.get(cid, {}).get(cond, {})
            a = entry.get("analysis")
            if a and "summary" in a:
                r = a["summary"].get("shadows_vs_baseline_ratio")
                if r is not None and not math.isnan(r):
                    ratios_for_cid[cond] = r

        row = f'<td><strong>{_esc(cid)}</strong></td>'
        for cond in conditions:
            r = ratios_for_cid.get(cond)
            if r is not None:
                color = _ratio_color(r)
                row += f'<td class="num" style="color:{color};font-weight:600;">{_fmt(r, ".3f")}</td>'
            else:
                row += '<td class="num">&mdash;</td>'

        # Sensitivity: range of ratios
        if len(ratios_for_cid) >= 2:
            vals = list(ratios_for_cid.values())
            sensitivity = max(vals) - min(vals)
            circuit_sensitivities.append((cid, sensitivity))
            row += f'<td class="num">{_fmt(sensitivity, ".3f")}</td>'
        else:
            row += '<td class="num">&mdash;</td>'
        rows.append(f"<tr>{row}</tr>")

    # Winner stability
    winner_changes = []
    for cid in CIRCUITS:
        winners = set()
        for cond in conditions:
            entry = all_data.get(cid, {}).get(cond, {})
            a = entry.get("analysis")
            if a and "summary" in a:
                w = a["summary"].get("winner_at_max_n")
                if w:
                    winners.add(w)
        if len(winners) > 1:
            winner_changes.append(cid)

    stability_note = ""
    if winner_changes:
        stability_note = (
            f'<p><strong>Winner changes across conditions:</strong> '
            f'{", ".join(winner_changes)} — protocol advantage is noise-dependent '
            f'for these circuits.</p>'
        )
    else:
        stability_note = '<p>The winning protocol is consistent across all noise conditions for every circuit.</p>'

    # Most/least sensitive
    sens_note = ""
    if circuit_sensitivities:
        circuit_sensitivities.sort(key=lambda x: x[1], reverse=True)
        most = circuit_sensitivities[0]
        least = circuit_sensitivities[-1]
        sens_note = (
            f'<p><strong>Most noise-sensitive:</strong> {most[0]} (ratio range = {most[1]:.3f}) &nbsp;|&nbsp; '
            f'<strong>Least noise-sensitive:</strong> {least[0]} (ratio range = {least[1]:.3f})</p>'
        )

    return f"""
    <h2>4. Noise Impact Analysis</h2>
    {stability_note}
    {sens_note}
    <div style="overflow-x:auto;">
    <table>
      <thead><tr>
        <th>Circuit</th>
        {"".join(f'<th class="num">{cond_labels[c]}</th>' for c in conditions)}
        <th class="num">Sensitivity</th>
      </tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
    </div>
    <p><small>Sensitivity = max(ratio) &minus; min(ratio) across conditions.
       Higher values indicate the shadows advantage is more noise-dependent.</small></p>
    """




def _section_bayesian_adaptive(adaptive_data: dict) -> str:
    """Section 5: Bayesian adaptive protocol selection."""
    if not adaptive_data:
        return """
        <h2>5. Bayesian Adaptive Protocol Selection</h2>
        <div class="card card-amber">
          <p><strong>Skipped.</strong> Use <code>--skip-adaptive=false</code> or ensure
          <code>bayesian_adaptive_protocol.py</code> is available to include this section.</p>
        </div>
        """

    parts = []
    parts.append('<h2>5. Bayesian Adaptive Protocol Selection</h2>')
    parts.append(
        '<p>Bayesian adaptive simulation incrementally allocates shot batches and commits '
        'to a protocol when P(best) exceeds the threshold. Available for circuits with '
        'compatible raw shot data: C-H2, S-GHZ-4, S-GHZ-5.</p>'
    )

    cond_labels = {"ideal": "Ideal", "readout_1e-2": "Readout", "depol_low": "Depol"}

    for cid in ["C-H2", "S-GHZ-4", "S-GHZ-5"]:
        cid_data = adaptive_data.get(cid, {})
        if not cid_data:
            continue

        parts.append(f'<h3>{_esc(cid)}</h3>')

        for profile in NOISE_PROFILES:
            pdata = cid_data.get(profile)
            if not pdata:
                continue

            parts.append(f'<h4>{cond_labels.get(profile, profile)} (budget = {pdata["n_budget"]:,})</h4>')
            parts.append(f'<p>Oracle winner: <strong>{_esc(pdata["oracle_protocol"])}</strong> '
                         f'(MAE = {_fmt(pdata["oracle_mae"], ".5f")})</p>')

            # Threshold table
            t_rows = []
            for tr in pdata["threshold_results"]:
                acc_style = ' style="color:var(--green);font-weight:600;"' if tr["accuracy"] >= 0.9 else ""
                t_rows.append(
                    f'<tr>'
                    f'<td class="num">{tr["threshold"]:.0%}</td>'
                    f'<td class="num">{tr["mean_commit_step"]:.1f}</td>'
                    f'<td class="num">{tr["mean_expl_shots"]:,.0f}</td>'
                    f'<td class="num"{acc_style}>{tr["accuracy"]:.0%}</td>'
                    f'<td class="num">{_fmt(tr["mean_adaptive_mae"], ".5f")}</td>'
                    f'<td class="num">{_fmt(tr["mean_regret"], "+.5f")}</td>'
                    f'</tr>'
                )
            parts.append(
                '<table><thead><tr>'
                '<th class="num">Threshold</th>'
                '<th class="num">Commit Step</th>'
                '<th class="num">Expl. Shots</th>'
                '<th class="num">Accuracy</th>'
                '<th class="num">Adapt. MAE</th>'
                '<th class="num">Regret</th>'
                '</tr></thead><tbody>' + "".join(t_rows) + '</tbody></table>'
            )

            # Trajectory
            trajectory = pdata.get("trajectory", [])
            if trajectory:
                proto_names = pdata.get("protocols", [])
                traj_header = '<tr><th class="num">Step</th><th class="num">Shots/proto</th>'
                for pn in proto_names:
                    traj_header += f'<th class="num">P({_esc(pn)})</th>'
                traj_header += '<th>Committed?</th></tr>'
                traj_rows = []
                for rec in trajectory:
                    r = f'<td class="num">{rec["step"]}</td><td class="num">{rec["shots_per_proto"]:,}</td>'
                    for pn in proto_names:
                        key = f"p_best_{pn}"
                        v = rec.get(key, 0)
                        style = ' style="font-weight:700;color:var(--green);"' if v > 0.5 else ""
                        r += f'<td class="num"{style}>{v:.3f}</td>'
                    if rec.get("committed"):
                        r += '<td><span class="tag tag-green">COMMIT</span></td>'
                    else:
                        r += "<td></td>"
                    traj_rows.append(f"<tr>{r}</tr>")
                parts.append(
                    '<details><summary style="cursor:pointer;font-size:0.9rem;color:var(--muted);">'
                    'Show P(best) trajectory (replicate 0, 95% threshold)</summary>'
                    f'<table><thead>{traj_header}</thead><tbody>{"".join(traj_rows)}</tbody></table>'
                    '</details>'
                )

    return "\n".join(parts)


def _section_statistical_significance(all_data: dict) -> str:
    """Section 6: Aggregate p-value summary."""
    rows = []
    sig_count = 0
    total_count = 0

    cond_labels = {"merged": "Merged", "ideal": "Ideal", "readout_1e-2": "Readout", "depol_low": "Depol"}

    for cid in CIRCUITS:
        for cond in ["merged"] + NOISE_PROFILES:
            entry = all_data.get(cid, {}).get(cond, {})
            a = entry.get("analysis")
            if not a or "statistical_comparison" not in a:
                continue
            sc = a["statistical_comparison"]
            # Use highest N
            n_keys = sorted(sc.keys(), key=lambda x: int(x) if x.isdigit() else 0, reverse=True)
            if not n_keys:
                continue
            top_n = n_keys[0]
            comp = sc[top_n]
            dt = comp.get("difference_test", {})
            p_val = dt.get("p_value")
            effect = dt.get("effect_size")
            reject = dt.get("reject_null")
            ssf = comp.get("ssf_ci", {})
            ssf_est = ssf.get("estimate")
            ssf_lo = ssf.get("ci_low")
            ssf_hi = ssf.get("ci_high")

            if p_val is not None:
                total_count += 1
                if reject:
                    sig_count += 1

            tag = ""
            if reject:
                tag = '<span class="tag tag-green">sig</span>'
            elif p_val is not None:
                tag = '<span class="tag tag-amber">ns</span>'

            rows.append(
                f'<tr>'
                f'<td>{_esc(cid)}</td>'
                f'<td>{cond_labels.get(cond, cond)}</td>'
                f'<td class="num">{top_n}</td>'
                f'<td class="num">{_fmt(p_val, ".4f")}</td>'
                f'<td class="num">{_fmt(effect, ".4f")}</td>'
                f'<td style="text-align:center;">{tag}</td>'
                f'<td class="num">{_fmt(ssf_est, ".3f")}'
                f'{f" [{_fmt(ssf_lo, '.3f')}, {_fmt(ssf_hi, '.3f')}]" if ssf_lo is not None else ""}</td>'
                f'</tr>'
            )

    return f"""
    <h2>6. Statistical Significance</h2>
    <p>Bootstrap permutation test comparing shadows vs. grouped baseline at highest shot budget.
       <strong>{sig_count}/{total_count}</strong> comparisons are statistically significant
       (p &lt; 0.05).</p>
    <div style="overflow-x:auto;">
    <table>
      <thead><tr>
        <th>Circuit</th><th>Condition</th><th class="num">N</th>
        <th class="num">p-value</th><th class="num">Effect Size</th>
        <th style="text-align:center;">Sig?</th>
        <th class="num">SSF [95% CI]</th>
      </tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
    </div>
    <p><small>SSF = shadows scaling factor (SE_shadows / SE_baseline). Values &lt; 1 favor shadows.</small></p>
    """


# ---------------------------------------------------------------------------
# Main HTML assembly
# ---------------------------------------------------------------------------

def generate_html(
    all_data: dict,
    p_best_data: dict,
    adaptive_data: dict,
    extended_metrics: dict | None = None,
) -> str:
    """Assemble the full HTML report."""
    if extended_metrics is None:
        extended_metrics = {}

    # Per-circuit detail cards
    circuit_cards = []
    for cid in CIRCUITS:
        data_by_cond = all_data.get(cid, {})
        ext_by_cond = extended_metrics.get(cid, {})
        circuit_cards.append(_section_circuit_detail(cid, data_by_cond, p_best_data, ext_by_cond))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>QuartumSE Mega Benchmark Report</title>
<style>
  :root {{
    --bg: #f8f9fa;
    --card: #ffffff;
    --accent: #2563eb;
    --accent-light: #dbeafe;
    --text: #1e293b;
    --muted: #64748b;
    --border: #e2e8f0;
    --green: #16a34a;
    --green-bg: #dcfce7;
    --amber: #d97706;
    --amber-bg: #fef3c7;
    --red: #dc2626;
    --code-bg: #f1f5f9;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.65;
    padding: 2rem 1rem;
  }}
  .container {{ max-width: 1100px; margin: 0 auto; }}
  h1 {{
    font-size: 1.9rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
  }}
  .subtitle {{
    color: var(--muted);
    font-size: 1.05rem;
    margin-bottom: 2rem;
  }}
  h2 {{
    font-size: 1.35rem;
    font-weight: 600;
    margin: 2.5rem 0 1rem;
    padding-bottom: 0.4rem;
    border-bottom: 2px solid var(--accent);
    color: var(--accent);
  }}
  h3 {{
    font-size: 1.1rem;
    font-weight: 600;
    margin: 1.5rem 0 0.5rem;
  }}
  h4 {{
    font-size: 0.95rem;
    font-weight: 600;
    margin: 1.2rem 0 0.4rem;
    color: var(--muted);
  }}
  p, li {{ margin-bottom: 0.6rem; }}
  ul, ol {{ padding-left: 1.5rem; }}
  hr {{ border: none; border-top: 1px solid var(--border); margin: 1rem 0; }}
  .card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.5rem;
    margin: 1rem 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }}
  .card-accent {{ border-left: 4px solid var(--accent); }}
  .card-green {{ border-left: 4px solid var(--green); background: var(--green-bg); }}
  .card-amber {{ border-left: 4px solid var(--amber); background: var(--amber-bg); }}
  code {{
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    font-size: 0.88em;
    background: var(--code-bg);
    padding: 0.15em 0.4em;
    border-radius: 4px;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    margin: 0.8rem 0;
  }}
  th {{
    background: var(--accent);
    color: #fff;
    font-weight: 600;
    text-align: left;
    padding: 0.5rem 0.6rem;
    white-space: nowrap;
  }}
  th:first-child {{ border-radius: 6px 0 0 0; }}
  th:last-child {{ border-radius: 0 6px 0 0; }}
  td {{
    padding: 0.4rem 0.6rem;
    border-bottom: 1px solid var(--border);
  }}
  tr:nth-child(even) td {{ background: #f8fafc; }}
  tr:hover td {{ background: var(--accent-light); }}
  .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .tag {{
    display: inline-block;
    padding: 0.15em 0.55em;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
  }}
  .tag-green {{ background: var(--green-bg); color: var(--green); }}
  .tag-amber {{ background: var(--amber-bg); color: var(--amber); }}
  details summary {{ list-style: none; }}
  details summary::-webkit-details-marker {{ display: none; }}
  details summary::before {{ content: "\\25B6\\FE0E "; font-size: 0.8em; }}
  details[open] summary::before {{ content: "\\25BC\\FE0E "; }}
  small {{ color: var(--muted); }}
</style>
</head>
<body>
<div class="container">

<h1>QuartumSE Mega Benchmark Report</h1>
<p class="subtitle">Comprehensive analysis of {len(CIRCUITS)} circuits across {1 + len(NOISE_PROFILES)} conditions</p>

{_section_executive_summary(all_data, adaptive_data)}

{_section_overview_table(all_data, extended_metrics)}

<h2>3. Per-Circuit Details</h2>
<p>Click to expand each circuit for protocol comparison, crossover analysis,
   locality correlation, and Bayesian P(best).</p>
{"".join(circuit_cards)}

{_section_noise_impact(all_data)}

{_section_bayesian_adaptive(adaptive_data)}

{_section_statistical_significance(all_data)}

<hr>
<p style="text-align:center;color:var(--muted);font-size:0.85rem;">
  Generated by <code>generate_mega_report.py</code> &mdash;
  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
</p>

</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate mega benchmark HTML report")
    parser.add_argument("--skip-adaptive", action="store_true",
                        help="Skip Bayesian adaptive simulation (faster)")
    parser.add_argument("--skip-pbest", action="store_true",
                        help="Skip P(best) computation from parquet (faster)")
    parser.add_argument("--output", type=str, default="mega_benchmark_report.html",
                        help="Output HTML file path")
    args = parser.parse_args()

    warnings.filterwarnings("ignore", category=FutureWarning)

    print("=" * 70)
    print("QuartumSE Mega Benchmark Report Generator")
    print("=" * 70)

    # --- Step 1: Discover runs ---
    print("\n[1/5] Discovering benchmark runs ...")
    run_map = discover_all_runs()

    found_count = 0
    for cid, entry in run_map.items():
        conditions_found = [k for k, v in entry.items() if v is not None]
        found_count += len(conditions_found)
        print(f"  {cid}: {', '.join(conditions_found) if conditions_found else 'NONE'}")
    print(f"  Total: {found_count} runs discovered")

    # --- Step 2: Load analysis.json for all runs ---
    print("\n[2/5] Loading analysis.json files ...")
    all_data: dict = {}  # circuit_id -> condition -> {"analysis": ..., "run_dir": ...}
    for cid, entry in run_map.items():
        all_data[cid] = {}
        for cond, run_dir in entry.items():
            if run_dir is None:
                all_data[cid][cond] = {}
                continue
            a = load_analysis(run_dir)
            all_data[cid][cond] = {"analysis": a, "run_dir": run_dir}
            if a:
                winner = a.get("summary", {}).get("winner_at_max_n", "?")
                ratio = a.get("summary", {}).get("shadows_vs_baseline_ratio")
                print(f"  {cid}/{cond}: winner={SHORT.get(winner, winner)}, ratio={_fmt(ratio, '.3f')}")

    # --- Step 3: Compute Bayesian P(best) + extended metrics from long_form ---
    p_best_data: dict = {}  # circuit_id -> condition -> {N_total -> {proto -> P(best)}}
    extended_metrics: dict = {}  # circuit_id -> condition -> {percentiles: ..., locality: ...}
    if not args.skip_pbest:
        print("\n[3/5] Computing Bayesian P(best) + extended metrics from long-form data ...")
        for cid in CIRCUITS:
            p_best_data[cid] = {}
            extended_metrics[cid] = {}
            for cond in ["merged"] + NOISE_PROFILES:
                entry = all_data.get(cid, {}).get(cond, {})
                run_dir = entry.get("run_dir")
                if run_dir is None:
                    continue
                lf = load_long_form(run_dir)
                gt = load_ground_truth(run_dir)
                if lf is None or gt is None:
                    continue
                try:
                    pb = compute_p_best_from_longform(lf, gt)
                    p_best_data[cid][cond] = pb
                    # Quick summary
                    max_n = max(pb.keys()) if pb else 0
                    if max_n:
                        top = max(pb[max_n], key=pb[max_n].get)
                        print(f"  {cid}/{cond} N={max_n}: best={SHORT.get(top, top)} "
                              f"P={pb[max_n][top]:.3f}")
                except Exception as e:
                    print(f"  [WARN] {cid}/{cond} P(best): {e}")
                try:
                    ext = compute_extended_metrics(lf, gt)
                    extended_metrics[cid][cond] = ext
                except Exception as e:
                    print(f"  [WARN] {cid}/{cond} extended metrics: {e}")
    else:
        print("\n[3/5] Skipping P(best) (--skip-pbest)")

    # --- Step 4: Bayesian adaptive ---
    if not args.skip_adaptive:
        print("\n[4/5] Running Bayesian adaptive simulation ...")
        adaptive_data = run_bayesian_adaptive_for_report(skip=False)
    else:
        print("\n[4/5] Skipping Bayesian adaptive (--skip-adaptive)")
        adaptive_data = {}

    # --- Step 5: Generate HTML ---
    print("\n[5/5] Generating HTML report ...")
    html = generate_html(all_data, p_best_data, adaptive_data, extended_metrics)

    output_path = ROOT / args.output
    output_path.write_text(html, encoding="utf-8")
    print(f"\nReport written to: {output_path}")
    print(f"Size: {output_path.stat().st_size / 1024:.1f} KB")
    print("Done!")


if __name__ == "__main__":
    main()
