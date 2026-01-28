"""Enhanced benchmark analysis module.

This module implements the improvements from Benchmarking_Improvement.md:
- N* interpolation with power-law fitting
- Per-observable crossover analysis
- Observable property analysis (locality correlation)
- Bootstrap hypothesis testing
- Cost-normalized comparisons
- Multiple pilot fraction analysis
- Sample complexity curves
- K-S tests and statistical comparisons
"""

from .comprehensive import (
    ComprehensiveBenchmarkAnalysis,
    run_comprehensive_analysis,
)
from .cost_normalized import (
    CostModel,
    CostNormalizedResult,
    compute_cost_normalized_metrics,
)
from .crossover import (
    CrossoverAnalysis,
    ObservableCrossover,
    per_observable_crossover,
)
from .interpolation import (
    PowerLawFit,
    fit_power_law,
    interpolate_n_star,
)
from .objective_metrics import (
    ObjectiveAnalysis,
    ObjectiveEstimate,
    bootstrap_objective_ci,
    compute_objective_metrics,
    compute_weighted_objective,
    format_objective_analysis,
)
from .observable_properties import (
    PropertyAnalysis,
    analyze_by_commutation,
    analyze_by_locality,
)
from .pilot_analysis import (
    PilotFractionResult,
    multi_pilot_analysis,
)
from .posthoc_benchmark import (
    CoverageAtBudget,
    PosthocBenchmarkResult,
    PosthocCostAccounting,
    QueryRound,
    compute_coverage_at_budget,
    format_posthoc_result,
    generate_query_rounds,
    run_posthoc_benchmark_from_suite,
    simulate_posthoc_benchmark,
)
from .statistical_tests import (
    StatisticalComparison,
    bootstrap_ci,
    bootstrap_hypothesis_test,
    compare_protocols_statistically,
    ks_test_protocols,
)

__all__ = [
    # Interpolation
    "interpolate_n_star",
    "fit_power_law",
    "PowerLawFit",
    # Crossover
    "per_observable_crossover",
    "CrossoverAnalysis",
    "ObservableCrossover",
    # Observable properties
    "analyze_by_locality",
    "analyze_by_commutation",
    "PropertyAnalysis",
    # Statistical tests
    "bootstrap_ci",
    "bootstrap_hypothesis_test",
    "ks_test_protocols",
    "compare_protocols_statistically",
    "StatisticalComparison",
    # Cost normalized
    "compute_cost_normalized_metrics",
    "CostModel",
    "CostNormalizedResult",
    # Pilot analysis
    "multi_pilot_analysis",
    "PilotFractionResult",
    # Comprehensive
    "ComprehensiveBenchmarkAnalysis",
    "run_comprehensive_analysis",
    # Objective metrics
    "ObjectiveEstimate",
    "ObjectiveAnalysis",
    "compute_weighted_objective",
    "bootstrap_objective_ci",
    "compute_objective_metrics",
    "format_objective_analysis",
    # Post-hoc benchmarking
    "QueryRound",
    "PosthocCostAccounting",
    "PosthocBenchmarkResult",
    "CoverageAtBudget",
    "generate_query_rounds",
    "compute_coverage_at_budget",
    "simulate_posthoc_benchmark",
    "format_posthoc_result",
    "run_posthoc_benchmark_from_suite",
]
