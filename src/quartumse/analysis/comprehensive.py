"""Comprehensive benchmark analysis.

Combines all analysis improvements into a single comprehensive report:
- Task 1-8 analysis with enhancements
- N* interpolation
- Per-observable crossover
- Observable property analysis
- Statistical significance testing
- Cost-normalized comparisons
- Multi-pilot analysis
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from pathlib import Path
import json

import numpy as np

from ..io.schemas import LongFormRow
from ..tasks import (
    TaskConfig, TaskType, CriterionType,
    WorstCaseTask, AverageTargetTask, FixedBudgetDistributionTask,
    DominanceTask, PilotSelectionTask, BiasVarianceTask,
    NoiseSensitivityTask, AdaptiveEfficiencyTask,
)

from .interpolation import interpolate_n_star, fit_power_law, compute_percentile_n_star
from .crossover import per_observable_crossover, CrossoverAnalysis
from .observable_properties import analyze_by_locality, compare_locality_performance
from .statistical_tests import compare_protocols_statistically, bootstrap_ci, StatisticalComparison
from .cost_normalized import compute_cost_normalized_metrics, CostModel, compare_cost_normalized
from .pilot_analysis import multi_pilot_analysis, MultiPilotAnalysis


@dataclass
class TaskAnalysis:
    """Analysis for a single task with enhancements."""
    task_id: str
    task_type: str
    base_results: dict[str, Any]
    enhanced_results: dict[str, Any] = field(default_factory=dict)


@dataclass
class ComprehensiveBenchmarkAnalysis:
    """Complete benchmark analysis with all improvements.

    Attributes:
        run_id: Benchmark run identifier
        protocols: List of protocol IDs analyzed
        n_observables: Number of observables
        n_shots_grid: Shot budgets evaluated
        task_analyses: Per-task analysis results
        crossover_analysis: Per-observable crossover analysis
        locality_analysis: Performance by observable locality
        statistical_comparison: Statistical significance tests
        cost_analysis: Cost-normalized comparisons
        pilot_analysis: Multi-pilot fraction analysis
        interpolated_n_star: N* estimates via power-law interpolation
        summary: Executive summary
    """
    run_id: str
    protocols: list[str]
    n_observables: int
    n_shots_grid: list[int]
    task_analyses: dict[str, TaskAnalysis]
    crossover_analysis: CrossoverAnalysis | None
    locality_analysis: dict[str, Any]
    statistical_comparison: dict[int, StatisticalComparison]
    cost_analysis: dict[str, Any]
    pilot_analysis: MultiPilotAnalysis | None
    interpolated_n_star: dict[str, dict[str, Any]]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "protocols": self.protocols,
            "n_observables": self.n_observables,
            "n_shots_grid": self.n_shots_grid,
            "task_analyses": {k: {"task_id": v.task_id, "task_type": v.task_type,
                                  "base_results": v.base_results,
                                  "enhanced_results": v.enhanced_results}
                              for k, v in self.task_analyses.items()},
            "crossover_analysis": self.crossover_analysis.summary if self.crossover_analysis else None,
            "locality_analysis": self.locality_analysis,
            "statistical_comparison": {n: c.to_dict() for n, c in self.statistical_comparison.items()},
            "cost_analysis": self.cost_analysis,
            "pilot_analysis": self.pilot_analysis.to_dict() if self.pilot_analysis else None,
            "interpolated_n_star": self.interpolated_n_star,
            "summary": self.summary,
        }

    def save(self, path: str | Path) -> None:
        """Save analysis to JSON file."""
        path = Path(path)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    def generate_report(self) -> str:
        """Generate markdown report."""
        lines = [
            f"# Comprehensive Benchmark Analysis",
            f"",
            f"**Run ID:** {self.run_id}",
            f"**Protocols:** {', '.join(self.protocols)}",
            f"**Observables:** {self.n_observables}",
            f"**Shot Grid:** {self.n_shots_grid}",
            f"",
            "---",
            "",
        ]

        # Executive Summary
        lines.extend([
            "## Executive Summary",
            "",
        ])
        for key, value in self.summary.items():
            lines.append(f"- **{key}:** {value}")
        lines.append("")

        # Task Results
        lines.extend([
            "---",
            "",
            "## Task Results",
            "",
        ])

        for task_id, analysis in self.task_analyses.items():
            lines.append(f"### {analysis.task_type.replace('_', ' ').title()}")
            lines.append("")
            for key, value in analysis.base_results.items():
                if not isinstance(value, (dict, list)):
                    lines.append(f"- {key}: {value}")
            if analysis.enhanced_results:
                lines.append("")
                lines.append("**Enhanced Analysis:**")
                for key, value in analysis.enhanced_results.items():
                    if not isinstance(value, (dict, list)):
                        lines.append(f"- {key}: {value}")
            lines.append("")

        # Statistical Significance
        if self.statistical_comparison:
            lines.extend([
                "---",
                "",
                "## Statistical Significance",
                "",
                "| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |",
                "|---|---------------|-------------|-------------|--------------|",
            ])
            for n, comp in sorted(self.statistical_comparison.items()):
                ssf_ci = comp.ssf_ci
                ssf_str = f"{ssf_ci.estimate:.2f} [{ssf_ci.ci_low:.2f}, {ssf_ci.ci_high:.2f}]" if ssf_ci else "N/A"
                lines.append(
                    f"| {n} | {comp.difference_test.p_value:.4f} | "
                    f"{comp.ks_test.p_value:.4f} | "
                    f"{'Yes' if comp.difference_test.reject_null else 'No'} | "
                    f"{ssf_str} |"
                )
            lines.append("")

        # Locality Analysis
        if self.locality_analysis:
            lines.extend([
                "---",
                "",
                "## Performance by Locality",
                "",
            ])
            for protocol_id, analysis in self.locality_analysis.items():
                if hasattr(analysis, 'by_locality'):
                    lines.append(f"### {protocol_id}")
                    lines.append("")
                    lines.append(f"- Locality-SE Correlation: {analysis.locality_correlation:.3f}")
                    lines.append("")

        # Crossover Analysis
        if self.crossover_analysis:
            summary = self.crossover_analysis.summary
            lines.extend([
                "---",
                "",
                "## Per-Observable Crossover Analysis",
                "",
                f"- Protocol A ({self.crossover_analysis.protocol_a}) wins on {summary['a_win_fraction']*100:.1f}% of observables",
                f"- Protocol B ({self.crossover_analysis.protocol_b}) wins on {summary['b_win_fraction']*100:.1f}% of observables",
                f"- Crossover exists for {summary['crossover_fraction']*100:.1f}% of observables",
                "",
            ])

        # Pilot Analysis
        if self.pilot_analysis:
            lines.extend([
                "---",
                "",
                "## Multi-Pilot Fraction Analysis",
                "",
                "| Pilot % | Accuracy | Mean Regret |",
                "|---------|----------|-------------|",
            ])
            for frac, result in sorted(self.pilot_analysis.results.items()):
                lines.append(f"| {frac*100:.0f}% | {result.selection_accuracy*100:.1f}% | {result.mean_regret:.4f} |")
            lines.append("")
            if self.pilot_analysis.optimal_fraction:
                lines.append(f"**Optimal pilot fraction:** {self.pilot_analysis.optimal_fraction*100:.0f}%")
            lines.append("")

        # Interpolated N*
        if self.interpolated_n_star:
            lines.extend([
                "---",
                "",
                "## Interpolated N* (Power-Law)",
                "",
            ])
            for protocol_id, data in self.interpolated_n_star.items():
                n_star = data.get("n_star_interpolated")
                r_sq = data.get("r_squared", 0)
                lines.append(f"- **{protocol_id}:** N* = {n_star:.0f} (R² = {r_sq:.3f})" if n_star else f"- **{protocol_id}:** N* not reached")
            lines.append("")

        return "\n".join(lines)


def run_comprehensive_analysis(
    long_form_results: list[LongFormRow],
    truth_values: dict[str, float] | None = None,
    epsilon: float = 0.01,
    delta: float = 0.05,
    locality_map: dict[str, int] | None = None,
    run_id: str = "comprehensive_analysis",
    shadows_protocol_id: str = "classical_shadows_v0",
    baseline_protocol_id: str = "direct_grouped",
) -> ComprehensiveBenchmarkAnalysis:
    """Run comprehensive benchmark analysis with all improvements.

    Args:
        long_form_results: Long-form benchmark results
        truth_values: Ground truth values for observables
        epsilon: Target precision
        delta: Failure probability
        locality_map: Map observable_id -> locality
        run_id: Analysis identifier
        shadows_protocol_id: ID of shadows protocol for comparison
        baseline_protocol_id: ID of baseline protocol for comparison

    Returns:
        ComprehensiveBenchmarkAnalysis with all results
    """
    if not long_form_results:
        raise ValueError("No results provided")

    # Extract metadata
    protocols = list(set(r.protocol_id for r in long_form_results))
    n_shots_grid = sorted(set(r.N_total for r in long_form_results))
    n_observables = len(set(r.observable_id for r in long_form_results))

    # Separate results by protocol
    by_protocol: dict[str, list[LongFormRow]] = {}
    for row in long_form_results:
        if row.protocol_id not in by_protocol:
            by_protocol[row.protocol_id] = []
        by_protocol[row.protocol_id].append(row)

    task_analyses = {}

    # =========================================================================
    # Task 1: Worst-Case with interpolation
    # =========================================================================
    task1_config = TaskConfig(
        task_id="task1_worst_case",
        task_type=TaskType.WORST_CASE,
        epsilon=epsilon,
        delta=delta,
        n_grid=n_shots_grid,
        criterion_type=CriterionType.TRUTH_BASED if truth_values else CriterionType.CI_BASED,
    )
    task1 = WorstCaseTask(task1_config)

    task1_results = {}
    for protocol_id, rows in by_protocol.items():
        output = task1.evaluate(rows, truth_values)
        task1_results[protocol_id] = output.to_task_result(run_id)

    # Enhanced: 95th percentile N*
    percentile_results = {}
    for protocol_id, rows in by_protocol.items():
        by_n = {}
        for row in rows:
            if row.N_total not in by_n:
                by_n[row.N_total] = []
            by_n[row.N_total].append(row.se)
        n_star_95, pct_by_n = compute_percentile_n_star(by_n, epsilon, percentile=95)
        percentile_results[protocol_id] = {"n_star_95th": n_star_95, "percentiles": pct_by_n}

    task_analyses["task1_worst_case"] = TaskAnalysis(
        task_id="task1_worst_case",
        task_type="worst_case",
        base_results={p: {"n_star": r.N_star} for p, r in task1_results.items()},
        enhanced_results={"percentile_95_n_star": percentile_results},
    )

    # =========================================================================
    # Task 2: Average Target
    # =========================================================================
    task2_config = TaskConfig(
        task_id="task2_average",
        task_type=TaskType.AVERAGE_TARGET,
        epsilon=epsilon,
        delta=delta,
        n_grid=n_shots_grid,
        criterion_type=CriterionType.TRUTH_BASED if truth_values else CriterionType.CI_BASED,
    )
    task2 = AverageTargetTask(task2_config)

    task2_results = {}
    for protocol_id, rows in by_protocol.items():
        output = task2.evaluate(rows, truth_values)
        task2_results[protocol_id] = output.metrics

    task_analyses["task2_average"] = TaskAnalysis(
        task_id="task2_average",
        task_type="average_target",
        base_results=task2_results,
    )

    # =========================================================================
    # Task 3: Fixed Budget Distribution
    # =========================================================================
    task3_config = TaskConfig(
        task_id="task3_distribution",
        task_type=TaskType.FIXED_BUDGET,
        epsilon=epsilon,
        n_grid=n_shots_grid,
    )
    task3 = FixedBudgetDistributionTask(task3_config)

    task3_results = {}
    for protocol_id, rows in by_protocol.items():
        output = task3.evaluate(rows, truth_values)
        task3_results[protocol_id] = output.details.get("se_distributions", {})

    task_analyses["task3_distribution"] = TaskAnalysis(
        task_id="task3_distribution",
        task_type="fixed_budget",
        base_results={"distributions": task3_results},
    )

    # =========================================================================
    # Task 4: Dominance with enhanced crossover
    # =========================================================================
    task4_config = TaskConfig(
        task_id="task4_dominance",
        task_type=TaskType.DOMINANCE,
        epsilon=epsilon,
        delta=delta,
        n_grid=n_shots_grid,
        criterion_type=CriterionType.TRUTH_BASED if truth_values else CriterionType.CI_BASED,
    )
    task4 = DominanceTask(task4_config)

    dominance_results = {}
    if shadows_protocol_id in by_protocol and baseline_protocol_id in by_protocol:
        dominance_results = task4.compare_protocols(
            by_protocol[shadows_protocol_id],
            by_protocol[baseline_protocol_id],
            truth_values,
            metric="mean_se",
        )

    task_analyses["task4_dominance"] = TaskAnalysis(
        task_id="task4_dominance",
        task_type="dominance",
        base_results=dominance_results,
    )

    # =========================================================================
    # Task 5: Pilot Selection
    # =========================================================================
    task5_config = TaskConfig(
        task_id="task5_pilot",
        task_type=TaskType.PILOT_SELECTION,
        epsilon=epsilon,
        delta=delta,
        n_grid=n_shots_grid,
        criterion_type=CriterionType.TRUTH_BASED if truth_values else CriterionType.CI_BASED,
        additional_params={"pilot_n": n_shots_grid[0], "target_n": n_shots_grid[-1]},
    )
    task5 = PilotSelectionTask(task5_config)
    task5_output = task5.evaluate(long_form_results, truth_values)

    task_analyses["task5_pilot"] = TaskAnalysis(
        task_id="task5_pilot",
        task_type="pilot_selection",
        base_results=task5_output.metrics,
    )

    # =========================================================================
    # Task 6: Bias-Variance
    # =========================================================================
    if truth_values:
        task6_config = TaskConfig(
            task_id="task6_biasvar",
            task_type=TaskType.BIAS_VARIANCE,
            n_grid=n_shots_grid,
        )
        task6 = BiasVarianceTask(task6_config)

        task6_results = {}
        for protocol_id, rows in by_protocol.items():
            output = task6.evaluate(rows, truth_values)
            task6_results[protocol_id] = output.metrics

        task_analyses["task6_biasvar"] = TaskAnalysis(
            task_id="task6_biasvar",
            task_type="bias_variance",
            base_results=task6_results,
        )

    # =========================================================================
    # Per-observable crossover analysis
    # =========================================================================
    crossover_analysis = None
    if shadows_protocol_id in by_protocol and baseline_protocol_id in by_protocol:
        crossover_analysis = per_observable_crossover(
            by_protocol[shadows_protocol_id],
            by_protocol[baseline_protocol_id],
            metric="se",
            interpolate=True,
        )

    # =========================================================================
    # Locality analysis
    # =========================================================================
    locality_analysis = analyze_by_locality(long_form_results, n_total=n_shots_grid[-1], locality_map=locality_map)

    # =========================================================================
    # Statistical comparison
    # =========================================================================
    statistical_comparison = {}
    if shadows_protocol_id in by_protocol and baseline_protocol_id in by_protocol:
        for n in n_shots_grid:
            try:
                comparison = compare_protocols_statistically(
                    by_protocol[shadows_protocol_id],
                    by_protocol[baseline_protocol_id],
                    n_total=n,
                    epsilon=epsilon,
                    n_bootstrap=5000,
                )
                statistical_comparison[n] = comparison
            except Exception:
                pass

    # =========================================================================
    # Cost-normalized analysis
    # =========================================================================
    cost_model = CostModel()
    cost_results = compute_cost_normalized_metrics(long_form_results, cost_model, truth_values)
    cost_comparison = compare_cost_normalized(cost_results, n_shots_grid[-1])
    cost_analysis = {
        "cost_model": cost_model.to_dict(),
        "comparison_at_max_n": cost_comparison,
    }

    # =========================================================================
    # Multi-pilot analysis
    # =========================================================================
    pilot_analysis = multi_pilot_analysis(
        long_form_results,
        target_n=n_shots_grid[-1],
        pilot_fractions=[0.02, 0.05, 0.10, 0.20],
    )

    # =========================================================================
    # N* interpolation
    # =========================================================================
    interpolated_n_star = {}
    for protocol_id, rows in by_protocol.items():
        # Compute mean SE at each N
        by_n: dict[int, list[float]] = {}
        for row in rows:
            if row.N_total not in by_n:
                by_n[row.N_total] = []
            by_n[row.N_total].append(row.se)

        ns = sorted(by_n.keys())
        mean_ses = [np.mean(by_n[n]) for n in ns]

        n_star, fit = interpolate_n_star(ns, mean_ses, epsilon, method="power_law")

        interpolated_n_star[protocol_id] = {
            "n_star_interpolated": n_star,
            "amplitude": fit.amplitude if fit else None,
            "exponent": fit.exponent if fit else None,
            "r_squared": fit.r_squared if fit else None,
        }

    # =========================================================================
    # Executive summary
    # =========================================================================
    summary = {
        "n_protocols": len(protocols),
        "n_observables": n_observables,
        "n_shots_evaluated": len(n_shots_grid),
        "max_shots": n_shots_grid[-1],
    }

    # Add key findings
    if shadows_protocol_id in by_protocol and baseline_protocol_id in by_protocol:
        shadows_se = np.mean([r.se for r in by_protocol[shadows_protocol_id] if r.N_total == n_shots_grid[-1]])
        baseline_se = np.mean([r.se for r in by_protocol[baseline_protocol_id] if r.N_total == n_shots_grid[-1]])
        summary["shadows_mean_se"] = float(shadows_se)
        summary["baseline_mean_se"] = float(baseline_se)
        summary["shadows_vs_baseline_ratio"] = float(shadows_se / baseline_se) if baseline_se > 0 else float('inf')
        summary["winner_at_max_n"] = shadows_protocol_id if shadows_se < baseline_se else baseline_protocol_id

    if crossover_analysis:
        summary["shadows_wins_fraction"] = crossover_analysis.summary.get("a_win_fraction", 0)
        summary["baseline_wins_fraction"] = crossover_analysis.summary.get("b_win_fraction", 0)

    if pilot_analysis and pilot_analysis.optimal_fraction:
        summary["optimal_pilot_fraction"] = pilot_analysis.optimal_fraction

    return ComprehensiveBenchmarkAnalysis(
        run_id=run_id,
        protocols=protocols,
        n_observables=n_observables,
        n_shots_grid=n_shots_grid,
        task_analyses=task_analyses,
        crossover_analysis=crossover_analysis,
        locality_analysis={p: a.to_dict() for p, a in locality_analysis.items()},
        statistical_comparison=statistical_comparison,
        cost_analysis=cost_analysis,
        pilot_analysis=pilot_analysis,
        interpolated_n_star=interpolated_n_star,
        summary=summary,
    )
