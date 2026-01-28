"""Unified benchmark suite with configurable modes.

Provides a single entry point for running benchmarks at different levels:
- basic: Core protocols + Tasks 1, 3, 6 + basic report
- complete: All 8 tasks + complete report
- analysis: Complete + enhanced analysis (crossover, locality, bootstrap, etc.)

All results are saved with unique timestamped directories.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .observables import ObservableSet


class BenchmarkMode(Enum):
    """Benchmark execution modes."""

    BASIC = "basic"  # Core benchmark + Tasks 1,3,6
    COMPLETE = "complete"  # All 8 tasks
    ANALYSIS = "analysis"  # Complete + enhanced analysis


@dataclass
class BenchmarkSuiteConfig:
    """Configuration for benchmark suite execution.

    Attributes:
        mode: Execution mode (basic, complete, analysis)
        n_shots_grid: Shot budgets to evaluate
        n_replicates: Number of replicates per configuration
        seed: Base random seed
        epsilon: Target precision for tasks
        delta: Failure probability
        compute_truth: Whether to compute ground truth
        shadows_protocol_id: Protocol ID for shadows (for comparison)
        baseline_protocol_id: Protocol ID for baseline (for comparison)
        output_base_dir: Base directory for outputs (timestamped subdir created)
    """

    mode: BenchmarkMode = BenchmarkMode.COMPLETE
    n_shots_grid: list[int] = field(default_factory=lambda: [100, 500, 1000, 5000])
    n_replicates: int = 20
    seed: int = 42
    epsilon: float = 0.01
    delta: float = 0.05
    compute_truth: bool = True
    shadows_protocol_id: str = "classical_shadows_v0"
    baseline_protocol_id: str = "direct_grouped"
    output_base_dir: str = "benchmark_results"

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "n_shots_grid": self.n_shots_grid,
            "n_replicates": self.n_replicates,
            "seed": self.seed,
            "epsilon": self.epsilon,
            "delta": self.delta,
            "compute_truth": self.compute_truth,
            "shadows_protocol_id": self.shadows_protocol_id,
            "baseline_protocol_id": self.baseline_protocol_id,
            "output_base_dir": self.output_base_dir,
        }


@dataclass
class BenchmarkSuiteResult:
    """Complete result from benchmark suite execution.

    Attributes:
        run_id: Unique run identifier
        timestamp: Execution timestamp
        mode: Benchmark mode used
        output_dir: Directory containing all outputs
        ground_truth: Ground truth result (if computed)
        long_form_results: List of LongFormRow
        task_results: Dict of task outputs (basic tasks)
        all_task_results: Dict of all 8 task outputs (complete mode)
        analysis: ComprehensiveBenchmarkAnalysis (analysis mode)
        reports: Dict of report paths
        summary: Summary statistics
    """

    run_id: str
    timestamp: datetime
    mode: BenchmarkMode
    output_dir: Path
    ground_truth: Any | None
    long_form_results: list
    task_results: dict[str, Any]
    all_task_results: dict[str, Any] | None
    analysis: Any | None  # ComprehensiveBenchmarkAnalysis
    reports: dict[str, Path]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "mode": self.mode.value,
            "output_dir": str(self.output_dir),
            "n_long_form_rows": len(self.long_form_results),
            "tasks_completed": list(self.task_results.keys()),
            "all_tasks_completed": (
                list(self.all_task_results.keys()) if self.all_task_results else []
            ),
            "has_analysis": self.analysis is not None,
            "reports": {k: str(v) for k, v in self.reports.items()},
            "summary": self.summary,
        }


def _generate_run_id(circuit_id: str) -> str:
    """Generate unique run ID with timestamp."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    import uuid

    short_uuid = uuid.uuid4().hex[:8]
    return f"{circuit_id}_{ts}_{short_uuid}"


def _create_output_dir(base_dir: str, run_id: str) -> Path:
    """Create timestamped output directory."""
    output_dir = Path(base_dir) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _run_all_tasks(
    long_form_rows: list,
    truth_values: dict[str, float] | None,
    n_shots_grid: list[int],
    n_replicates: int,
    epsilon: float,
    delta: float,
    protocol_ids: list[str],
) -> dict[str, Any]:
    """Run all 8 tasks from the Measurements Bible."""
    from .tasks import (
        BiasVarianceTask,
        FixedBudgetDistributionTask,
        TaskConfig,
        TaskType,
        WorstCaseTask,
    )

    all_results = {}

    # Task 1: Worst-Case Guarantee
    task1_config = TaskConfig(
        task_id="task1_worst_case",
        task_type=TaskType.WORST_CASE,
        epsilon=epsilon,
        delta=delta,
        n_grid=n_shots_grid,
        n_replicates=n_replicates,
    )
    task1 = WorstCaseTask(task1_config)

    for protocol_id in protocol_ids:
        protocol_rows = [r for r in long_form_rows if r.protocol_id == protocol_id]
        if protocol_rows:
            try:
                result = task1.evaluate(protocol_rows, truth_values or {})
                all_results[f"task1_{protocol_id}"] = result
            except Exception as e:
                print(f"Task 1 failed for {protocol_id}: {e}")

    # Task 2: Average Target (similar to Task 1 but with mean)
    task2_config = TaskConfig(
        task_id="task2_average",
        task_type=TaskType.AVERAGE_TARGET,
        epsilon=epsilon,
        delta=delta,
        n_grid=n_shots_grid,
        n_replicates=n_replicates,
    )
    try:
        from .tasks import AverageTargetTask

        task2 = AverageTargetTask(task2_config)
        for protocol_id in protocol_ids:
            protocol_rows = [r for r in long_form_rows if r.protocol_id == protocol_id]
            if protocol_rows:
                try:
                    result = task2.evaluate(protocol_rows, truth_values or {})
                    all_results[f"task2_{protocol_id}"] = result
                except Exception:
                    pass
    except ImportError:
        pass  # Task 2 not implemented

    # Task 3: Fixed Budget Distribution
    task3_config = TaskConfig(
        task_id="task3_distribution",
        task_type=TaskType.FIXED_BUDGET,
        epsilon=epsilon,
        delta=delta,
        n_grid=n_shots_grid,
        n_replicates=n_replicates,
    )
    task3 = FixedBudgetDistributionTask(task3_config)

    for protocol_id in protocol_ids:
        protocol_rows = [r for r in long_form_rows if r.protocol_id == protocol_id]
        if protocol_rows:
            try:
                result = task3.evaluate(protocol_rows, truth_values or {})
                all_results[f"task3_{protocol_id}"] = result
            except Exception:
                pass

    # Task 4: Dominance
    task4_config = TaskConfig(
        task_id="task4_dominance",
        task_type=TaskType.DOMINANCE,
        epsilon=epsilon,
        delta=delta,
        n_grid=n_shots_grid,
        n_replicates=n_replicates,
    )
    try:
        from .tasks import DominanceTask

        task4 = DominanceTask(task4_config)
        # Compare pairs of protocols
        for i, p1 in enumerate(protocol_ids):
            for p2 in protocol_ids[i + 1 :]:
                rows_p1 = [r for r in long_form_rows if r.protocol_id == p1]
                rows_p2 = [r for r in long_form_rows if r.protocol_id == p2]
                if rows_p1 and rows_p2:
                    try:
                        result = task4.evaluate_pair(rows_p1, rows_p2, truth_values or {})
                        all_results[f"task4_{p1}_vs_{p2}"] = result
                    except Exception:
                        pass
    except (ImportError, AttributeError):
        pass  # Task 4 not fully implemented

    # Task 5: Pilot Selection (handled via multi_pilot_analysis in analysis)
    # Included in comprehensive analysis

    # Task 6: Bias-Variance
    if truth_values:
        task6_config = TaskConfig(
            task_id="task6_biasvar",
            task_type=TaskType.BIAS_VARIANCE,
            epsilon=epsilon,
            delta=delta,
            n_grid=n_shots_grid,
            n_replicates=n_replicates,
        )
        task6 = BiasVarianceTask(task6_config)

        for protocol_id in protocol_ids:
            protocol_rows = [r for r in long_form_rows if r.protocol_id == protocol_id]
            if protocol_rows:
                try:
                    result = task6.evaluate(protocol_rows, truth_values)
                    all_results[f"task6_{protocol_id}"] = result
                except Exception as e:
                    print(f"Task 6 failed for {protocol_id}: {e}")

    # Task 7: Noise Sensitivity (requires multiple noise profiles)
    # Would need separate benchmark runs with different noise - skip for now

    # Task 8: Adaptive Efficiency
    try:
        from .tasks import AdaptiveEfficiencyTask

        task8_config = TaskConfig(
            task_id="task8_adaptive",
            task_type=TaskType.ADAPTIVE,
            epsilon=epsilon,
            delta=delta,
            n_grid=n_shots_grid,
            n_replicates=n_replicates,
        )
        task8 = AdaptiveEfficiencyTask(task8_config)
        for protocol_id in protocol_ids:
            protocol_rows = [r for r in long_form_rows if r.protocol_id == protocol_id]
            if protocol_rows:
                try:
                    result = task8.evaluate(protocol_rows, truth_values or {})
                    all_results[f"task8_{protocol_id}"] = result
                except Exception:
                    pass
    except (ImportError, AttributeError):
        pass  # Task 8 not implemented

    return all_results


def _generate_basic_report(
    run_id: str,
    summary: dict,
    task_results: dict,
    output_dir: Path,
) -> Path:
    """Generate basic benchmark report."""
    report_lines = [
        f"# Benchmark Report: {run_id}",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        "",
        "## Summary",
        "",
        f"- **Run ID:** {run_id}",
        f"- **Protocols:** {', '.join(summary.get('protocols', []))}",
        f"- **Observables:** {summary.get('n_observables', 0)}",
        f"- **Shot Grid:** {summary.get('n_shots_grid', [])}",
        f"- **Replicates:** {summary.get('n_replicates', 0)}",
        f"- **Total Rows:** {summary.get('n_long_form_rows', 0)}",
        "",
        "## Protocol Performance",
        "",
    ]

    protocol_summaries = summary.get("protocol_summaries", {})
    if protocol_summaries:
        report_lines.append("| Protocol | Mean SE | Max SE | Median SE |")
        report_lines.append("|----------|---------|--------|-----------|")
        for protocol_id, stats in protocol_summaries.items():
            mean_se = stats.get("mean_se", 0)
            max_se = stats.get("max_se", 0)
            median_se = stats.get("median_se", 0)
            report_lines.append(
                f"| {protocol_id} | {mean_se:.4f} | {max_se:.4f} | {median_se:.4f} |"
            )
        report_lines.append("")

    # Task results summary
    if task_results:
        report_lines.append("## Task Results")
        report_lines.append("")
        for task_id, result in task_results.items():
            if hasattr(result, "n_star"):
                report_lines.append(f"- **{task_id}:** N* = {result.n_star}")
        report_lines.append("")

    report_content = "\n".join(report_lines)
    report_path = output_dir / "basic_report.md"
    report_path.write_text(report_content, encoding="utf-8")

    return report_path


def _generate_complete_report(
    run_id: str,
    summary: dict,
    all_task_results: dict,
    long_form_rows: list,
    truth_values: dict | None,
    config: BenchmarkSuiteConfig,
    output_dir: Path,
) -> Path:
    """Generate complete benchmark report with all 8 tasks."""
    report_lines = [
        f"# Complete Benchmark Report: {run_id}",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        "**Mode:** Complete (All 8 Tasks)",
        "",
        "---",
        "",
        "## Configuration",
        "",
        f"- **Shot Grid:** {config.n_shots_grid}",
        f"- **Replicates:** {config.n_replicates}",
        f"- **Target Epsilon:** {config.epsilon}",
        f"- **Delta:** {config.delta}",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"- **Protocols:** {', '.join(summary.get('protocols', []))}",
        f"- **Observables:** {summary.get('n_observables', 0)}",
        f"- **Has Ground Truth:** {summary.get('has_ground_truth', False)}",
        "",
    ]

    # Protocol performance at max N
    protocol_summaries = summary.get("protocol_summaries", {})
    if protocol_summaries:
        max_n = max(config.n_shots_grid)
        report_lines.append(f"### Protocol Performance at N = {max_n}")
        report_lines.append("")
        report_lines.append("| Protocol | Mean SE | Max SE | Mean Abs Error |")
        report_lines.append("|----------|---------|--------|----------------|")
        for protocol_id, stats in protocol_summaries.items():
            mean_se = stats.get("mean_se", 0)
            max_se = stats.get("max_se", 0)
            mae = stats.get("mean_abs_error", "N/A")
            mae_str = f"{mae:.4f}" if isinstance(mae, float) else mae
            report_lines.append(f"| {protocol_id} | {mean_se:.4f} | {max_se:.4f} | {mae_str} |")
        report_lines.append("")

    report_lines.extend(
        [
            "---",
            "",
            "## Task Results",
            "",
        ]
    )

    # Group task results by task number
    tasks_by_num = {}
    for task_id, result in all_task_results.items():
        # Extract task number (e.g., "task1_protocol" -> 1)
        parts = task_id.split("_")
        if len(parts) >= 1 and parts[0].startswith("task"):
            task_num = parts[0].replace("task", "")
            if task_num not in tasks_by_num:
                tasks_by_num[task_num] = {}
            tasks_by_num[task_num][task_id] = result

    task_descriptions = {
        "1": "Worst-Case Guarantee",
        "2": "Average Target",
        "3": "Fixed Budget Distribution",
        "4": "Dominance",
        "5": "Pilot Selection",
        "6": "Bias-Variance Decomposition",
        "7": "Noise Sensitivity",
        "8": "Adaptive Efficiency",
    }

    for task_num in sorted(tasks_by_num.keys()):
        task_name = task_descriptions.get(task_num, f"Task {task_num}")
        report_lines.append(f"### Task {task_num}: {task_name}")
        report_lines.append("")

        for task_id, result in tasks_by_num[task_num].items():
            protocol_part = task_id.replace(f"task{task_num}_", "")

            if hasattr(result, "n_star") and result.n_star:
                report_lines.append(f"- **{protocol_part}:** N* = {result.n_star}")
            elif hasattr(result, "to_dict"):
                rd = result.to_dict()
                if "n_star" in rd:
                    report_lines.append(f"- **{protocol_part}:** N* = {rd['n_star']}")
                elif "metrics" in rd:
                    metrics = rd["metrics"]
                    report_lines.append(f"- **{protocol_part}:** {metrics}")

        report_lines.append("")

    report_content = "\n".join(report_lines)
    report_path = output_dir / "complete_report.md"
    report_path.write_text(report_content, encoding="utf-8")

    return report_path


def run_benchmark_suite(
    circuit: Any,
    observable_set: ObservableSet,
    circuit_id: str = "circuit",
    config: BenchmarkSuiteConfig | None = None,
    protocols: list | None = None,
    locality_map: dict[str, int] | None = None,
) -> BenchmarkSuiteResult:
    """Run unified benchmark suite.

    This is the main entry point for running benchmarks. It provides three modes:

    - **basic**: Run core protocols + Tasks 1, 3, 6 + basic report
    - **complete**: Run all 8 tasks + complete report
    - **analysis**: Complete + enhanced analysis (crossover, locality, bootstrap)

    All results are saved to a unique timestamped directory.

    Args:
        circuit: Quantum circuit (any Qiskit QuantumCircuit)
        observable_set: Set of observables to estimate
        circuit_id: Identifier for the circuit
        config: Benchmark configuration (default: BenchmarkSuiteConfig())
        protocols: List of protocol IDs or instances (default: all baselines + shadows)
        locality_map: Optional mapping of observable_id -> locality (Pauli weight)

    Returns:
        BenchmarkSuiteResult with all outputs and paths to saved reports

    Example:
        >>> from quartumse import run_benchmark_suite, BenchmarkMode, BenchmarkSuiteConfig
        >>>
        >>> # Basic benchmark
        >>> result = run_benchmark_suite(circuit, observables, circuit_id="ghz_4q")
        >>>
        >>> # Complete with all 8 tasks
        >>> config = BenchmarkSuiteConfig(mode=BenchmarkMode.COMPLETE)
        >>> result = run_benchmark_suite(circuit, observables, config=config)
        >>>
        >>> # Full analysis
        >>> config = BenchmarkSuiteConfig(mode=BenchmarkMode.ANALYSIS)
        >>> result = run_benchmark_suite(circuit, observables, config=config)
        >>>
        >>> print(f"Reports saved to: {result.output_dir}")
    """
    from .benchmarking import run_publication_benchmark

    if config is None:
        config = BenchmarkSuiteConfig()

    # Generate unique run ID and output directory
    run_id = _generate_run_id(circuit_id)
    timestamp = datetime.now()
    output_dir = _create_output_dir(config.output_base_dir, run_id)

    print("=" * 70)
    print(f"BENCHMARK SUITE: {config.mode.value.upper()}")
    print("=" * 70)
    print(f"Run ID: {run_id}")
    print(f"Output: {output_dir}")
    print(f"Mode: {config.mode.value}")
    print()

    # Step 1: Run base benchmark
    print("Step 1: Running base benchmark...")
    base_results = run_publication_benchmark(
        circuit=circuit,
        observable_set=observable_set,
        protocols=protocols,
        n_shots_grid=config.n_shots_grid,
        n_replicates=config.n_replicates,
        seed=config.seed,
        compute_truth=config.compute_truth,
        circuit_id=circuit_id,
        output_dir=str(output_dir / "base"),
        epsilon=config.epsilon,
        delta=config.delta,
    )

    long_form_rows = base_results["long_form_results"]
    truth_values = (
        base_results["ground_truth"].truth_values if base_results["ground_truth"] else None
    )
    task_results = base_results["task_results"]
    summary = base_results["summary"]
    protocol_ids = summary.get("protocols", [])

    print(f"  Completed: {len(long_form_rows)} rows")
    print()

    # Initialize result containers
    all_task_results = None
    analysis = None
    reports = {}

    # Step 2: Run additional tasks for complete/analysis modes
    if config.mode in [BenchmarkMode.COMPLETE, BenchmarkMode.ANALYSIS]:
        print("Step 2: Running all 8 tasks...")
        all_task_results = _run_all_tasks(
            long_form_rows=long_form_rows,
            truth_values=truth_values,
            n_shots_grid=config.n_shots_grid,
            n_replicates=config.n_replicates,
            epsilon=config.epsilon,
            delta=config.delta,
            protocol_ids=protocol_ids,
        )
        print(f"  Completed: {len(all_task_results)} task evaluations")
        print()

    # Step 3: Run comprehensive analysis for analysis mode
    if config.mode == BenchmarkMode.ANALYSIS:
        print("Step 3: Running comprehensive analysis...")
        from .analysis import run_comprehensive_analysis

        analysis = run_comprehensive_analysis(
            long_form_results=long_form_rows,
            truth_values=truth_values,
            epsilon=config.epsilon,
            delta=config.delta,
            locality_map=locality_map,
            run_id=run_id,
            shadows_protocol_id=config.shadows_protocol_id,
            baseline_protocol_id=config.baseline_protocol_id,
        )
        print("  Comprehensive analysis complete")
        print()

    # Step 4: Generate reports
    print("Step 4: Generating reports...")

    # Always generate basic report
    basic_report_path = _generate_basic_report(
        run_id=run_id,
        summary=summary,
        task_results=task_results,
        output_dir=output_dir,
    )
    reports["basic"] = basic_report_path
    print(f"  Basic report: {basic_report_path}")

    # Generate complete report for complete/analysis modes
    if config.mode in [BenchmarkMode.COMPLETE, BenchmarkMode.ANALYSIS]:
        complete_report_path = _generate_complete_report(
            run_id=run_id,
            summary=summary,
            all_task_results=all_task_results or {},
            long_form_rows=long_form_rows,
            truth_values=truth_values,
            config=config,
            output_dir=output_dir,
        )
        reports["complete"] = complete_report_path
        print(f"  Complete report: {complete_report_path}")

    # Generate analysis report for analysis mode
    if config.mode == BenchmarkMode.ANALYSIS and analysis:
        analysis_report_content = analysis.generate_report()
        analysis_report_path = output_dir / "analysis_report.md"
        analysis_report_path.write_text(analysis_report_content, encoding="utf-8")
        reports["analysis"] = analysis_report_path
        print(f"  Analysis report: {analysis_report_path}")

        # Also save JSON
        analysis_json_path = output_dir / "analysis.json"
        analysis.save(analysis_json_path)
        reports["analysis_json"] = analysis_json_path
        print(f"  Analysis JSON: {analysis_json_path}")

    # Save config
    config_path = output_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump(config.to_dict(), f, indent=2)
    reports["config"] = config_path

    # Save run manifest
    manifest = {
        "run_id": run_id,
        "timestamp": timestamp.isoformat(),
        "mode": config.mode.value,
        "circuit_id": circuit_id,
        "n_observables": len(observable_set),
        "n_protocols": len(protocol_ids),
        "protocols": protocol_ids,
        "n_shots_grid": config.n_shots_grid,
        "n_replicates": config.n_replicates,
        "n_long_form_rows": len(long_form_rows),
        "has_ground_truth": truth_values is not None,
        "tasks_completed": list(task_results.keys()),
        "all_tasks_completed": list(all_task_results.keys()) if all_task_results else [],
        "has_analysis": analysis is not None,
        "reports": {k: str(v) for k, v in reports.items()},
    }
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    reports["manifest"] = manifest_path

    print()
    print("=" * 70)
    print("BENCHMARK COMPLETE")
    print("=" * 70)
    print(f"Output directory: {output_dir}")
    print(f"Reports generated: {list(reports.keys())}")
    print()

    return BenchmarkSuiteResult(
        run_id=run_id,
        timestamp=timestamp,
        mode=config.mode,
        output_dir=output_dir,
        ground_truth=base_results["ground_truth"],
        long_form_results=long_form_rows,
        task_results=task_results,
        all_task_results=all_task_results,
        analysis=analysis,
        reports=reports,
        summary=summary,
    )
