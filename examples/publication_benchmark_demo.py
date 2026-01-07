#!/usr/bin/env python
"""Publication-Ready Benchmark: Shadows vs Direct Baselines.

This script demonstrates a rigorous, publication-grade benchmark following
the Measurements Bible methodology. It includes:

1. Ground truth computation via statevector simulation
2. Multiple protocols: Direct baselines + Classical Shadows v0
3. Multiple shot budgets with replicates
4. Task evaluation (worst-case, distribution, bias-variance)
5. FWER-controlled confidence intervals
6. Comprehensive output and summary statistics

Usage:
    python publication_benchmark_demo.py

Output:
    - Ground truth values
    - Per-protocol performance at each shot budget
    - N* (shots-to-target) for worst-case criterion
    - Bias-variance decomposition (when ground truth available)
    - Shot-savings factors (SSF)

Requirements:
    pip install numpy qiskit qiskit-aer pydantic
"""

import argparse
import sys
sys.path.insert(0, "src")

import numpy as np
from datetime import datetime
from qiskit import QuantumCircuit

from quartumse.observables import generate_observable_set, partition_observable_set
from quartumse.protocols import (
    DirectGroupedProtocol,
    DirectOptimizedProtocol,
    ShadowsV0Protocol,
    list_protocols,
)
from quartumse.backends import StatevectorBackend, compute_ground_truth
from quartumse.benchmarking import (
    quick_comparison,
    compute_ssf,
    simulate_protocol_execution,
)
from quartumse.stats import construct_simultaneous_cis, FWERMethod


def create_benchmark_circuit(circuit_type: str, n_qubits: int) -> QuantumCircuit:
    """Create a benchmark circuit.

    Args:
        circuit_type: Type of circuit ("ghz", "random", "product").
        n_qubits: Number of qubits.

    Returns:
        QuantumCircuit for benchmarking.
    """
    circuit = QuantumCircuit(n_qubits)

    if circuit_type == "ghz":
        # GHZ state: |00...0> + |11...1>
        circuit.h(0)
        for i in range(1, n_qubits):
            circuit.cx(i - 1, i)

    elif circuit_type == "random":
        # Random single-qubit rotations + entangling layer
        rng = np.random.default_rng(42)
        for i in range(n_qubits):
            circuit.rx(rng.uniform(0, 2 * np.pi), i)
            circuit.ry(rng.uniform(0, 2 * np.pi), i)
        for i in range(n_qubits - 1):
            circuit.cx(i, i + 1)

    elif circuit_type == "product":
        # Product state with random single-qubit rotations
        rng = np.random.default_rng(42)
        for i in range(n_qubits):
            circuit.ry(rng.uniform(0, np.pi), i)

    else:
        raise ValueError(f"Unknown circuit type: {circuit_type}")

    return circuit


def run_benchmark(n_replicates: int) -> None:
    """Run the publication-ready benchmark."""
    print("=" * 80)
    print("PUBLICATION-READY BENCHMARK")
    print("Measurements Bible Methodology")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    print()

    # ==========================================================================
    # Configuration
    # ==========================================================================
    SEED = 42
    N_QUBITS = 4
    N_OBSERVABLES = 15
    CIRCUIT_TYPE = "ghz"
    N_SHOTS_GRID = [100, 500, 1000, 2000]
    N_REPLICATES = n_replicates
    EPSILON = 0.05  # Target precision
    DELTA = 0.05  # Global failure probability

    print("[Config]")
    print(f"  n_qubits: {N_QUBITS}")
    print(f"  n_observables: {N_OBSERVABLES}")
    print(f"  circuit_type: {CIRCUIT_TYPE}")
    print(f"  n_shots_grid: {N_SHOTS_GRID}")
    print(f"  n_replicates: {N_REPLICATES}")
    print(f"  epsilon: {EPSILON}")
    print(f"  delta: {DELTA}")
    print(f"  seed: {SEED}")
    print()

    # ==========================================================================
    # Step 1: Generate Observables
    # ==========================================================================
    print("[1] Observable Generation (Measurements Bible Section 3.3)")
    print("-" * 60)

    obs_set = generate_observable_set(
        generator_id="random_pauli",
        n_qubits=N_QUBITS,
        n_observables=N_OBSERVABLES,
        seed=SEED,
        max_weight=3,
    )

    locality_dist = obs_set.locality_distribution()
    print(f"  Generated {len(obs_set)} observables")
    print(f"  Locality distribution: {locality_dist}")
    print(f"  Mean locality: {obs_set.mean_locality():.2f}")

    # Grouping analysis
    groups, stats = partition_observable_set(obs_set, method="greedy")
    print(f"  Commuting groups: {stats['n_groups']}")
    print(f"  Mean group size: {stats['mean_group_size']:.2f}")
    print()

    # ==========================================================================
    # Step 2: Create Circuit
    # ==========================================================================
    print("[2] Circuit Preparation")
    print("-" * 60)

    circuit = create_benchmark_circuit(CIRCUIT_TYPE, N_QUBITS)
    print(f"  Circuit type: {CIRCUIT_TYPE}")
    print(f"  Depth: {circuit.depth()}")
    print(f"  Gates: {circuit.count_ops()}")
    print()

    # ==========================================================================
    # Step 3: Compute Ground Truth
    # ==========================================================================
    print("[3] Ground Truth Computation (Measurements Bible Section 3.4)")
    print("-" * 60)

    backend = StatevectorBackend()
    ground_truth = backend.compute_ground_truth(circuit, obs_set, "benchmark_circuit")

    truth_values = ground_truth.truth_values
    truth_array = np.array(list(truth_values.values()))

    print(f"  Mode: {ground_truth.truth_mode}")
    print(f"  Truth value range: [{truth_array.min():.4f}, {truth_array.max():.4f}]")
    print(f"  Truth value mean: {truth_array.mean():.4f}")
    print(f"  Truth value std: {truth_array.std():.4f}")
    print()

    # Show some examples
    print("  Sample ground truth values:")
    obs_by_id = {obs.observable_id: obs for obs in obs_set.observables}
    for i, (obs_id, val) in enumerate(list(truth_values.items())[:5]):
        obs = obs_by_id.get(obs_id)
        if obs:
            print(f"    {obs.pauli_string}: {val:.6f}")
    print()

    # ==========================================================================
    # Step 4: Initialize Protocols
    # ==========================================================================
    print("[4] Protocol Initialization")
    print("-" * 60)

    protocols = [
        DirectGroupedProtocol(),
        DirectOptimizedProtocol(),
        ShadowsV0Protocol(),
    ]

    print(f"  Available protocols: {list_protocols()}")
    print(f"  Selected protocols:")
    for p in protocols:
        print(f"    - {p.protocol_id} v{p.protocol_version}")
    print()

    # ==========================================================================
    # Step 5: Run Benchmark at Each Shot Budget
    # ==========================================================================
    print("[5] Protocol Execution")
    print("-" * 60)

    all_results = {}  # {(protocol_id, n_shots, rep): Estimates}

    for n_shots in N_SHOTS_GRID:
        print(f"\n  N = {n_shots} shots:")
        for protocol in protocols:
            rep_results = []
            for rep in range(N_REPLICATES):
                rep_seed = SEED + rep * 1000 + n_shots

                estimates = simulate_protocol_execution(
                    protocol=protocol,
                    observable_set=obs_set,
                    n_shots=n_shots,
                    seed=rep_seed,
                    true_expectations=truth_values,
                )
                rep_results.append(estimates)
                all_results[(protocol.protocol_id, n_shots, rep)] = estimates

            # Aggregate stats across replicates
            all_ses = []
            all_errors = []
            for est in rep_results:
                for e in est.estimates:
                    all_ses.append(e.se)
                    if e.observable_id in truth_values:
                        all_errors.append(abs(e.estimate - truth_values[e.observable_id]))

            mean_se = np.mean(all_ses)
            mean_error = np.mean(all_errors) if all_errors else float("nan")

            print(f"    {protocol.protocol_id:25s}: mean_SE={mean_se:.4f}, mean_|err|={mean_error:.4f}")

    print()

    # ==========================================================================
    # Step 6: Compute N* (Shots-to-Target)
    # ==========================================================================
    print("[6] N* Analysis (Measurements Bible Section 8, Task 1)")
    print("-" * 60)

    def check_criterion(estimates, epsilon):
        """Check if all observables meet precision criterion."""
        return all(e.se <= epsilon for e in estimates.estimates)

    n_star_results = {}
    for protocol in protocols:
        # Find minimum N where criterion is satisfied in majority of replicates
        for n_shots in N_SHOTS_GRID:
            satisfied_count = 0
            for rep in range(N_REPLICATES):
                est = all_results.get((protocol.protocol_id, n_shots, rep))
                if est and check_criterion(est, EPSILON):
                    satisfied_count += 1

            # Require (1 - delta) fraction of replicates to satisfy
            if satisfied_count >= N_REPLICATES * (1 - DELTA):
                n_star_results[protocol.protocol_id] = n_shots
                break
        else:
            n_star_results[protocol.protocol_id] = None

    print(f"  Target precision: epsilon = {EPSILON}")
    print(f"  Confidence requirement: (1 - delta) = {1 - DELTA:.0%}")
    print()
    for protocol_id, n_star in n_star_results.items():
        if n_star:
            print(f"  {protocol_id:25s}: N* = {n_star}")
        else:
            print(f"  {protocol_id:25s}: N* > {max(N_SHOTS_GRID)} (not achieved)")
    print()

    # ==========================================================================
    # Step 7: Compute SSF
    # ==========================================================================
    print("[7] Shot-Savings Factor (Measurements Bible Section 2.4)")
    print("-" * 60)

    baseline_id = "direct_grouped"
    baseline_n_star = n_star_results.get(baseline_id)

    if baseline_n_star:
        print(f"  Baseline: {baseline_id} (N* = {baseline_n_star})")
        print()
        for protocol_id, n_star in n_star_results.items():
            if n_star:
                ssf = baseline_n_star / n_star
                print(f"  {protocol_id:25s}: SSF = {ssf:.2f}x")
            else:
                print(f"  {protocol_id:25s}: SSF = N/A (N* not achieved)")
    else:
        print(f"  Baseline {baseline_id} did not achieve target precision")
        print("  Computing SSF from SE ratio at largest N instead:")
        max_n = max(N_SHOTS_GRID)
        results_at_max = {}
        for protocol in protocols:
            rep_results = [
                all_results[(protocol.protocol_id, max_n, rep)]
                for rep in range(N_REPLICATES)
            ]
            mean_se = np.mean([e.se for est in rep_results for e in est.estimates])
            results_at_max[protocol.protocol_id] = mean_se

        baseline_se = results_at_max.get(baseline_id, 1.0)
        for protocol_id, se in results_at_max.items():
            ssf = baseline_se / se if se > 0 else float("inf")
            print(f"  {protocol_id:25s}: SSF = {ssf:.2f}x (SE ratio)")
    print()

    # ==========================================================================
    # Step 8: Bias-Variance Analysis
    # ==========================================================================
    print("[8] Bias-Variance Decomposition (Measurements Bible Section 8, Task 6)")
    print("-" * 60)

    max_n = max(N_SHOTS_GRID)

    for protocol in protocols:
        # Collect estimates across replicates
        estimates_by_obs = {}  # obs_id -> list of estimates
        for rep in range(N_REPLICATES):
            est = all_results[(protocol.protocol_id, max_n, rep)]
            for e in est.estimates:
                if e.observable_id not in estimates_by_obs:
                    estimates_by_obs[e.observable_id] = []
                estimates_by_obs[e.observable_id].append(e.estimate)

        # Compute bias and variance
        biases = []
        variances = []
        for obs_id, ests in estimates_by_obs.items():
            mean_est = np.mean(ests)
            truth = truth_values[obs_id]
            bias = mean_est - truth
            var = np.var(ests, ddof=1)
            biases.append(bias)
            variances.append(var)

        mean_bias = np.mean(biases)
        mean_var = np.mean(variances)
        mean_mse = np.mean([b**2 + v for b, v in zip(biases, variances)])
        mean_rmse = np.sqrt(mean_mse)

        print(f"  {protocol.protocol_id} (N = {max_n}):")
        print(f"    Mean bias:     {mean_bias:+.6f}")
        print(f"    Mean variance: {mean_var:.6f}")
        print(f"    Mean RMSE:     {mean_rmse:.6f}")
        print()

    # ==========================================================================
    # Step 9: FWER-Controlled CIs
    # ==========================================================================
    print("[9] FWER-Controlled Confidence Intervals (Measurements Bible Section 7)")
    print("-" * 60)

    max_n = max(N_SHOTS_GRID)

    for protocol in protocols:
        # Get estimates from last replicate at max N
        est = all_results[(protocol.protocol_id, max_n, 0)]
        estimates = [e.estimate for e in est.estimates]
        ses = [e.se for e in est.estimates]

        sim_cis = construct_simultaneous_cis(
            estimates=estimates,
            standard_errors=ses,
            alpha=DELTA,
            fwer_method=FWERMethod.BONFERRONI,
        )

        # Check coverage against ground truth
        truths = [truth_values[e.observable_id] for e in est.estimates]
        coverage = sim_cis.coverage_fraction(truths)
        all_covered = sim_cis.all_contain(truths)

        print(f"  {protocol.protocol_id}:")
        print(f"    FWER method: {sim_cis.fwer_adjustment.method.value}")
        print(f"    Nominal coverage: {sim_cis.coverage_guarantee:.1%}")
        print(f"    Empirical per-obs coverage: {coverage:.1%}")
        print(f"    Family-wise coverage: {all_covered}")
        print()

    # ==========================================================================
    # Summary
    # ==========================================================================
    print("=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)
    print()
    print(f"{'Protocol':<25} {'N*':<10} {'SSF':<10} {'Mean SE':<12} {'Mean |err|':<12}")
    print("-" * 69)

    max_n = max(N_SHOTS_GRID)
    baseline_n_star = n_star_results.get("direct_grouped")

    for protocol in protocols:
        n_star = n_star_results[protocol.protocol_id]
        n_star_str = str(n_star) if n_star else f">{max(N_SHOTS_GRID)}"

        if n_star and baseline_n_star:
            ssf = baseline_n_star / n_star
            ssf_str = f"{ssf:.2f}x"
        else:
            ssf_str = "N/A"

        # Get stats at max N
        rep_results = [
            all_results[(protocol.protocol_id, max_n, rep)]
            for rep in range(N_REPLICATES)
        ]
        mean_se = np.mean([e.se for est in rep_results for e in est.estimates])
        mean_err = np.mean([
            abs(e.estimate - truth_values[e.observable_id])
            for est in rep_results
            for e in est.estimates
        ])

        print(f"{protocol.protocol_id:<25} {n_star_str:<10} {ssf_str:<10} {mean_se:<12.4f} {mean_err:<12.4f}")

    print()
    print("=" * 80)
    print("For publication-grade results, extend n_shots_grid")
    print("to cover the full regime of interest.")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publication benchmark demo.")
    parser.add_argument(
        "--n-replicates",
        type=int,
        default=20,
        help="Number of replicates per configuration (publication-grade default).",
    )
    args = parser.parse_args()

    run_benchmark(args.n_replicates)
