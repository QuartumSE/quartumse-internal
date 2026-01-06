#!/usr/bin/env python
"""QuartumSE Benchmarking Quick Start.

This script demonstrates the basic benchmarking workflow following
the Measurements Bible v3 methodology.

Usage:
    python quickstart_benchmark.py

Requirements:
    pip install numpy pydantic
"""

import sys
sys.path.insert(0, "src")

import numpy as np

from quartumse.observables import generate_observable_set, partition_observable_set
from quartumse.protocols import (
    DirectNaiveProtocol,
    DirectGroupedProtocol,
    DirectOptimizedProtocol,
)
from quartumse.stats import FWERMethod, construct_simultaneous_cis


def main():
    """Run quick start benchmark demonstration."""
    print("=" * 60)
    print("QuartumSE Benchmarking Quick Start")
    print("Measurements Bible v3 Methodology")
    print("=" * 60)

    # Configuration
    SEED = 42
    N_QUBITS = 4
    N_OBSERVABLES = 20
    N_SHOTS = 1000

    # Step 1: Generate observables
    print("\n[1] Generating observables...")
    observable_set = generate_observable_set(
        generator_id="random_pauli",
        n_qubits=N_QUBITS,
        n_observables=N_OBSERVABLES,
        seed=SEED,
        max_weight=3,
    )
    print(f"    Generated {len(observable_set)} observables")
    print(f"    Locality distribution: {observable_set.locality_distribution()}")

    # Step 2: Analyze commuting groups
    print("\n[2] Analyzing commuting groups...")
    groups, stats = partition_observable_set(observable_set)
    print(f"    Found {stats['n_groups']} groups")
    print(f"    Mean group size: {stats['mean_group_size']:.1f}")

    # Step 3: Initialize protocols
    print("\n[3] Initializing protocols...")
    protocols = {
        "direct_naive": DirectNaiveProtocol(),
        "direct_grouped": DirectGroupedProtocol(),
        "direct_optimized": DirectOptimizedProtocol(),
    }
    for name, proto in protocols.items():
        print(f"    {name}: {proto.protocol_id} v{proto.protocol_version}")

    # Step 4: Run protocols (simulated)
    print(f"\n[4] Running protocols with N={N_SHOTS} shots...")
    results = {}
    rng = np.random.default_rng(SEED)

    for name, protocol in protocols.items():
        # Initialize
        state = protocol.initialize(observable_set, N_SHOTS, SEED)

        # Get plan
        plan = protocol.plan(state)

        # Simulate data (in real usage, execute on backend)
        from quartumse.protocols.state import RawDatasetChunk

        bitstrings = {}
        for setting, n in zip(plan.settings, plan.shots_per_setting):
            bs = [
                "".join(str(rng.integers(0, 2)) for _ in range(N_QUBITS))
                for _ in range(n)
            ]
            bitstrings[setting.setting_id] = bs

        chunk = RawDatasetChunk(bitstrings=bitstrings, settings_executed=list(bitstrings.keys()))
        state = protocol.update(state, chunk)

        # Finalize
        estimates = protocol.finalize(state, observable_set)
        results[name] = estimates

        se_values = [e.se for e in estimates.estimates]
        print(f"    {name}: mean_SE={np.mean(se_values):.4f}, n_settings={len(plan.settings)}")

    # Step 5: Compute SSF
    print("\n[5] Computing Shot-Savings Factor...")
    baseline_se = np.mean([e.se for e in results["direct_grouped"].estimates])
    for name, estimates in results.items():
        protocol_se = np.mean([e.se for e in estimates.estimates])
        ssf = baseline_se / protocol_se if protocol_se > 0 else float("inf")
        print(f"    {name}: SSF = {ssf:.2f}x")

    # Step 6: Construct FWER-controlled CIs
    print("\n[6] Constructing FWER-controlled CIs...")
    best_estimates = results["direct_grouped"]
    estimates_list = [e.estimate for e in best_estimates.estimates]
    ses_list = [e.se for e in best_estimates.estimates]

    sim_cis = construct_simultaneous_cis(
        estimates=estimates_list,
        standard_errors=ses_list,
        alpha=0.05,
        fwer_method=FWERMethod.BONFERRONI,
    )
    print(f"    Method: {sim_cis.fwer_adjustment.method.value}")
    print(f"    Coverage guarantee: {sim_cis.coverage_guarantee:.1%}")
    print(f"    Per-comparison confidence: {sim_cis.fwer_adjustment.confidence_individual[0]:.4f}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Observables: {N_OBSERVABLES} on {N_QUBITS} qubits")
    print(f"Shot budget: {N_SHOTS}")
    print(f"Commuting groups: {stats['n_groups']}")
    print(f"FWER method: Bonferroni at α=0.05")
    print("=" * 60)
    print("\n✓ Quick start complete!")
    print("  See notebooks/ for full executable specifications.")
    print("  See docs/Measurements_Bible.md for methodology details.")


if __name__ == "__main__":
    main()
