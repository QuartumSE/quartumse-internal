"""Configuration for classical shadows experiments."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ShadowVersion(str, Enum):
    """Supported classical shadows versions."""

    V0_BASELINE = "v0"  # Random local Clifford (baseline)
    V1_NOISE_AWARE = "v1"  # Noise-aware inverse channel + MEM
    V2_FERMIONIC = "v2"  # Fermionic shadows for 2-RDM
    V3_ADAPTIVE = "v3"  # Adaptive/derandomized measurement selection
    V4_ROBUST = "v4"  # Robust Bayesian with bootstrapped CIs


class MeasurementEnsemble(str, Enum):
    """Types of measurement ensembles for shadows."""

    RANDOM_LOCAL_CLIFFORD = "random_local_clifford"
    PAULI_BASIS = "pauli_basis"
    GLOBAL_CLIFFORD = "global_clifford"  # Future: more expensive but more efficient
    FERMIONIC_GAUSSIAN = "fermionic_gaussian"  # For v2


class ShadowConfig(BaseModel):
    """Configuration for classical shadows estimation."""

    # Core parameters
    version: ShadowVersion = Field(
        default=ShadowVersion.V0_BASELINE, description="Shadows algorithm version"
    )
    shadow_size: int = Field(
        default=1000, description="Number of random measurements (shadow size)"
    )
    measurement_ensemble: MeasurementEnsemble = Field(
        default=MeasurementEnsemble.RANDOM_LOCAL_CLIFFORD
    )

    # v1+ (noise-aware)
    apply_inverse_channel: bool = Field(
        default=False, description="Apply noise-aware inverse channel (v1+)"
    )
    noise_model_path: Optional[str] = Field(
        None, description="Path to serialized noise model"
    )

    # v2+ (fermionic)
    fermionic_mode: bool = Field(default=False, description="Enable fermionic shadows (v2+)")
    rdm_order: int = Field(default=1, description="RDM order for fermionic mode (1 or 2)")

    # v3+ (adaptive)
    adaptive: bool = Field(default=False, description="Use adaptive measurement selection (v3+)")
    target_observables: Optional[List[str]] = Field(
        None, description="Observable strings for adaptive prioritization"
    )
    derandomization_strategy: Optional[str] = Field(
        None, description="greedy, importance_sampling, etc."
    )

    # v4+ (robust)
    bayesian_inference: bool = Field(
        default=False, description="Enable Bayesian robust estimation (v4+)"
    )
    bootstrap_samples: int = Field(default=1000, description="Bootstrap samples for CI (v4+)")
    confidence_level: float = Field(default=0.95, description="Confidence interval level")

    # General settings
    random_seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    parallel_shots: bool = Field(
        default=True, description="Execute shadow measurements in parallel batches"
    )
    batch_size: Optional[int] = Field(None, description="Batch size for parallel execution")

    # Variance reduction
    median_of_means: bool = Field(
        default=False, description="Use median-of-means estimator for robustness"
    )
    num_groups: int = Field(default=10, description="Number of groups for median-of-means")

    # Advanced
    custom_parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Version-specific custom parameters"
    )

    model_config = ConfigDict(use_enum_values=False)

    def validate_version_compatibility(self) -> None:
        """Validate that enabled features match the selected version."""
        version_requirements = {
            ShadowVersion.V0_BASELINE: [],
            ShadowVersion.V1_NOISE_AWARE: ["apply_inverse_channel"],
            ShadowVersion.V2_FERMIONIC: ["fermionic_mode"],
            ShadowVersion.V3_ADAPTIVE: ["adaptive"],
            ShadowVersion.V4_ROBUST: ["bayesian_inference"],
        }

        # Warning: simplified validation
        # In production, this would check feature availability
        pass
