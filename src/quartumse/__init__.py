"""
QuartumSE - Quantum Measurement Optimization & Observability Platform

A vendor-neutral framework for running quantum experiments with:
- Classical shadows for shot-efficient observable estimation
- Rigorous error mitigation and confidence intervals
- Full provenance tracking and reproducibility
- Cross-platform backend support (IBM, AWS, and more)
- Publication-grade benchmarking per Measurements Bible

License: Apache 2.0
"""

__version__ = "0.2.0"
__author__ = "QuartumSE Team"

# Core API exports (existing)
from quartumse.estimator import Estimator, ShadowEstimator
from quartumse.reporting import ProvenanceManifest, Report
from quartumse.shadows import ClassicalShadows, ShadowConfig

# Benchmarking API exports (Measurements Bible)
from quartumse.observables import (
    Observable,
    ObservableSet,
    generate_observable_set,
    # Suite classes
    ObservableSuite,
    ObjectiveType,
    SuiteType,
    # Suite builders
    make_ghz_suites,
    make_bell_suites,
    make_ising_suites,
    make_qaoa_ring_suites,
    make_phase_sensing_suites,
    make_chemistry_suites,
    make_stress_suite,
    make_posthoc_library,
    make_commuting_suite,
    # Pauli generators
    generate_all_k_local,
    sample_random_paulis,
)
from quartumse.protocols import (
    Protocol,
    Estimates,
    DirectNaiveProtocol,
    DirectGroupedProtocol,
    DirectOptimizedProtocol,
    get_protocol,
    list_protocols,
)
from quartumse.stats import (
    normal_ci,
    construct_ci,
    construct_simultaneous_cis,
    FWERMethod,
)
from quartumse.tasks import (
    TaskConfig,
    TaskType,
    SweepConfig,
    SweepOrchestrator,
)
from quartumse.io import (
    LongFormRow,
    SummaryRow,
    ParquetWriter,
    ParquetReader,
)
from quartumse.noise import (
    NoiseProfile,
    get_profile,
    list_profiles,
)
from quartumse.viz import (
    plot_attainment_curves,
    plot_ssf_comparison,
    ReportBuilder,
)

# Enhanced Analysis (Benchmarking Improvements)
from quartumse.analysis import (
    run_comprehensive_analysis,
    ComprehensiveBenchmarkAnalysis,
    interpolate_n_star,
    fit_power_law,
    per_observable_crossover,
    analyze_by_locality,
    bootstrap_ci,
    bootstrap_hypothesis_test,
    ks_test_protocols,
    compare_protocols_statistically,
    compute_cost_normalized_metrics,
    CostModel,
    multi_pilot_analysis,
    # Objective metrics (Work Item 4)
    ObjectiveEstimate,
    ObjectiveAnalysis,
    compute_objective_metrics,
    format_objective_analysis,
    # Post-hoc benchmarking (Work Item 3)
    PosthocBenchmarkResult,
    run_posthoc_benchmark_from_suite,
    format_posthoc_result,
)

# Unified Benchmark Suite
from quartumse.benchmark_suite import (
    run_benchmark_suite,
    BenchmarkMode,
    BenchmarkSuiteConfig,
    BenchmarkSuiteResult,
)

__all__ = [
    # Version
    "__version__",
    "__author__",
    # Core classes (existing)
    "Estimator",
    "ShadowEstimator",
    "ClassicalShadows",
    "ShadowConfig",
    "ProvenanceManifest",
    "Report",
    # Observables
    "Observable",
    "ObservableSet",
    "generate_observable_set",
    # Suites (Benchmarking)
    "ObservableSuite",
    "ObjectiveType",
    "SuiteType",
    "make_ghz_suites",
    "make_bell_suites",
    "make_ising_suites",
    "make_qaoa_ring_suites",
    "make_phase_sensing_suites",
    "make_chemistry_suites",
    "make_stress_suite",
    "make_posthoc_library",
    "make_commuting_suite",
    "generate_all_k_local",
    "sample_random_paulis",
    # Protocols
    "Protocol",
    "Estimates",
    "DirectNaiveProtocol",
    "DirectGroupedProtocol",
    "DirectOptimizedProtocol",
    "get_protocol",
    "list_protocols",
    # Statistics
    "normal_ci",
    "construct_ci",
    "construct_simultaneous_cis",
    "FWERMethod",
    # Tasks
    "TaskConfig",
    "TaskType",
    "SweepConfig",
    "SweepOrchestrator",
    # I/O
    "LongFormRow",
    "SummaryRow",
    "ParquetWriter",
    "ParquetReader",
    # Noise
    "NoiseProfile",
    "get_profile",
    "list_profiles",
    # Visualization
    "plot_attainment_curves",
    "plot_ssf_comparison",
    "ReportBuilder",
    # Analysis (Enhanced Benchmarking)
    "run_comprehensive_analysis",
    "ComprehensiveBenchmarkAnalysis",
    "interpolate_n_star",
    "fit_power_law",
    "per_observable_crossover",
    "analyze_by_locality",
    "bootstrap_ci",
    "bootstrap_hypothesis_test",
    "ks_test_protocols",
    "compare_protocols_statistically",
    "compute_cost_normalized_metrics",
    "CostModel",
    "multi_pilot_analysis",
    # Objective metrics
    "ObjectiveEstimate",
    "ObjectiveAnalysis",
    "compute_objective_metrics",
    "format_objective_analysis",
    # Post-hoc benchmarking
    "PosthocBenchmarkResult",
    "run_posthoc_benchmark_from_suite",
    "format_posthoc_result",
    # Unified Benchmark Suite
    "run_benchmark_suite",
    "BenchmarkMode",
    "BenchmarkSuiteConfig",
    "BenchmarkSuiteResult",
]
