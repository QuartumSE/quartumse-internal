"""
QuartumSE - Quantum Measurement Optimization & Observability Platform

A vendor-neutral framework for running quantum experiments with:
- Classical shadows for shot-efficient observable estimation
- Rigorous error mitigation and confidence intervals
- Full provenance tracking and reproducibility
- Cross-platform backend support (IBM, AWS, and more)

License: Apache 2.0
"""

__version__ = "0.1.0"
__author__ = "QuartumSE Team"

# Core API exports
from quartumse.estimator import Estimator, ShadowEstimator
from quartumse.shadows import ClassicalShadows, ShadowConfig
from quartumse.reporting import ProvenanceManifest, Report

__all__ = [
    # Version
    "__version__",
    "__author__",
    # Core classes
    "Estimator",
    "ShadowEstimator",
    "ClassicalShadows",
    "ShadowConfig",
    "ProvenanceManifest",
    "Report",
]
