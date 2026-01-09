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

from .interpolation import (
    interpolate_n_star,
    fit_power_law,
    PowerLawFit,
)
from .crossover import (
    per_observable_crossover,
    CrossoverAnalysis,
    ObservableCrossover,
)
from .observable_properties import (
    analyze_by_locality,
    analyze_by_commutation,
    PropertyAnalysis,
)
from .statistical_tests import (
    bootstrap_ci,
    bootstrap_hypothesis_test,
    ks_test_protocols,
    StatisticalComparison,
)
from .cost_normalized import (
    compute_cost_normalized_metrics,
    CostModel,
    CostNormalizedResult,
)
from .pilot_analysis import (
    multi_pilot_analysis,
    PilotFractionResult,
)
from .comprehensive import (
    ComprehensiveBenchmarkAnalysis,
    run_comprehensive_analysis,
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
]
