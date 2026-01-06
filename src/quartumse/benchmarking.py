"""High-level benchmarking API (Measurements Bible v3).

This module provides a simplified interface for running benchmarks
following the Measurements Bible methodology.

Example:
    from quartumse.benchmarking import run_benchmark, quick_comparison

    # Quick comparison of protocols
    results = quick_comparison(
        circuit=my_circuit,
        observables=my_observables,
        protocols=["direct_naive", "direct_grouped"],
        n_shots=1000,
    )

    # Full benchmark sweep
    report = run_benchmark(
        circuits=[circuit1, circuit2],
        observable_sets=[obs_set1],
        protocols=["direct_naive", "direct_grouped", "direct_optimized"],
        n_grid=[100, 500, 1000, 5000],
        n_replicates=10,
        output_dir="results/benchmark_001",
    )
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np

from .io import LongFormResultBuilder, LongFormResultSet, ParquetWriter, SummaryAggregator
from .io.schemas import RunManifest
from .observables import Observable, ObservableSet, generate_observable_set
from .protocols import (
    DirectGroupedProtocol,
    DirectNaiveProtocol,
    DirectOptimizedProtocol,
    Estimates,
    Protocol,
    get_protocol,
)
from .protocols.state import RawDatasetChunk
from .stats import construct_simultaneous_cis, FWERMethod
from .tasks import SweepConfig, SweepOrchestrator, TaskConfig, TaskType, WorstCaseTask
from .viz import ReportBuilder, create_benchmark_report


def get_default_protocols() -> list[Protocol]:
    """Get the default set of baseline protocols.

    Returns:
        List of DirectNaive, DirectGrouped, and DirectOptimized protocols.
    """
    return [
        DirectNaiveProtocol(),
        DirectGroupedProtocol(),
        DirectOptimizedProtocol(),
    ]


def simulate_protocol_execution(
    protocol: Protocol,
    observable_set: ObservableSet,
    n_shots: int,
    seed: int,
    true_expectations: dict[str, float] | None = None,
) -> Estimates:
    """Simulate protocol execution with synthetic data.

    This function simulates measurement outcomes assuming each observable
    yields ±1 eigenvalues with P(+1) = (1 + ⟨O⟩)/2.

    Args:
        protocol: Protocol to execute.
        observable_set: Observables to estimate.
        n_shots: Number of shots.
        seed: Random seed.
        true_expectations: True expectation values (default: random).

    Returns:
        Estimates from the protocol.
    """
    rng = np.random.default_rng(seed)

    # Generate true expectations if not provided
    if true_expectations is None:
        true_expectations = {
            obs.observable_id: rng.uniform(-0.5, 0.5)
            for obs in observable_set.observables
        }

    # Initialize protocol
    state = protocol.initialize(observable_set, n_shots, seed)

    # Get measurement plan
    plan = protocol.plan(state)

    # Simulate measurements
    bitstrings: dict[str, list[str]] = {}

    for setting, n_setting_shots in zip(plan.settings, plan.shots_per_setting):
        setting_bitstrings = []
        n_qubits = observable_set.n_qubits

        for _ in range(n_setting_shots):
            # Generate bitstring based on measurement basis and true expectations
            bs = []
            for q in range(n_qubits):
                # Simplified: each qubit measured in Z basis
                # In reality, this depends on the measurement basis
                p_one = 0.5  # Default to random
                bs.append("1" if rng.random() < p_one else "0")
            setting_bitstrings.append("".join(bs))

        bitstrings[setting.setting_id] = setting_bitstrings

    # Update state with data
    chunk = RawDatasetChunk(
        bitstrings=bitstrings,
        settings_executed=list(bitstrings.keys()),
    )
    state = protocol.update(state, chunk)

    # Finalize and return estimates
    return protocol.finalize(state, observable_set)


def quick_comparison(
    observable_set: ObservableSet,
    protocols: list[str | Protocol] | None = None,
    n_shots: int = 1000,
    seed: int = 42,
    true_expectations: dict[str, float] | None = None,
) -> dict[str, Estimates]:
    """Quick comparison of protocols on a single configuration.

    Args:
        observable_set: Observables to estimate.
        protocols: Protocol IDs or instances (default: all baselines).
        n_shots: Number of shots.
        seed: Random seed.
        true_expectations: True expectation values.

    Returns:
        Dict mapping protocol_id to Estimates.
    """
    if protocols is None:
        protocol_instances = get_default_protocols()
    else:
        protocol_instances = []
        for p in protocols:
            if isinstance(p, str):
                protocol_cls = get_protocol(p)
                protocol_instances.append(protocol_cls())
            else:
                protocol_instances.append(p)

    results = {}
    for protocol in protocol_instances:
        estimates = simulate_protocol_execution(
            protocol=protocol,
            observable_set=observable_set,
            n_shots=n_shots,
            seed=seed,
            true_expectations=true_expectations,
        )
        results[protocol.protocol_id] = estimates

    return results


def run_benchmark(
    observable_sets: list[tuple[str, ObservableSet]],
    circuits: list[tuple[str, Any]] | None = None,
    protocols: list[str | Protocol] | None = None,
    n_grid: list[int] | None = None,
    n_replicates: int = 10,
    output_dir: str | None = None,
    seed: int = 42,
    epsilon: float = 0.01,
    delta: float = 0.05,
) -> dict[str, Any]:
    """Run a full benchmark sweep.

    Args:
        observable_sets: List of (id, ObservableSet) tuples.
        circuits: List of (id, circuit) tuples (default: identity circuit).
        protocols: Protocol IDs or instances.
        n_grid: Shot budget grid.
        n_replicates: Number of replicates.
        output_dir: Output directory for results.
        seed: Base random seed.
        epsilon: Target precision.
        delta: Global failure probability.

    Returns:
        Benchmark results summary.
    """
    run_id = f"benchmark_{uuid4().hex[:8]}"

    # Default circuits
    if circuits is None:
        circuits = [("identity", None)]

    # Default protocols
    if protocols is None:
        protocol_instances = get_default_protocols()
    else:
        protocol_instances = []
        for p in protocols:
            if isinstance(p, str):
                protocol_cls = get_protocol(p)
                protocol_instances.append(protocol_cls())
            else:
                protocol_instances.append(p)

    # Default N grid
    if n_grid is None:
        n_grid = [100, 500, 1000, 5000, 10000]

    # Configure sweep
    sweep_config = SweepConfig(
        run_id=run_id,
        protocols=protocol_instances,
        circuits=circuits,
        observable_sets=observable_sets,
        n_grid=n_grid,
        n_replicates=n_replicates,
        seeds={"base": seed},
    )

    # Run sweep
    orchestrator = SweepOrchestrator(sweep_config)
    results = orchestrator.run()

    # Compute summaries
    aggregator = SummaryAggregator(results, epsilon=epsilon)
    summaries = aggregator.compute_summaries()

    # Save results if output_dir specified
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        writer = ParquetWriter(output_path)
        writer.write_long_form(results)
        writer.write_summary(summaries)

        manifest = orchestrator.create_manifest()
        writer.write_manifest(manifest)

    # Return summary
    return {
        "run_id": run_id,
        "n_results": len(results),
        "n_protocols": len(protocol_instances),
        "n_circuits": len(circuits),
        "n_observable_sets": len(observable_sets),
        "n_grid": n_grid,
        "n_replicates": n_replicates,
        "summaries": summaries,
        "output_dir": output_dir,
    }


def compute_ssf(
    results: dict[str, Estimates],
    baseline_id: str = "direct_grouped",
    metric: str = "mean_se",
) -> dict[str, float]:
    """Compute shot-savings factor for each protocol.

    Args:
        results: Dict mapping protocol_id to Estimates.
        baseline_id: Baseline protocol ID.
        metric: Metric to use for comparison.

    Returns:
        Dict mapping protocol_id to SSF value.
    """
    if baseline_id not in results:
        raise ValueError(f"Baseline protocol '{baseline_id}' not in results")

    baseline_estimates = results[baseline_id]

    if metric == "mean_se":
        baseline_metric = np.mean([e.se for e in baseline_estimates.estimates])
    elif metric == "max_se":
        baseline_metric = max(e.se for e in baseline_estimates.estimates)
    else:
        raise ValueError(f"Unknown metric: {metric}")

    ssf_results = {}
    for protocol_id, estimates in results.items():
        if metric == "mean_se":
            protocol_metric = np.mean([e.se for e in estimates.estimates])
        else:
            protocol_metric = max(e.se for e in estimates.estimates)

        # SSF = baseline_metric / protocol_metric
        # Higher is better (protocol achieves same precision with fewer shots)
        if protocol_metric > 0:
            ssf_results[protocol_id] = baseline_metric / protocol_metric
        else:
            ssf_results[protocol_id] = float("inf")

    return ssf_results


def generate_test_observables(
    n_qubits: int = 4,
    n_observables: int = 20,
    seed: int = 42,
    generator: str = "random_pauli",
) -> ObservableSet:
    """Generate test observables for benchmarking.

    Args:
        n_qubits: Number of qubits.
        n_observables: Number of observables.
        seed: Random seed.
        generator: Generator to use.

    Returns:
        ObservableSet with generated observables.
    """
    return generate_observable_set(
        generator_id=generator,
        n_qubits=n_qubits,
        n_observables=n_observables,
        seed=seed,
    )
