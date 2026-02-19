"""GHZ-4 benchmark with N=20000, 10 replicates, 3 noise profiles + raw shots.

Same setup as run_noise_benchmark.py but for a 4-qubit GHZ circuit.

Usage:
    python run_ghz_benchmark.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, "src")

from qiskit import QuantumCircuit

from quartumse import BenchmarkMode, BenchmarkSuiteConfig, run_benchmark_suite
from quartumse.observables.core import ObservableSet
from quartumse.observables.suites import make_chemistry_suites

# -- Config -------------------------------------------------------------------
N_SHOTS = [20000]
N_REPLICATES = 10
NOISE_PROFILES = ["ideal", "readout_1e-2", "depol_low"]
OUTPUT_BASE = "pilot_analysis_noise_ghz"
SEED = 42


def build_ghz_circuit(n_qubits: int = 4) -> QuantumCircuit:
    qc = QuantumCircuit(n_qubits)
    qc.h(0)
    for i in range(n_qubits - 1):
        qc.cx(i, i + 1)
    return qc


def build_merged_observable_set() -> tuple[ObservableSet, dict[str, int]]:
    suites = make_chemistry_suites(4)
    pauli_to_obs: dict = {}
    for suite in suites.values():
        for obs in suite.observables:
            if obs.pauli_string not in pauli_to_obs:
                pauli_to_obs[obs.pauli_string] = obs
    merged = list(pauli_to_obs.values())
    obs_set = ObservableSet(
        observables=merged,
        observable_set_id="GHZ4_merged",
        generator_id="suite_merger",
        generator_version="1.0.0",
    )
    loc_map = {o.observable_id: o.locality for o in obs_set.observables}
    return obs_set, loc_map


def main():
    qc = build_ghz_circuit(4)
    obs_set, loc_map = build_merged_observable_set()

    print(f"Circuit: GHZ-4 ({qc.num_qubits} qubits)")
    print(f"Observables: {len(obs_set)} (merged from chemistry suites)")
    print(f"N_shots: {N_SHOTS}")
    print(f"Replicates: {N_REPLICATES}")
    print(f"Noise profiles: {NOISE_PROFILES}")
    print(f"Output base: {OUTPUT_BASE}")
    print()

    results = {}
    t_total = time.perf_counter()

    for noise_profile in NOISE_PROFILES:
        print("=" * 72)
        print(f"NOISE PROFILE: {noise_profile}")
        print("=" * 72)

        config = BenchmarkSuiteConfig(
            mode=BenchmarkMode.BASIC,
            n_shots_grid=N_SHOTS,
            n_replicates=N_REPLICATES,
            seed=SEED,
            epsilon=0.05,
            delta=0.05,
            shadows_protocol_id="classical_shadows_v0",
            baseline_protocol_id="direct_grouped",
            output_base_dir=f"{OUTPUT_BASE}/{noise_profile}",
            noise_profile=noise_profile if noise_profile != "ideal" else None,
        )

        t0 = time.perf_counter()
        result = run_benchmark_suite(
            circuit=qc,
            observable_set=obs_set,
            circuit_id=f"GHZ4__{noise_profile}",
            config=config,
            locality_map=loc_map,
        )
        elapsed = time.perf_counter() - t0

        results[noise_profile] = result
        print(f"\n  Completed {noise_profile} in {elapsed:.1f}s")
        print(f"  Output: {result.output_dir}")

        # Verify raw_shots
        rs_path = result.output_dir / "base" / "raw_shots" / "data.parquet"
        if rs_path.exists():
            import pandas as pd
            rs_df = pd.read_parquet(rs_path)
            print(f"  Raw shots: {len(rs_df)} rows")
        else:
            print("  WARNING: No raw_shots/data.parquet!")
        print()

    total_elapsed = time.perf_counter() - t_total
    print("=" * 72)
    print(f"ALL DONE in {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
    print("=" * 72)

    for noise_profile, result in results.items():
        base_dir = result.output_dir / "base"
        print(f"  {noise_profile}: {base_dir}")

    print("\nTo run pilot analysis on each:")
    for noise_profile, result in results.items():
        base_dir = result.output_dir / "base"
        print(f"  python pilot_posthoc_analysis.py --data-dir \"{base_dir}\"")


if __name__ == "__main__":
    main()
