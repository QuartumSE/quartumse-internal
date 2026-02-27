"""Generate / update the performance baseline file.

Usage:
    python scripts/update_perf_baseline.py

Runs every benchmark defined in tests/perf/test_perf.py, collects median
timings, and writes tests/perf/perf_baseline.json.  Commit that file so
CI can detect regressions.
"""

from __future__ import annotations

import json
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
BASELINE_PATH = ROOT / "tests" / "perf" / "perf_baseline.json"

# ---------------------------------------------------------------------------
# Workload (identical to tests/perf/conftest.py)
# ---------------------------------------------------------------------------

N_SHOTS = 1000
SEED = 42


def build_workload():
    from qiskit import QuantumCircuit

    from quartumse.observables import Observable, ObservableSet

    qc = QuantumCircuit(4)
    qc.h(0)
    qc.cx(0, 1)
    qc.h(2)
    qc.cx(2, 3)

    rng = np.random.default_rng(12345)
    paulis = ["I", "X", "Y", "Z"]
    obs_list = []
    for i in range(20):
        ps = "".join(rng.choice(paulis) for _ in range(4))
        if ps == "IIII":
            ps = "ZIII"
        obs_list.append(Observable(observable_id=f"o{i:02d}", pauli_string=ps, coefficient=1.0))
    obs_set = ObservableSet(observables=obs_list)

    try:
        from quartumse.backends.truth import compute_ground_truth

        ground_truth = compute_ground_truth(qc, obs_set)
    except Exception:
        ground_truth = {o.observable_id: 0.0 for o in obs_list}

    # Raw pauli strings for construction benchmark
    rng2 = np.random.default_rng(12345)
    paulis_raw = []
    for _ in range(20):
        ps = "".join(rng2.choice(paulis) for _ in range(4))
        if ps == "IIII":
            ps = "ZIII"
        paulis_raw.append(ps)

    return qc, obs_set, ground_truth, paulis_raw


def timeit(fn, *, n_runs: int = 7) -> list[float]:
    times: list[float] = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        times.append(t1 - t0)
    return times


# ---------------------------------------------------------------------------
# Benchmarks
# ---------------------------------------------------------------------------


def run_all_benchmarks():
    from quartumse.benchmarking import quick_comparison, simulate_protocol_execution
    from quartumse.observables import Observable, ObservableSet
    from quartumse.observables.grouping import greedy_grouping, sorted_insertion_grouping
    from quartumse.protocols import (
        DirectGroupedProtocol,
        DirectNaiveProtocol,
        DirectOptimizedProtocol,
        ShadowsV0Protocol,
    )

    circuit, obs_set, gt, paulis_raw = build_workload()
    results: dict[str, dict] = {}

    def record(name: str, times: list[float]):
        med = statistics.median(times)
        results[name] = {
            "median": round(med, 6),
            "stdev": round(statistics.stdev(times) if len(times) > 1 else 0.0, 6),
            "n_runs": len(times),
            "all_times": [round(t, 6) for t in times],
        }
        print(f"  {name:<35s}  median={med:.4f}s  (n={len(times)})")

    print("Running benchmarks...")

    # 1) simulate_direct_naive
    proto = DirectNaiveProtocol()
    t = timeit(
        lambda: simulate_protocol_execution(
            protocol=proto,
            observable_set=obs_set,
            n_shots=N_SHOTS,
            seed=SEED,
            true_expectations=gt,
            circuit=circuit,
        )
    )
    record("simulate_direct_naive", t)

    # 2) simulate_direct_grouped
    proto = DirectGroupedProtocol()
    t = timeit(
        lambda: simulate_protocol_execution(
            protocol=proto,
            observable_set=obs_set,
            n_shots=N_SHOTS,
            seed=SEED,
            true_expectations=gt,
            circuit=circuit,
        )
    )
    record("simulate_direct_grouped", t)

    # 3) simulate_direct_optimized
    proto = DirectOptimizedProtocol()
    t = timeit(
        lambda: simulate_protocol_execution(
            protocol=proto,
            observable_set=obs_set,
            n_shots=N_SHOTS,
            seed=SEED,
            true_expectations=gt,
            circuit=circuit,
        )
    )
    record("simulate_direct_optimized", t)

    # 4) simulate_shadows_v0
    proto = ShadowsV0Protocol()
    t = timeit(
        lambda: simulate_protocol_execution(
            protocol=proto,
            observable_set=obs_set,
            n_shots=N_SHOTS,
            seed=SEED,
            true_expectations=gt,
            circuit=circuit,
        )
    )
    record("simulate_shadows_v0", t)

    # 5) observable_set_construction
    def obs_construction():
        ol = [
            Observable(observable_id=f"o{i:02d}", pauli_string=ps, coefficient=1.0)
            for i, ps in enumerate(paulis_raw)
        ]
        _ = ObservableSet(observables=ol)

    t = timeit(obs_construction)
    record("observable_set_construction", t)

    # 6) grouping_algorithms
    obs = obs_set.observables

    def grouping():
        greedy_grouping(obs)
        sorted_insertion_grouping(obs)

    t = timeit(grouping)
    record("grouping_algorithms", t)

    # 7) quick_comparison_3proto
    protos = [DirectNaiveProtocol(), DirectGroupedProtocol(), ShadowsV0Protocol()]

    def qc_run():
        quick_comparison(
            observable_set=obs_set,
            protocols=protos,
            n_shots=N_SHOTS,
            seed=SEED,
            true_expectations=gt,
        )

    t = timeit(qc_run)
    record("quick_comparison_3proto", t)

    # 8) eigenvalue_direct_naive
    naive = DirectNaiveProtocol()
    rng = np.random.default_rng(99)
    bitstrings = ["".join(str(b) for b in row) for row in rng.integers(0, 2, size=(N_SHOTS, 4))]

    t = timeit(lambda: naive._estimate_from_bitstrings(bitstrings, "ZIZI", 1.0), n_runs=21)
    record("eigenvalue_direct_naive", t)

    # 9) eigenvalue_direct_grouped
    grouped = DirectGroupedProtocol()

    t = timeit(
        lambda: grouped._estimate_from_bitstrings(bitstrings, "ZIZI", "ZZZZ", 1.0), n_runs=21
    )
    record("eigenvalue_direct_grouped", t)

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    # Git metadata
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True, cwd=ROOT
        ).strip()
    except Exception:
        sha = "unknown"

    results = run_all_benchmarks()

    baseline = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "commit": sha,
            "python_version": sys.version,
            "platform": sys.platform,
            "n_shots": N_SHOTS,
            "seed": SEED,
        },
        "benchmarks": results,
    }

    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BASELINE_PATH, "w") as f:
        json.dump(baseline, f, indent=2)

    print(f"\nBaseline written to {BASELINE_PATH}")
    print(f"  commit: {sha}")
    print(f"  benchmarks: {len(results)}")


if __name__ == "__main__":
    main()
