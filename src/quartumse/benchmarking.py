"""High-level benchmarking API (Measurements Bible).

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

from .backends.truth import GroundTruthConfig
from .io import LongFormResultBuilder, LongFormResultSet, ParquetWriter, SummaryAggregator
from .io.schemas import RunManifest
from .observables import ObservableSet, generate_observable_set
from .protocols import (
    DirectGroupedProtocol,
    DirectNaiveProtocol,
    DirectOptimizedProtocol,
    Estimates,
    Protocol,
    get_protocol,
)
from .tasks import SweepConfig, SweepOrchestrator, TaskConfig, TaskType, WorstCaseTask
from .viz import create_benchmark_report


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
    """Execute protocol using a physical measurement path.

    This function runs the protocol against a backend to generate
    measurement outcomes that respect the protocol's measurement plan.

    Args:
        protocol: Protocol to execute.
        observable_set: Observables to estimate.
        n_shots: Number of shots.
        seed: Random seed.
        true_expectations: True expectation values (unused in physical execution).
        circuit: Optional circuit for protocols that need it (e.g., shadows).

    Returns:
        Estimates from the protocol.
    """
    from qiskit import QuantumCircuit

    rng = np.random.default_rng(seed)

    # Create default circuit if not provided
    if circuit is None:
        n_qubits = observable_set.n_qubits
        circuit = QuantumCircuit(n_qubits)
        # Simple state: random single-qubit rotations
        for q in range(n_qubits):
            circuit.ry(rng.uniform(0, np.pi), q)

    from qiskit_aer import AerSimulator

    backend = AerSimulator()
    return protocol.run(
        circuit=circuit,
        observable_set=observable_set,
        total_budget=n_shots,
        backend=backend,
        seed=seed,
    )


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
        long_form_path = writer.write_long_form(results)
        summary_path = writer.write_summary(summaries)

        manifest = orchestrator.create_manifest()
        manifest.long_form_path = str(long_form_path)
        manifest.summary_path = str(summary_path)
        plots_dir = output_path / "plots"
        plots_dir.mkdir(parents=True, exist_ok=True)
        manifest.plots_dir = str(plots_dir)
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


def _build_plot_summary(
    result_set: LongFormResultSet,
    summary_rows: list[Any],
    baseline_id: str,
    epsilon: float,
) -> dict[str, Any]:
    """Build a summary dictionary for standard benchmark plots."""
    from .io.summary import compute_shot_savings_factor

    attainment: dict[str, dict[int, float]] = {}
    coverage: dict[str, dict[int, float]] = {}
    se_distribution: dict[int, dict[str, list[float]]] = {}

    for row in summary_rows:
        if row.attainment_fraction is not None:
            attainment.setdefault(row.protocol_id, {})[row.N_total] = row.attainment_fraction
        if row.coverage_per_observable is not None:
            coverage.setdefault(row.protocol_id, {})[row.N_total] = row.coverage_per_observable

    for row in result_set:
        se_distribution.setdefault(row.N_total, {}).setdefault(row.protocol_id, []).append(row.se)

    ssf_data: dict[str, float] = {}
    for protocol_id in result_set.get_unique_protocols():
        if protocol_id == baseline_id:
            ssf_data[protocol_id] = 1.0
            continue
        ssf_by_circuit = compute_shot_savings_factor(
            summary_rows,
            protocol_id=protocol_id,
            baseline_protocol_id=baseline_id,
        )
        if ssf_by_circuit:
            ssf_data[protocol_id] = next(iter(ssf_by_circuit.values()))

    summary: dict[str, Any] = {
        "epsilon": epsilon,
        "baseline": baseline_id,
        "confidence_level": 0.95,
    }
    if attainment:
        summary["attainment"] = attainment
    if ssf_data:
        summary["ssf"] = ssf_data
    if se_distribution:
        summary["se_distribution"] = se_distribution
    if coverage:
        summary["coverage"] = coverage

    return summary


# =============================================================================
# Publication-Grade Benchmarking with Ground Truth
# =============================================================================


def run_publication_benchmark(
    circuit: Any,
    observable_set: ObservableSet,
    protocols: list[str | Protocol] | None = None,
    n_shots_grid: list[int] | None = None,
    n_replicates: int = 20,
    seed: int = 42,
    compute_truth: bool = True,
    circuit_id: str = "circuit",
    output_dir: str | None = None,
    epsilon: float = 0.01,
    delta: float = 0.05,
    ground_truth_config: GroundTruthConfig | None = None,
    max_workers: int | None = None,
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
        n_replicates: Number of replicates per configuration (publication-grade default).
        seed: Base random seed for reproducibility.
        compute_truth: Whether to compute ground truth via statevector.
        circuit_id: Identifier for the circuit.
        output_dir: Directory to save results (optional).
        epsilon: Target precision for tasks.
        delta: Global failure probability.
        ground_truth_config: Optional configuration for statevector ground truth
            (including memory_limit_bytes).
        max_workers: Optional number of workers for parallel protocol execution.

    Returns:
        Dict with benchmark results including:
        - ground_truth: GroundTruthResult
        - long_form_results: List of LongFormRow
        - task_results: Dict mapping task_id to TaskOutput
        - summary: Aggregate statistics
    """
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator

    from .backends import compute_ground_truth as _compute_ground_truth
    from .io import (
        LongFormResultSet,
        ParquetWriter,
        SummaryAggregator,
    )
    from .tasks import (
        BiasVarianceTask,
        FixedBudgetDistributionTask,
    )
    from .utils.provenance import (
        get_environment_lock,
        get_git_commit_hash,
        get_python_version,
        get_quartumse_version,
    )

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
            ground_truth = _compute_ground_truth(
                circuit,
                observable_set,
                circuit_id,
                config=ground_truth_config,
            )
            truth_values = ground_truth.truth_values
        except Exception as e:
            print(f"Warning: Ground truth computation failed: {e}")
            print("Proceeding without ground truth (some tasks will be limited)")

    # Step 2: Run protocols at each shot budget with replicates
    run_id = f"publication_benchmark_{uuid4().hex[:8]}"
    methodology_version = "3.0.0"
    observable_set_id = f"{circuit_id}_observables"
    result_set = LongFormResultSet()
    builder = LongFormResultBuilder()

    circuit_depth = circuit.depth() if isinstance(circuit, QuantumCircuit) else None
    twoq_gate_count = None
    if isinstance(circuit, QuantumCircuit):
        twoq_gate_count = sum(1 for instr, qargs, _ in circuit.data if len(qargs) == 2)

    backend_id = "aer_simulator"
    execution_backend = AerSimulator()

    def _generate_seeds(rep: int, n_shots: int, protocol_index: int) -> dict[str, int]:
        rng = np.random.default_rng(seed + rep * 1000 + n_shots + protocol_index * 17)
        seed_protocol = int(rng.integers(0, 2**31))
        return {
            "seed_policy": "publication_benchmark",
            "seed_protocol": seed_protocol,
            "seed_acquire": seed_protocol,
            "seed_bootstrap": int(rng.integers(0, 2**31)),
        }

    observable_lookup = {obs.observable_id: obs for obs in observable_set.observables}

    def _run_protocol(
        protocol_index: int,
        protocol: Protocol,
        rep: int,
        n_shots: int,
    ) -> tuple[Protocol, dict[str, int], Estimates]:
        seeds = _generate_seeds(rep, n_shots, protocol_index)
        estimates = protocol.run(
            circuit=circuit,
            observable_set=observable_set,
            total_budget=n_shots,
            backend=execution_backend,
            seed=seeds["seed_protocol"],
        )
        return protocol, seeds, estimates

    for n_shots in n_shots_grid:
        for rep in range(n_replicates):
            if max_workers and max_workers > 1 and len(protocol_instances) > 1:
                from concurrent.futures import ThreadPoolExecutor

                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = [
                        executor.submit(_run_protocol, idx, protocol, rep, n_shots)
                        for idx, protocol in enumerate(protocol_instances)
                    ]
                    protocol_runs = [future.result() for future in futures]
            else:
                protocol_runs = [
                    _run_protocol(idx, protocol, rep, n_shots)
                    for idx, protocol in enumerate(protocol_instances)
                ]

            for protocol, seeds, estimates in protocol_runs:
                for est in estimates.estimates:
                    obs = observable_lookup[est.observable_id]
                    row_builder = (
                        builder.reset()
                        .with_run_id(run_id)
                        .with_methodology_version(methodology_version)
                        .with_circuit(
                            circuit_id=circuit_id,
                            n_qubits=observable_set.n_qubits,
                            depth=circuit_depth,
                            twoq_gate_count=twoq_gate_count,
                        )
                        .with_observable(
                            observable_id=est.observable_id,
                            observable_type=obs.observable_type.value,
                            locality=obs.locality,
                            coefficient=obs.coefficient,
                            observable_set_id=observable_set_id,
                            group_id=obs.group_id,
                            M_total=len(observable_set),
                        )
                        .with_protocol(
                            protocol_id=estimates.protocol_id or protocol.protocol_id,
                            protocol_version=estimates.protocol_version
                            or protocol.protocol_version,
                        )
                        .with_backend(backend_id, noise_profile_id="ideal")
                        .with_replicate(rep)
                        .with_seeds(
                            seed_policy=seeds["seed_policy"],
                            seed_protocol=seeds["seed_protocol"],
                            seed_acquire=seeds["seed_acquire"],
                            seed_bootstrap=seeds["seed_bootstrap"],
                        )
                        .with_budget(
                            N_total=n_shots,
                            n_settings=est.n_settings or estimates.n_settings,
                        )
                        .with_estimate(
                            estimate=est.estimate,
                            se=est.se,
                            ci_low=est.ci.ci_low if est.ci else None,
                            ci_high=est.ci.ci_high if est.ci else None,
                            ci_low_raw=est.ci.ci_low_raw if est.ci else None,
                            ci_high_raw=est.ci.ci_high_raw if est.ci else None,
                            ci_method_id=est.ci.method.value if est.ci else None,
                        )
                        .with_timing(
                            time_quantum_s=estimates.time_quantum_s,
                            time_classical_s=estimates.time_classical_s,
                        )
                    )

                    if est.observable_id in truth_values:
                        row_builder.with_truth(
                            truth_values[est.observable_id],
                            mode="exact_statevector" if ground_truth else "simulated",
                        )

                    result_set.add(row_builder.build())

    # Step 3: Evaluate tasks
    task_results = {}
    long_form_rows = list(result_set)

    # Pre-group rows by protocol_id for O(N) instead of O(P*N) filtering
    from collections import defaultdict

    rows_by_protocol: dict[str, list] = defaultdict(list)
    for row in long_form_rows:
        rows_by_protocol[row.protocol_id].append(row)

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
        protocol_rows = rows_by_protocol.get(protocol.protocol_id, [])
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
            protocol_rows = rows_by_protocol.get(protocol.protocol_id, [])
            if protocol_rows:
                try:
                    result = task3.evaluate(protocol_rows, truth_values)
                    task_results[f"task3_{protocol.protocol_id}"] = result
                except Exception:
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
                protocol_rows = rows_by_protocol.get(protocol.protocol_id, [])
                if protocol_rows:
                    try:
                        result = task6.evaluate(protocol_rows, truth_values)
                        task_results[f"task6_{protocol.protocol_id}"] = result
                    except Exception as e:
                        print(f"Task 6 evaluation failed for {protocol.protocol_id}: {e}")
        except ImportError:
            pass

    # Step 4: Compute summary statistics
    summary_rows = SummaryAggregator(result_set, epsilon=epsilon).compute_summaries()
    summary = {
        "run_id": run_id,
        "n_protocols": len(protocol_instances),
        "n_shots_grid": n_shots_grid,
        "n_replicates": n_replicates,
        "n_observables": len(observable_set),
        "has_ground_truth": ground_truth is not None,
        "n_long_form_rows": len(result_set),
        "protocols": [p.protocol_id for p in protocol_instances],
    }

    # Per-protocol summaries at largest N (reuse pre-grouped rows)
    max_n = max(n_shots_grid)
    protocol_summaries = {}
    for protocol in protocol_instances:
        # Filter from pre-grouped data instead of full list
        protocol_rows = [
            r for r in rows_by_protocol.get(protocol.protocol_id, []) if r.N_total == max_n
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

        writer = ParquetWriter(output_path)
        long_form_path = writer.write_long_form(result_set)
        summary_path = writer.write_summary(summary_rows)

        import json

        # Save ground truth
        if ground_truth:
            truth_path = output_path / "ground_truth.json"
            with open(truth_path, "w") as f:
                json.dump(
                    {
                        "truth_values": ground_truth.truth_values,
                        "truth_mode": ground_truth.truth_mode,
                        "n_qubits": ground_truth.n_qubits,
                        "circuit_id": ground_truth.circuit_id,
                    },
                    f,
                    indent=2,
                )

        summary_json_path = output_path / "summary.json"
        with open(summary_json_path, "w") as f:

            def convert(obj):
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                if isinstance(obj, (np.float32, np.float64)):
                    return float(obj)
                if isinstance(obj, (np.int32, np.int64)):
                    return int(obj)
                return obj

            json.dump(summary, f, indent=2, default=convert)

        task_results_payload = [output.to_task_result(run_id) for output in task_results.values()]
        task_results_path = None
        if task_results_payload:
            task_results_path = writer.write_task_results(task_results_payload)

        plots_dir = output_path / "plots"
        plots_dir.mkdir(parents=True, exist_ok=True)
        baseline_id = "direct_grouped"
        if baseline_id not in [p.protocol_id for p in protocol_instances]:
            baseline_id = protocol_instances[0].protocol_id
        results_summary = _build_plot_summary(
            result_set,
            summary_rows,
            baseline_id=baseline_id,
            epsilon=epsilon,
        )
        try:
            create_benchmark_report(results_summary, str(plots_dir))
        except ImportError as exc:
            print(f"Warning: Skipping plots (matplotlib unavailable): {exc}")

        manifest = RunManifest(
            run_id=run_id,
            methodology_version=methodology_version,
            created_at=datetime.now(),
            git_commit_hash=get_git_commit_hash(),
            quartumse_version=get_quartumse_version(),
            python_version=get_python_version(),
            environment_lock=get_environment_lock(),
            circuits=[circuit_id],
            observable_sets=[observable_set_id],
            protocols=[p.protocol_id for p in protocol_instances],
            N_grid=n_shots_grid,
            n_replicates=n_replicates,
            noise_profiles=["ideal"],
            long_form_path=str(long_form_path),
            summary_path=str(summary_path),
            task_results_path=str(task_results_path) if task_results_path else None,
            plots_dir=str(plots_dir),
            completed_at=datetime.now(),
            status="completed",
            config={
                "seed_policy": "publication_benchmark",
                "seeds": {"base": seed},
                "epsilon": epsilon,
                "delta": delta,
                "compute_truth": compute_truth,
            },
        )
        writer.write_manifest(manifest)

    return {
        "ground_truth": ground_truth,
        "long_form_results": list(result_set),
        "task_results": task_results,
        "summary": summary,
        "protocol_summaries": protocol_summaries,
    }
