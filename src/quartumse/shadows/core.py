"""
Core classical shadows interface.

Classical shadows enable "measure once, ask later" observable estimation:
sample a small number of randomized measurements, then estimate many observables offline.
"""

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
from qiskit import QuantumCircuit


class Observable:
    """Representation of a quantum observable (Pauli string or general)."""

    def __init__(self, pauli_string: str, coefficient: float = 1.0):
        """
        Initialize observable.

        Args:
            pauli_string: Pauli string like "IXYZ" (I=identity, X/Y/Z=Paulis)
            coefficient: Coefficient for the term
        """
        self.pauli_string = pauli_string
        self.coefficient = coefficient
        self.num_qubits = len(pauli_string)
        # Cache support indices for vectorized operations
        self._cached_support: list[int] | None = None

    @property
    def support(self) -> list[int]:
        """Return list of qubit indices where operator is non-identity (cached)."""
        if self._cached_support is None:
            self._cached_support = [i for i, c in enumerate(self.pauli_string) if c != "I"]
        return self._cached_support

    def __repr__(self) -> str:
        return f"{self.coefficient}*{self.pauli_string}"


class ShadowEstimate:
    """Result of shadow-based estimation."""

    def __init__(
        self,
        expectation_value: float,
        variance: float,
        confidence_interval: tuple[float, float],
        shadow_size: int,
        metadata: dict[str, Any] | None = None,
    ):
        self.expectation_value = expectation_value
        self.variance = variance
        self.confidence_interval = confidence_interval
        self.shadow_size = shadow_size
        self.metadata = metadata or {}

    @property
    def ci_lower(self) -> float:
        return self.confidence_interval[0]

    @property
    def ci_upper(self) -> float:
        return self.confidence_interval[1]

    @property
    def ci_width(self) -> float:
        return self.ci_upper - self.ci_lower

    def __repr__(self) -> str:
        return (
            f"ShadowEstimate(value={self.expectation_value:.4f}, "
            f"CI=[{self.ci_lower:.4f}, {self.ci_upper:.4f}], "
            f"shadow_size={self.shadow_size})"
        )


class ClassicalShadows(ABC):
    """
    Abstract base class for classical shadows implementations.

    Different versions (v0-v4) subclass this to provide specific algorithms.
    """

    def __init__(self, config: Any):
        self.config = config
        self.shadow_data: np.ndarray | None = None
        self.measurement_bases: np.ndarray | None = None
        self.measurement_outcomes: np.ndarray | None = None

    @abstractmethod
    def generate_measurement_circuits(
        self, base_circuit: QuantumCircuit, num_shadows: int
    ) -> list[QuantumCircuit]:
        """
        Generate randomized measurement circuits for shadows protocol.

        Args:
            base_circuit: The state preparation circuit
            num_shadows: Number of random measurements

        Returns:
            List of circuits with randomized measurements appended
        """
        pass

    @abstractmethod
    def reconstruct_classical_shadow(
        self, measurement_outcomes: np.ndarray, measurement_bases: np.ndarray
    ) -> np.ndarray:
        """
        Reconstruct classical shadow snapshots from measurement data.

        Args:
            measurement_outcomes: Binary outcomes (0/1) for each measurement
            measurement_bases: Which basis was measured for each qubit

        Returns:
            Array of shadow snapshots (density matrix representations)
        """
        pass

    @abstractmethod
    def estimate_observable(
        self, observable: Observable, shadow_data: np.ndarray | None = None
    ) -> ShadowEstimate:
        """
        Estimate expectation value of an observable using shadow data.

        Args:
            observable: The observable to estimate
            shadow_data: Pre-computed shadow snapshots (or use self.shadow_data)

        Returns:
            Estimate with confidence interval
        """
        pass

    @abstractmethod
    def estimate_shadow_size_needed(self, observable: Observable, target_precision: float) -> int:
        """Estimate the number of shadows required for a desired precision."""

        raise NotImplementedError

    def estimate_multiple_observables(
        self, observables: list[Observable]
    ) -> dict[str, ShadowEstimate]:
        """
        Estimate multiple observables from the same shadow data.

        This is the key advantage: one shadow dataset, many observables.
        """
        if self.shadow_data is None:
            raise ValueError("No shadow data available. Run generate_measurement_circuits first.")

        results = {}
        for obs in observables:
            estimate = self.estimate_observable(obs)
            results[str(obs)] = estimate

        return results

    def compute_variance_bound(self, observable: Observable, shadow_size: int) -> float:
        """
        Theoretical variance bound for the shadow estimator.

        Useful for shot allocation and adaptive strategies.
        """
        # Default implementation (subclasses can override)
        # For random local Clifford: Var ≤ 4^k / M, where k = support size
        support_size = sum(1 for p in observable.pauli_string if p != "I")
        return float(4**support_size) / float(shadow_size)

    def compute_confidence_interval(
        self, mean: float, variance: float, n_samples: int, confidence: float = 0.95
    ) -> tuple[float, float]:
        """Compute confidence interval using normal approximation."""
        from scipy import stats

        std_error = np.sqrt(variance / n_samples)
        z_score = float(stats.norm.ppf((1 + confidence) / 2))

        ci_lower = mean - z_score * std_error
        ci_upper = mean + z_score * std_error

        return (ci_lower, ci_upper)
