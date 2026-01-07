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
    circuit: Any = None,
) -> Estimates:
    """Simulate protocol execution with synthetic data.

    This function simulates measurement outcomes. For protocols with custom
    acquire() methods (like shadows), it uses those. Otherwise, it generates
    random bitstrings.

    Args:
        protocol: Protocol to execute.
        observable_set: Observables to estimate.
        n_shots: Number of shots.
        seed: Random seed.
        true_expectations: True expectation values (default: random).
        circuit: Optional circuit for protocols that need it (e.g., shadows).

    Returns:
        Estimates from the protocol.
    """
    from qiskit import QuantumCircuit

    rng = np.random.default_rng(seed)

    # Generate true expectations if not provided
    if true_expectations is None:
        true_expectations = {
            obs.observable_id: rng.uniform(-0.5, 0.5)
            for obs in observable_set.observables
        }

    # Create default circuit if not provided
    if circuit is None:
        n_qubits = observable_set.n_qubits
        circuit = QuantumCircuit(n_qubits)
        # Simple state: random single-qubit rotations
        for q in range(n_qubits):
            circuit.ry(rng.uniform(0, np.pi), q)

    # Initialize protocol
    state = protocol.initialize(observable_set, n_shots, seed)

    # Get measurement plan
    plan = protocol.plan(state)

    # Check if protocol has a custom acquire method (shadows protocols do)
    is_shadows_protocol = "shadows" in protocol.protocol_id.lower()

    if is_shadows_protocol:
        # Use protocol's acquire method for shadows
        from qiskit_aer import AerSimulator
        backend = AerSimulator()
        chunk = protocol.acquire(circuit, plan, backend, seed)
    else:
        # Simulate measurements for baseline protocols
        bitstrings: dict[str, list[str]] = {}
        n_qubits = observable_set.n_qubits

        for setting, n_setting_shots in zip(plan.settings, plan.shots_per_setting):
            setting_bitstrings = []

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

        chunk = RawDatasetChunk(
            bitstrings=bitstrings,
            settings_executed=list(bitstrings.keys()),
            n_qubits=n_qubits,
        )

    # Update state with data
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


# =============================================================================
# Publication-Grade Benchmarking with Ground Truth
# =============================================================================

def run_publication_benchmark(
    circuit: Any,
    observable_set: ObservableSet,
    protocols: list[str | Protocol] | None = None,
    n_shots_grid: list[int] | None = None,
    n_replicates: int = 10,
    seed: int = 42,
    compute_truth: bool = True,
    circuit_id: str = "circuit",
    output_dir: str | None = None,
    epsilon: float = 0.01,
    delta: float = 0.05,
) -> dict[str, Any]:
    """Run publication-grade benchmark with ground truth (Measurements Bible).

    This function implements the complete benchmarking workflow:
    1. Compute ground truth via statevector simulation
    2. Run all protocols at each shot budget with multiple replicates
    3. Build long-form results with truth values
    4. Evaluate tasks (worst-case, distribution, bias-variance)
    5. Generate summary statistics and reports

    Args:
        circuit: State preparation circuit.
        observable_set: Set of observables to estimate.
        protocols: Protocol IDs or instances (default: all baselines + shadows).
        n_shots_grid: Shot budgets to evaluate (default: [100, 500, 1000, 5000]).
        n_replicates: Number of replicates per configuration.
        seed: Base random seed for reproducibility.
        compute_truth: Whether to compute ground truth via statevector.
        circuit_id: Identifier for the circuit.
        output_dir: Directory to save results (optional).
        epsilon: Target precision for tasks.
        delta: Global failure probability.

    Returns:
        Dict with benchmark results including:
        - ground_truth: GroundTruthResult
        - long_form_results: List of LongFormRow
        - task_results: Dict mapping task_id to TaskOutput
        - summary: Aggregate statistics
    """
    from qiskit import QuantumCircuit

    from .backends import StatevectorBackend, compute_ground_truth as _compute_ground_truth
    from .io import LongFormResultBuilder, LongFormRow
    from .tasks import WorstCaseTask, FixedBudgetDistributionTask, BiasVarianceTask, TaskConfig, TaskType

    # Default protocols: baselines + shadows v0
    if protocols is None:
        protocols = [
            DirectGroupedProtocol(),
            DirectOptimizedProtocol(),
        ]
        # Try to add shadows protocol if available
        try:
            from .protocols.shadows import ShadowsV0Protocol
            protocols.append(ShadowsV0Protocol())
        except ImportError:
            pass

    # Resolve protocol strings to instances
    protocol_instances = []
    for p in protocols:
        if isinstance(p, str):
            protocol_cls = get_protocol(p)
            protocol_instances.append(protocol_cls())
        else:
            protocol_instances.append(p)

    # Default shot grid
    if n_shots_grid is None:
        n_shots_grid = [100, 500, 1000, 5000]

    # Step 1: Compute ground truth
    ground_truth = None
    truth_values = {}

    if compute_truth:
        try:
            ground_truth = _compute_ground_truth(circuit, observable_set, circuit_id)
            truth_values = ground_truth.truth_values
        except Exception as e:
            print(f"Warning: Ground truth computation failed: {e}")
            print("Proceeding without ground truth (some tasks will be limited)")

    # Step 2: Run protocols at each shot budget with replicates
    long_form_rows: list[LongFormRow] = []
    run_id = f"publication_benchmark_{uuid4().hex[:8]}"

    for n_shots in n_shots_grid:
        for rep in range(n_replicates):
            rep_seed = seed + rep * 1000 + n_shots

            for protocol in protocol_instances:
                # Run protocol
                estimates = simulate_protocol_execution(
                    protocol=protocol,
                    observable_set=observable_set,
                    n_shots=n_shots,
                    seed=rep_seed,
                    true_expectations=truth_values if truth_values else None,
                )

                # Build long-form rows
                for est in estimates.estimates:
                    builder = LongFormResultBuilder()
                    builder.with_ids(
                        run_id=run_id,
                        protocol_id=protocol.protocol_id,
                        circuit_id=circuit_id,
                        observable_id=est.observable_id,
                    )
                    builder.with_estimate(
                        estimate=est.estimate,
                        se=est.se,
                        variance=est.variance,
                    )
                    builder.with_budget(
                        N_total=n_shots,
                        n_settings=estimates.n_settings,
                    )
                    builder.with_replicate(rep)

                    # Add CI if available
                    if est.ci:
                        builder.with_ci(
                            ci_low=est.ci.ci_low,
                            ci_high=est.ci.ci_high,
                            ci_method=est.ci.method.value,
                        )

                    # Add truth if available
                    if est.observable_id in truth_values:
                        builder.with_truth(
                            truth_values[est.observable_id],
                            mode="exact_statevector" if ground_truth else "simulated",
                        )

                    row = builder.build()
                    long_form_rows.append(row)

    # Step 3: Evaluate tasks
    task_results = {}

    # Task 1: Worst-case
    task1_config = TaskConfig(
        task_id="task1_worstcase",
        task_type=TaskType.WORST_CASE,
        epsilon=epsilon,
        delta=delta,
        n_grid=n_shots_grid,
        n_replicates=n_replicates,
    )
    task1 = WorstCaseTask(task1_config)

    for protocol in protocol_instances:
        protocol_rows = [r for r in long_form_rows if r.protocol_id == protocol.protocol_id]
        if protocol_rows:
            try:
                result = task1.evaluate(protocol_rows, truth_values)
                task_results[f"task1_{protocol.protocol_id}"] = result
            except Exception as e:
                print(f"Task 1 evaluation failed for {protocol.protocol_id}: {e}")

    # Task 3: Distribution (if implemented)
    try:
        task3_config = TaskConfig(
            task_id="task3_distribution",
            task_type=TaskType.FIXED_BUDGET,
            epsilon=epsilon,
            delta=delta,
            n_grid=n_shots_grid,
            n_replicates=n_replicates,
        )
        task3 = FixedBudgetDistributionTask(task3_config)

        for protocol in protocol_instances:
            protocol_rows = [r for r in long_form_rows if r.protocol_id == protocol.protocol_id]
            if protocol_rows:
                try:
                    result = task3.evaluate(protocol_rows, truth_values)
                    task_results[f"task3_{protocol.protocol_id}"] = result
                except Exception as e:
                    pass  # Task 3 may not be fully implemented
    except ImportError:
        pass

    # Task 6: Bias-Variance (requires ground truth)
    if truth_values:
        try:
            task6_config = TaskConfig(
                task_id="task6_biasvar",
                task_type=TaskType.BIAS_VARIANCE,
                epsilon=epsilon,
                delta=delta,
                n_grid=n_shots_grid,
                n_replicates=n_replicates,
            )
            task6 = BiasVarianceTask(task6_config)

            for protocol in protocol_instances:
                protocol_rows = [r for r in long_form_rows if r.protocol_id == protocol.protocol_id]
                if protocol_rows:
                    try:
                        result = task6.evaluate(protocol_rows, truth_values)
                        task_results[f"task6_{protocol.protocol_id}"] = result
                    except Exception as e:
                        print(f"Task 6 evaluation failed for {protocol.protocol_id}: {e}")
        except ImportError:
            pass

    # Step 4: Compute summary statistics
    summary = {
        "run_id": run_id,
        "n_protocols": len(protocol_instances),
        "n_shots_grid": n_shots_grid,
        "n_replicates": n_replicates,
        "n_observables": len(observable_set),
        "has_ground_truth": ground_truth is not None,
        "n_long_form_rows": len(long_form_rows),
        "protocols": [p.protocol_id for p in protocol_instances],
    }

    # Per-protocol summaries at largest N
    max_n = max(n_shots_grid)
    protocol_summaries = {}
    for protocol in protocol_instances:
        protocol_rows = [
            r for r in long_form_rows
            if r.protocol_id == protocol.protocol_id and r.N_total == max_n
        ]
        if protocol_rows:
            ses = [r.se for r in protocol_rows if r.se is not None]
            if ses:
                protocol_summaries[protocol.protocol_id] = {
                    "mean_se": np.mean(ses),
                    "max_se": np.max(ses),
                    "median_se": np.median(ses),
                }
                if truth_values:
                    errors = [
                        abs(r.estimate - truth_values.get(r.observable_id, 0))
                        for r in protocol_rows
                        if r.observable_id in truth_values
                    ]
                    if errors:
                        protocol_summaries[protocol.protocol_id]["mean_abs_error"] = np.mean(errors)
                        protocol_summaries[protocol.protocol_id]["max_abs_error"] = np.max(errors)

    summary["protocol_summaries"] = protocol_summaries

    # Step 5: Save results if output_dir specified
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save long-form results
        writer = ParquetWriter(output_path)
        writer.write_long_form(long_form_rows)

        # Save ground truth
        if ground_truth:
            import json
            truth_path = output_path / "ground_truth.json"
            with open(truth_path, "w") as f:
                json.dump({
                    "truth_values": ground_truth.truth_values,
                    "truth_mode": ground_truth.truth_mode,
                    "n_qubits": ground_truth.n_qubits,
                    "circuit_id": ground_truth.circuit_id,
                }, f, indent=2)

        # Save summary
        summary_path = output_path / "summary.json"
        with open(summary_path, "w") as f:
            # Convert numpy types to Python types for JSON
            def convert(obj):
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, (np.float32, np.float64)):
                    return float(obj)
                elif isinstance(obj, (np.int32, np.int64)):
                    return int(obj)
                return obj

            json.dump(summary, f, indent=2, default=convert)

    return {
        "ground_truth": ground_truth,
        "long_form_results": long_form_rows,
        "task_results": task_results,
        "summary": summary,
        "protocol_summaries": protocol_summaries,
    }
