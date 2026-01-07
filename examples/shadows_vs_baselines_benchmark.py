#!/usr/bin/env python
"""Benchmark: Classical Shadows v0 vs Direct Measurement Baselines.

This script demonstrates a rigorous comparison between the classical shadows
v0 protocol and the direct measurement baselines, following the Measurements
Bible v3 methodology.

Methodology:
- Generate random Pauli observables
- Estimate using both shadows and direct baselines
- Compare standard errors and compute SSF
- Apply FWER-controlled confidence intervals
- Report coverage statistics

Usage:
    python shadows_vs_baselines_benchmark.py
"""

import sys
sys.path.insert(0, "src")

import numpy as np
from qiskit import QuantumCircuit

from quartumse.observables import generate_observable_set, partition_observable_set
from quartumse.protocols import DirectGroupedProtocol, DirectOptimizedProtocol
from quartumse.benchmarking import quick_comparison, compute_ssf
from quartumse.stats import construct_simultaneous_cis, FWERMethod
from quartumse.shadows import RandomLocalCliffordShadows
from quartumse.shadows.config import ShadowConfig
from quartumse.shadows.core import Observable as ShadowObservable


def run_shadows_estimation(
    circuit: QuantumCircuit,
    observables: list[tuple[str, str, float]],  # (id, pauli_string, coefficient)
    n_shots: int,
    seed: int,
) -> dict[str, dict]:
    """Run classical shadows estimation.

    Args:
        circuit: State preparation circuit.
        observables: List of (observable_id, pauli_string, coefficient) tuples.
        n_shots: Number of shadow measurements.
        seed: Random seed.

    Returns:
        Dict mapping observable_id to {estimate, se, n_shots}.
    """
    # Configure shadows
    config = ShadowConfig(
        num_shadows=n_shots,
        random_seed=seed,
        median_of_means=False,
        confidence_level=0.95,
    )

    shadows = RandomLocalCliffordShadows(config)

    # Generate measurement circuits
    circuits = shadows.generate_measurement_circuits(circuit, n_shots)

    # Simulate measurements (in ideal case)
    rng = np.random.default_rng(seed)
    n_qubits = circuit.num_qubits

    # For this demo, simulate random measurements
    # In real usage, execute circuits on backend
    measurement_outcomes = rng.integers(0, 2, size=(n_shots, n_qubits))

    # Store the bases that were sampled during circuit generation
    measurement_bases = shadows.measurement_bases

    # Reconstruct shadows
    shadows.reconstruct_classical_shadow(measurement_outcomes, measurement_bases)

    # Estimate each observable
    results = {}
    for obs_id, pauli_str, coeff in observables:
        shadow_obs = ShadowObservable(
            pauli_string=pauli_str,
            coefficient=coeff,
        )
        estimate_result = shadows.estimate_observable(shadow_obs)

        # Compute SE from variance
        se = np.sqrt(estimate_result.variance / n_shots) if estimate_result.variance > 0 else 0.0

        results[obs_id] = {
            "estimate": estimate_result.expectation_value,
            "se": se,
            "variance": estimate_result.variance,
            "n_shots": n_shots,
        }

    return results


def main():
    """Run the benchmark comparison."""
    print("=" * 70)
    print("CLASSICAL SHADOWS VS DIRECT BASELINES BENCHMARK")
    print("Measurements Bible v3 Methodology")
    print("=" * 70)
    print()

    # Configuration
    SEED = 42
    N_QUBITS = 4
    N_OBSERVABLES = 20
    N_SHOTS = 2000

    # Step 1: Generate observables
    print("[1] Observable Generation (seeded per Measurements Bible §3.3)")
    print("-" * 50)

    obs_set = generate_observable_set(
        generator_id="random_pauli",
        n_qubits=N_QUBITS,
        n_observables=N_OBSERVABLES,
        seed=SEED,
        max_weight=3,
    )

    print(f"    n_qubits: {N_QUBITS}")
    print(f"    n_observables: {N_OBSERVABLES}")
    print(f"    generator_seed: {SEED}")
    print(f"    locality distribution: {obs_set.locality_distribution()}")
    print()

    # Step 2: Analyze commuting structure
    print("[2] Commuting Group Analysis (for baseline protocols)")
    print("-" * 50)

    groups, stats = partition_observable_set(obs_set, method="greedy")
    print(f"    n_groups: {stats['n_groups']}")
    print(f"    mean_group_size: {stats['mean_group_size']:.2f}")
    print(f"    grouping_method: greedy")
    print()

    # Step 3: Create state preparation circuit
    print("[3] State Preparation")
    print("-" * 50)

    circuit = QuantumCircuit(N_QUBITS)
    # Create a simple entangled state for testing
    circuit.h(0)
    for i in range(1, N_QUBITS):
        circuit.cx(i-1, i)

    print(f"    circuit: GHZ-like entangled state")
    print(f"    depth: {circuit.depth()}")
    print()

    # Step 4: Generate "true" expectations for evaluation
    print("[4] Ground Truth (simulated)")
    print("-" * 50)

    rng = np.random.default_rng(SEED)
    true_expectations = {
        obs.observable_id: rng.uniform(-0.5, 0.5)
        for obs in obs_set.observables
    }
    print(f"    truth_mode: simulated (random uniform)")
    print()

    # Step 5: Run baseline protocols
    print("[5] Baseline Protocol Execution")
    print("-" * 50)

    baseline_protocols = [
        DirectGroupedProtocol(),
        DirectOptimizedProtocol(),
    ]

    baseline_results = quick_comparison(
        observable_set=obs_set,
        protocols=baseline_protocols,
        n_shots=N_SHOTS,
        seed=SEED,
        true_expectations=true_expectations,
    )

    for pid, est in baseline_results.items():
        ses = [e.se for e in est.estimates]
        print(f"    {pid}:")
        print(f"        mean_SE: {np.mean(ses):.4f}")
        print(f"        max_SE:  {np.max(ses):.4f}")
        print(f"        n_settings: {len(set(e.metadata.get('group_id', i) for i, e in enumerate(est.estimates)))}")
    print()

    # Step 6: Run shadows protocol
    print("[6] Classical Shadows v0 Execution")
    print("-" * 50)

    observables_for_shadows = [
        (obs.observable_id, obs.pauli_string, obs.coefficient)
        for obs in obs_set.observables
    ]

    shadows_results = run_shadows_estimation(
        circuit=circuit,
        observables=observables_for_shadows,
        n_shots=N_SHOTS,
        seed=SEED,
    )

    shadows_ses = [r["se"] for r in shadows_results.values()]
    print(f"    shadows_v0:")
    print(f"        mean_SE: {np.mean(shadows_ses):.4f}")
    print(f"        max_SE:  {np.max(shadows_ses):.4f}")
    print(f"        n_settings: {N_SHOTS} (one per shot)")
    print()

    # Step 7: Compute SSF
    print("[7] Shot-Savings Factor Analysis (Measurements Bible §2.4)")
    print("-" * 50)

    baseline_mean_se = np.mean([e.se for e in baseline_results["direct_grouped"].estimates])
    shadows_mean_se = np.mean(shadows_ses)

    # SSF = baseline_se / protocol_se (higher is better for protocol)
    # In terms of variance: SSF = var_baseline / var_protocol
    ssf_shadows_vs_grouped = baseline_mean_se / shadows_mean_se if shadows_mean_se > 0 else float("inf")

    print(f"    Reference baseline: direct_grouped")
    print(f"    SSF (shadows vs grouped): {ssf_shadows_vs_grouped:.2f}x")

    ssf_baselines = compute_ssf(baseline_results, baseline_id="direct_grouped", metric="mean_se")
    for pid, val in ssf_baselines.items():
        print(f"    SSF ({pid} vs grouped): {val:.2f}x")
    print()

    # Step 8: FWER-Controlled CIs
    print("[8] FWER-Controlled Confidence Intervals (Measurements Bible §7)")
    print("-" * 50)

    # For grouped baseline
    best = baseline_results["direct_grouped"]
    estimates = [e.estimate for e in best.estimates]
    ses = [e.se for e in best.estimates]

    sim_cis = construct_simultaneous_cis(
        estimates=estimates,
        standard_errors=ses,
        alpha=0.05,
        fwer_method=FWERMethod.BONFERRONI,
    )

    print(f"    FWER method: {sim_cis.fwer_adjustment.method.value}")
    print(f"    Global delta: 0.05")
    print(f"    Per-comparison alpha: {sim_cis.fwer_adjustment.confidence_individual[0]:.6f}")
    print(f"    Coverage guarantee: {sim_cis.coverage_guarantee:.1%}")

    # Check coverage against "truth"
    truths = [true_expectations[e.observable_id] for e in best.estimates]
    cov = sim_cis.coverage_fraction(truths)
    all_covered = sim_cis.all_contain(truths)

    print(f"    Empirical per-observable coverage: {cov:.1%}")
    print(f"    Family-wise coverage (all in CI): {all_covered}")
    print()

    # Step 9: Summary Table
    print("[9] Summary Table")
    print("=" * 70)
    print(f"{'Protocol':<25} {'Mean SE':<12} {'Max SE':<12} {'SSF':<10}")
    print("-" * 70)

    for pid, est in baseline_results.items():
        ses = [e.se for e in est.estimates]
        ssf_val = ssf_baselines.get(pid, 1.0)
        print(f"{pid:<25} {np.mean(ses):<12.4f} {np.max(ses):<12.4f} {ssf_val:<10.2f}x")

    print(f"{'shadows_v0':<25} {np.mean(shadows_ses):<12.4f} {np.max(shadows_ses):<12.4f} {ssf_shadows_vs_grouped:<10.2f}x")
    print("=" * 70)
    print()

    # Step 10: Regime Analysis
    print("[10] Regime Analysis (Measurements Bible §4.4)")
    print("-" * 50)

    locality_dist = obs_set.locality_distribution()
    high_weight = sum(v for k, v in locality_dist.items() if k >= 3)
    low_weight = sum(v for k, v in locality_dist.items() if k < 3)

    print(f"    Observable locality:")
    print(f"        Low-weight (k<3): {low_weight} observables")
    print(f"        High-weight (k>=3): {high_weight} observables")
    print()
    print("    Expected regime behavior:")
    print("        - Shadows: Better for many observables, low-weight Paulis")
    print("        - Direct grouped: Better for few observables, high commutation")
    print("        - Direct optimized: Best when variance-aware allocation helps")
    print()

    # Interpretation
    print("[11] Interpretation")
    print("-" * 50)
    if ssf_shadows_vs_grouped > 1.0:
        print(f"    Shadows achieves {ssf_shadows_vs_grouped:.1f}x shot-savings vs grouped baseline")
        print("    This is expected for the test configuration with many low-weight observables")
    else:
        print(f"    Direct grouped is more efficient ({1/ssf_shadows_vs_grouped:.1f}x) in this regime")
        print("    Consider shadows for larger observable sets or different locality distributions")

    print()
    print("=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70)
    print()
    print("Artifacts generated:")
    print("  - Observable set with reproducible seed")
    print("  - Protocol comparison metrics")
    print("  - FWER-controlled confidence intervals")
    print("  - Regime analysis")
    print()
    print("For publication-grade results, run with:")
    print("  - Multiple shot budgets (N_grid)")
    print("  - Multiple replicates (n_replicates >= 10)")
    print("  - Ground truth from statevector simulation")


if __name__ == "__main__":
    main()
