"""Statistical utilities for quantum measurement analysis (Measurements Bible §6).

This package provides:
- Confidence interval construction (§6.1, §6.2)
- Family-wise error rate control (§6.3)
- Coverage verification utilities (§6.4)

Usage:
    from quartumse.stats import (
        # Confidence intervals
        normal_ci,
        bootstrap_percentile_ci,
        bootstrap_bca_ci,
        construct_ci,
        ci_from_eigenvalues,
        ConfidenceInterval,
        CIMethodType,
        # FWER control
        bonferroni_adjustment,
        sidak_adjustment,
        holm_adjustment,
        compute_fwer_adjustment,
        construct_simultaneous_cis,
        FWERMethod,
        FWERAdjustment,
        SimultaneousCIs,
        # Coverage verification
        compute_coverage,
        compute_simultaneous_coverage,
        simulate_coverage,
        validate_coverage,
        CoverageResult,
    )

    # Construct normal CI
    ci = normal_ci(estimate=0.5, se=0.02, confidence_level=0.95)

    # Construct simultaneous CIs with FWER control
    estimates = [0.5, 0.3, 0.1]
    ses = [0.02, 0.03, 0.01]
    sim_cis = construct_simultaneous_cis(
        estimates, ses, alpha=0.05, fwer_method="bonferroni"
    )

    # Verify coverage
    truths = [0.52, 0.28, 0.11]
    print(f"Family-wise coverage: {sim_cis.all_contain(truths)}")
"""

from .confidence import (
    CIMethodType,
    ConfidenceInterval,
    bootstrap_bca_ci,
    bootstrap_percentile_ci,
    ci_from_eigenvalues,
    clamp_to_physical_bounds,
    construct_ci,
    normal_ci,
)
from .coverage import (
    CoverageResult,
    CoverageSimulationResult,
    compute_coverage,
    compute_simultaneous_coverage,
    simulate_coverage,
    validate_coverage,
)
from .fwer import (
    FWERAdjustment,
    FWERMethod,
    SimultaneousCIs,
    bonferroni_adjustment,
    compute_fwer_adjustment,
    compute_required_confidence_for_fwer,
    construct_simultaneous_cis,
    holm_adjustment,
    sidak_adjustment,
)

__all__ = [
    # Confidence intervals
    "CIMethodType",
    "ConfidenceInterval",
    "normal_ci",
    "bootstrap_percentile_ci",
    "bootstrap_bca_ci",
    "construct_ci",
    "ci_from_eigenvalues",
    "clamp_to_physical_bounds",
    # FWER control
    "FWERMethod",
    "FWERAdjustment",
    "SimultaneousCIs",
    "bonferroni_adjustment",
    "sidak_adjustment",
    "holm_adjustment",
    "compute_fwer_adjustment",
    "construct_simultaneous_cis",
    "compute_required_confidence_for_fwer",
    # Coverage
    "CoverageResult",
    "CoverageSimulationResult",
    "compute_coverage",
    "compute_simultaneous_coverage",
    "simulate_coverage",
    "validate_coverage",
]
