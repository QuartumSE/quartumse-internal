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
from quartumse.observables import Observable, ObservableSet, generate_observable_set
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
]
