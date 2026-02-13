"""Protocol state and data structures for the Measurements Bible §5 interface.

This module defines the core data structures used by all measurement protocols:
- ProtocolState: Mutable state maintained across protocol rounds
- MeasurementPlan: Specification of measurement settings and shot allocation
- MeasurementSetting: Single measurement basis/unitary configuration
- RawDatasetChunk: Raw measurement outcomes from one acquisition round
- ObservableEstimate: Per-observable estimation result
- Estimates: Complete estimation results for all observables
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np
from numpy.typing import NDArray


class CIMethod(Enum):
    """Confidence interval construction method (§6.1)."""

    NORMAL = "normal"
    BOOTSTRAP = "bootstrap"
    CONSERVATIVE_BOUNDED = "conservative_bounded"
    NONE = "none"


@dataclass
class MeasurementSetting:
    """A single measurement setting specification (§3.3).

    Supports both string-based and array-based basis representations.

    Attributes:
        setting_id: Unique identifier for this setting.
        measurement_basis: String representation of measurement basis (e.g., "ZXZY").
        basis_choices: Per-qubit basis choices as array. For Pauli measurements:
            0 = Z (computational), 1 = X, 2 = Y.
            If not provided, computed from measurement_basis.
        target_qubits: List of qubit indices this setting applies to.
        pre_rotations: Optional pre-rotation specification (e.g., for global Clifford).
        metadata: Additional setting-specific metadata.
    """

    setting_id: str
    measurement_basis: str = ""
    basis_choices: NDArray[np.int_] | None = None
    target_qubits: list[int] | None = None
    pre_rotations: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Compute basis_choices from measurement_basis if not provided."""
        if self.basis_choices is None and self.measurement_basis:
            basis_map = {"Z": 0, "X": 1, "Y": 2, "I": 0}
            self.basis_choices = np.array(
                [basis_map.get(b, 0) for b in self.measurement_basis], dtype=np.int_
            )
        if self.target_qubits is None and self.measurement_basis:
            self.target_qubits = list(range(len(self.measurement_basis)))


@dataclass
class MeasurementPlan:
    """Measurement plan specifying settings and shot allocation (§5.2).

    Attributes:
        settings: List of measurement settings to execute.
        shots_per_setting: Number of shots to allocate to each setting.
        observable_setting_map: Mapping from observable_id to list of setting indices
            that can estimate that observable.
        total_shots: Total shots in this plan.
        metadata: Additional plan metadata (e.g., optimization objective).
    """

    settings: list[MeasurementSetting]
    shots_per_setting: list[int]
    observable_setting_map: dict[str, list[int]]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_shots(self) -> int:
        """Total shots across all settings."""
        return sum(self.shots_per_setting)

    @property
    def n_settings(self) -> int:
        """Number of distinct measurement settings."""
        return len(self.settings)


@dataclass
class RawDatasetChunk:
    """Raw measurement outcomes from one acquisition round (§5.2).

    Supports two data formats:
    1. Dict-based: bitstrings mapping setting_id -> list[str]
    2. Array-based: setting_indices, outcomes, basis_choices as NDArrays

    Attributes:
        bitstrings: Dict mapping setting_id to list of bitstring outcomes.
        settings_executed: List of setting IDs that were executed.
        setting_indices: Which setting produced each shot. Shape: (n_shots,).
        outcomes: Measurement outcomes as array. Shape: (n_shots, n_qubits).
        basis_choices: Basis choice for each shot. Shape: (n_shots, n_qubits).
        n_qubits: Number of qubits measured.
        metadata: Additional per-chunk metadata (timestamps, backend info).
    """

    # Dict-based format (used by baseline protocols)
    bitstrings: dict[str, list[str]] = field(default_factory=dict)
    settings_executed: list[str] = field(default_factory=list)

    # Array-based format (optional, for advanced use)
    setting_indices: NDArray[np.int_] | None = None
    outcomes: NDArray[np.int_] | None = None
    basis_choices: NDArray[np.int_] | None = None
    n_qubits: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def n_shots(self) -> int:
        """Number of shots in this chunk."""
        if self.bitstrings:
            return sum(len(bs) for bs in self.bitstrings.values())
        elif self.setting_indices is not None:
            return len(self.setting_indices)
        return 0


@dataclass
class ProtocolState:
    """Mutable state maintained by a protocol across rounds (§5.1).

    This state is updated by the protocol's `update()` method after each
    acquisition round. It enables adaptive protocols to make decisions
    based on accumulated data.

    Attributes:
        observable_set: The set of observables being estimated.
        total_budget: Total shot budget allocated for estimation.
        remaining_budget: Remaining shots not yet used.
        seed: Random seed for reproducibility.
        accumulated_data: List of RawDatasetChunk from all rounds.
        total_shots_used: Running total of shots consumed.
        n_rounds: Number of acquisition rounds completed.
        round_number: Alias for n_rounds for backwards compatibility.
        round_metadata: Per-round metadata (classical time, settings used).
        adaptive_state: Protocol-specific adaptive state (e.g., variance estimates).
        converged: Whether the protocol has determined convergence.
        early_stopped: Whether early stopping was triggered.
        metadata: Additional protocol-specific metadata.
    """

    # Required fields (set by initialize)
    observable_set: Any = None  # ObservableSet, but Any to avoid circular import
    total_budget: int = 0
    remaining_budget: int = 0
    seed: int = 42

    # Accumulation state
    accumulated_data: list[RawDatasetChunk] = field(default_factory=list)
    total_shots_used: int = 0
    n_rounds: int = 0
    round_metadata: list[dict[str, Any]] = field(default_factory=list)

    # Adaptive state
    adaptive_state: dict[str, Any] = field(default_factory=dict)
    converged: bool = False
    early_stopped: bool = False

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def round_number(self) -> int:
        """Alias for n_rounds for backwards compatibility."""
        return self.n_rounds

    @round_number.setter
    def round_number(self, value: int) -> None:
        """Set n_rounds via round_number alias."""
        self.n_rounds = value

    def add_chunk(self, chunk: RawDatasetChunk, round_meta: dict[str, Any] | None = None) -> None:
        """Add a data chunk and update counters."""
        self.accumulated_data.append(chunk)
        self.total_shots_used += chunk.n_shots
        self.n_rounds += 1
        self.round_metadata.append(round_meta or {})

    def get_all_outcomes(self) -> NDArray[np.int_]:
        """Concatenate outcomes from all chunks."""
        if not self.accumulated_data:
            raise ValueError("No data accumulated yet")
        return np.vstack([chunk.outcomes for chunk in self.accumulated_data])

    def get_all_bases(self) -> NDArray[np.int_]:
        """Concatenate basis choices from all chunks."""
        if not self.accumulated_data:
            raise ValueError("No data accumulated yet")
        return np.vstack([chunk.basis_choices for chunk in self.accumulated_data])


@dataclass
class CIResult:
    """Confidence interval result with both raw and clamped bounds (§6.1).

    Attributes:
        ci_low_raw: Lower bound before clamping.
        ci_high_raw: Upper bound before clamping.
        ci_low: Lower bound after clamping (if applicable).
        ci_high: Upper bound after clamping (if applicable).
        confidence_level: Nominal confidence level (e.g., 0.95).
        method: CI construction method used.
        clamped: Whether bounds were clamped.
        clamp_range: The range used for clamping, if any.
    """

    ci_low_raw: float
    ci_high_raw: float
    ci_low: float
    ci_high: float
    confidence_level: float
    method: CIMethod
    clamped: bool = False
    clamp_range: tuple[float, float] | None = None

    @property
    def half_width(self) -> float:
        """CI half-width (clamped bounds)."""
        return (self.ci_high - self.ci_low) / 2

    @property
    def half_width_raw(self) -> float:
        """CI half-width (raw bounds)."""
        return (self.ci_high_raw - self.ci_low_raw) / 2

    @classmethod
    def from_se(
        cls,
        estimate: float,
        se: float,
        confidence_level: float = 0.95,
        method: CIMethod = CIMethod.NORMAL,
        clamp_range: tuple[float, float] | None = None,
    ) -> CIResult:
        """Create CI from standard error using normal approximation."""
        from scipy import stats

        z = stats.norm.ppf((1 + confidence_level) / 2)
        ci_low_raw = estimate - z * se
        ci_high_raw = estimate + z * se

        ci_low = ci_low_raw
        ci_high = ci_high_raw
        clamped = False

        if clamp_range is not None:
            ci_low = max(ci_low_raw, clamp_range[0])
            ci_high = min(ci_high_raw, clamp_range[1])
            clamped = ci_low != ci_low_raw or ci_high != ci_high_raw

        return cls(
            ci_low_raw=ci_low_raw,
            ci_high_raw=ci_high_raw,
            ci_low=ci_low,
            ci_high=ci_high,
            confidence_level=confidence_level,
            method=method,
            clamped=clamped,
            clamp_range=clamp_range,
        )


@dataclass
class ObservableEstimate:
    """Estimation result for a single observable (§5.3).

    Attributes:
        observable_id: Unique identifier for the observable.
        estimate: Point estimate of the expectation value.
        se: Standard error of the estimate.
        n_shots: Number of shots used for this observable.
        n_settings: Number of measurement settings used.
        ci: Confidence interval result (if computed).
        variance: Variance of the estimator.
        effective_sample_size: Effective sample size proxy.
        bias_estimate: Estimated bias (if available from truth).
        diagnostics: Additional diagnostics (tail flags, batch stats).
    """

    observable_id: str
    estimate: float
    se: float
    n_shots: int = 0
    n_settings: int = 0
    ci: CIResult | None = None
    variance: float | None = None
    effective_sample_size: float | None = None
    bias_estimate: float | None = None
    diagnostics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Estimates:
    """Complete estimation results for all observables (§5.3).

    Supports both list-based and dict-based storage of estimates.

    Attributes:
        estimates: List of ObservableEstimate objects.
        observable_estimates: Dict mapping observable_id to ObservableEstimate (computed).
        total_shots: Total shots used for estimation.
        n_settings: Number of distinct measurement settings used.
        time_quantum_s: Quantum execution time in seconds.
        time_classical_s: Classical processing time in seconds.
        protocol_id: ID of the protocol that produced these estimates.
        protocol_version: Version of the protocol.
        ci_method_id: CI method used (if uniform across observables).
        metadata: Additional metadata.
    """

    # Primary storage as list (used by protocols)
    estimates: list[ObservableEstimate] = field(default_factory=list)

    # Optional: total shots and settings
    total_shots: int = 0
    n_settings: int = 0

    # Timing
    time_quantum_s: float | None = None
    time_classical_s: float | None = None

    # Protocol info
    protocol_id: str | None = None
    protocol_version: str | None = None
    ci_method_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # Optional: raw shot-level data for post-hoc analysis (e.g., pilot subsampling)
    raw_chunks: list[RawDatasetChunk] | None = field(default=None, repr=False)

    @property
    def observable_estimates(self) -> dict[str, ObservableEstimate]:
        """Dict view mapping observable_id to ObservableEstimate."""
        return {est.observable_id: est for est in self.estimates}

    @property
    def n_observables(self) -> int:
        """Number of observables estimated."""
        return len(self.estimates)

    def get_estimate(self, observable_id: str) -> ObservableEstimate:
        """Get estimate for a specific observable."""
        for est in self.estimates:
            if est.observable_id == observable_id:
                return est
        raise KeyError(f"Observable {observable_id} not found in estimates")

    def max_se(self) -> float:
        """Maximum standard error across all observables."""
        if not self.estimates:
            return float("inf")
        return max(est.se for est in self.estimates)

    def mean_se(self) -> float:
        """Mean standard error across all observables."""
        ses = [est.se for est in self.observable_estimates.values()]
        return sum(ses) / len(ses)

    def max_ci_half_width(self) -> float | None:
        """Maximum CI half-width across all observables."""
        half_widths = [
            est.ci.half_width for est in self.observable_estimates.values() if est.ci is not None
        ]
        return max(half_widths) if half_widths else None

    def all_within_target(self, epsilon: float, use_ci: bool = True) -> bool:
        """Check if all observables meet precision target.

        Args:
            epsilon: Target precision (SE or CI half-width).
            use_ci: If True, check CI half-width; otherwise check SE.

        Returns:
            True if all observables meet the target.
        """
        for est in self.observable_estimates.values():
            if use_ci and est.ci is not None:
                if est.ci.half_width > epsilon:
                    return False
            elif est.se > epsilon:
                return False
        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "observable_estimates": {
                obs_id: {
                    "observable_id": est.observable_id,
                    "estimate": est.estimate,
                    "se": est.se,
                    "variance": est.variance,
                    "ci": (
                        {
                            "ci_low": est.ci.ci_low,
                            "ci_high": est.ci.ci_high,
                            "ci_low_raw": est.ci.ci_low_raw,
                            "ci_high_raw": est.ci.ci_high_raw,
                            "confidence_level": est.ci.confidence_level,
                            "method": est.ci.method.value,
                            "clamped": est.ci.clamped,
                        }
                        if est.ci
                        else None
                    ),
                    "effective_sample_size": est.effective_sample_size,
                    "diagnostics": est.diagnostics,
                }
                for obs_id, est in self.observable_estimates.items()
            },
            "n_observables": self.n_observables,
            "total_shots": self.total_shots,
            "n_settings": self.n_settings,
            "time_quantum_s": self.time_quantum_s,
            "time_classical_s": self.time_classical_s,
            "protocol_id": self.protocol_id,
            "protocol_version": self.protocol_version,
            "ci_method_id": self.ci_method_id,
            "metadata": self.metadata,
        }
