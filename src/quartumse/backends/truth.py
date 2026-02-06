"""Ground truth computation via statevector simulation (Measurements Bible §3.4).

This module provides exact expectation value computation for Pauli observables
using statevector simulation. Ground truth is essential for:
- Bias-variance decomposition (Task 6)
- Coverage calibration
- Validating estimator correctness

Memory requirements:
- Statevector: ~16 * 2^n bytes (complex128)
- Density matrix: ~16 * 4^n bytes (complex128)

By default, statevector ground truth enforces a 512 MB memory limit for
feasibility (configurable via ``GroundTruthConfig`` or ``memory_limit_bytes``).
For larger systems, use reference truth with high-precision sampling instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Pauli, PauliList, SparsePauliOp, Statevector

if TYPE_CHECKING:
    from quartumse.observables import Observable, ObservableSet


@dataclass
class GroundTruthResult:
    """Result from ground truth computation.

    Attributes:
        truth_values: Dict mapping observable_id to exact expectation value.
        truth_mode: Mode used for computation ("exact_statevector", etc.).
        n_qubits: Number of qubits.
        circuit_id: Identifier for the circuit used.
        metadata: Additional metadata (runtime, memory usage).
    """

    truth_values: dict[str, float]
    truth_mode: str = "exact_statevector"
    n_qubits: int = 0
    circuit_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def get(self, observable_id: str) -> float:
        """Get truth value for an observable."""
        if observable_id not in self.truth_values:
            raise KeyError(f"No ground truth for observable {observable_id}")
        return self.truth_values[observable_id]


class StatevectorBackend:
    """Backend for exact ground truth computation via statevector simulation.

    This backend computes exact expectation values <O> = Tr(O|psi><psi|)
    using Qiskit's Statevector class.

    Example:
        backend = StatevectorBackend()
        truth = backend.compute_ground_truth(circuit, observable_set)
        print(truth.truth_values)  # {obs_id: <O>, ...}
    """

    DEFAULT_MEMORY_LIMIT_BYTES = 512 * 1024**2

    def __init__(
        self,
        memory_limit_bytes: int | None = DEFAULT_MEMORY_LIMIT_BYTES,
        max_qubits: int | None = None,
    ) -> None:
        """Initialize statevector backend.

        Args:
            memory_limit_bytes: Maximum memory for simulation
                (default: 512 MB; set to None for no limit).
            max_qubits: Optional maximum qubits supported as a secondary cap.
        """
        self.memory_limit_bytes = memory_limit_bytes
        self.max_qubits = max_qubits

    def _check_feasibility(self, n_qubits: int) -> None:
        """Check if statevector simulation is feasible."""
        # Memory estimate: 16 bytes per complex128 amplitude
        memory_required = 16 * (2**n_qubits)
        if self.memory_limit_bytes and memory_required > self.memory_limit_bytes:
            raise ValueError(
                f"Statevector simulation requires ~{memory_required / 1e9:.2f} GB, "
                "which exceeds the configured memory limit of "
                f"{self.memory_limit_bytes / 1e9:.2f} GB. "
                "Increase memory_limit_bytes or use reference truth instead."
            )

        if self.max_qubits is not None and n_qubits > self.max_qubits:
            raise ValueError(
                "Statevector simulation blocked by max_qubits="
                f"{self.max_qubits} (n_qubits={n_qubits}). "
                "Memory_limit_bytes is the primary feasibility rule; adjust "
                "max_qubits or memory_limit_bytes if you want to override this cap."
            )

    def compute_ground_truth(
        self,
        circuit: QuantumCircuit,
        observable_set: ObservableSet,
        circuit_id: str = "circuit",
    ) -> GroundTruthResult:
        """Compute exact ground truth for all observables.

        Args:
            circuit: State preparation circuit.
            observable_set: Set of observables to compute expectations for.
            circuit_id: Identifier for the circuit.

        Returns:
            GroundTruthResult with exact expectation values.
        """
        n_qubits = circuit.num_qubits
        self._check_feasibility(n_qubits)

        # Get statevector
        statevector = Statevector.from_instruction(circuit)

        # Compute expectations
        truth_values = {}
        observables = list(observable_set.observables)
        pauli_strings = [obs.pauli_string for obs in observables]
        coefficients = [obs.coefficient for obs in observables]
        try:
            pauli_list = PauliList(pauli_strings)
            expectations = statevector.expectation_value(pauli_list)
            for obs, expectation, coeff in zip(
                observables, expectations, coefficients, strict=False
            ):
                truth_values[obs.observable_id] = float(np.real(expectation)) * coeff
        except Exception:
            for obs in observables:
                expectation = self._compute_pauli_expectation(statevector, obs)
                truth_values[obs.observable_id] = expectation

        return GroundTruthResult(
            truth_values=truth_values,
            truth_mode="exact_statevector",
            n_qubits=n_qubits,
            circuit_id=circuit_id,
            metadata={
                "n_observables": len(observable_set),
                "backend": "statevector",
            },
        )

    def _compute_pauli_expectation(
        self,
        statevector: Statevector,
        observable: Observable,
    ) -> float:
        """Compute <psi|O|psi> for a Pauli observable.

        Args:
            statevector: The quantum state.
            observable: Pauli observable with string representation.

        Returns:
            Exact expectation value.
        """
        # Create Pauli operator
        pauli_str = observable.pauli_string
        coeff = observable.coefficient

        # Qiskit uses little-endian ordering, reverse if needed
        # Our convention: pauli_string[0] is qubit 0
        pauli = Pauli(pauli_str)
        op = SparsePauliOp(pauli, coeffs=[coeff])

        # Compute expectation value
        expectation = statevector.expectation_value(op)

        # Should be real for Hermitian observables
        return float(np.real(expectation))

    def compute_single_expectation(
        self,
        circuit: QuantumCircuit,
        pauli_string: str,
        coefficient: float = 1.0,
    ) -> float:
        """Compute expectation for a single Pauli string.

        Convenience method for quick ground truth checks.

        Args:
            circuit: State preparation circuit.
            pauli_string: Pauli string (e.g., "XZIY").
            coefficient: Observable coefficient.

        Returns:
            Exact expectation value.
        """
        self._check_feasibility(circuit.num_qubits)

        statevector = Statevector.from_instruction(circuit)
        pauli = Pauli(pauli_string)
        op = SparsePauliOp(pauli, coeffs=[coefficient])

        return float(np.real(statevector.expectation_value(op)))


def compute_ground_truth(
    circuit: QuantumCircuit,
    observable_set: ObservableSet,
    circuit_id: str = "circuit",
    max_qubits: int | None = None,
    config: GroundTruthConfig | None = None,
) -> GroundTruthResult:
    """Convenience function to compute ground truth.

    Args:
        circuit: State preparation circuit.
        observable_set: Set of observables.
        circuit_id: Identifier for the circuit.
        max_qubits: Optional secondary qubit cap for statevector simulation.
        config: Optional ground truth configuration. When provided, its
            memory_limit_bytes is the primary feasibility gate.

    Returns:
        GroundTruthResult with exact expectations.
    """
    resolved_config = config or GroundTruthConfig(max_qubits=max_qubits)
    backend = StatevectorBackend(
        memory_limit_bytes=resolved_config.memory_limit_bytes,
        max_qubits=resolved_config.max_qubits,
    )
    return backend.compute_ground_truth(circuit, observable_set, circuit_id)


def compute_observable_expectation(
    circuit: QuantumCircuit,
    pauli_string: str,
    coefficient: float = 1.0,
) -> float:
    """Compute exact expectation for a single observable.

    Args:
        circuit: State preparation circuit.
        pauli_string: Pauli string representation.
        coefficient: Observable coefficient.

    Returns:
        Exact expectation value.
    """
    backend = StatevectorBackend()
    return backend.compute_single_expectation(circuit, pauli_string, coefficient)


@dataclass(frozen=True)
class GroundTruthConfig:
    """Configuration for statevector ground truth computation.

    Attributes:
        memory_limit_bytes: Maximum memory for simulation. Defaults to 512 MB
            (matching the historical ~25-qubit limit for complex128 statevectors).
            Set to None to disable the memory limit.
        max_qubits: Optional secondary qubit cap. Memory_limit_bytes is the primary
            feasibility rule.
    """

    memory_limit_bytes: int | None = StatevectorBackend.DEFAULT_MEMORY_LIMIT_BYTES
    max_qubits: int | None = None


# Reference truth for large systems (when statevector is infeasible)
@dataclass
class ReferenceTruthConfig:
    """Configuration for reference truth computation.

    When exact statevector simulation is infeasible, use high-shot
    sampling to establish reference truth with known uncertainty.

    Attributes:
        n_shots: Number of shots for reference (should be >> protocol shots).
        se_target_ratio: Target SE ratio (reference SE should be << protocol SE).
        ci_method: CI method for reference uncertainty.
    """

    n_shots: int = 1_000_000
    se_target_ratio: float = 0.1  # Reference SE should be ≤ ε/10
    ci_method: str = "normal"


def estimate_required_shots_for_reference(
    target_precision: float,
    se_ratio: float = 0.1,
    max_variance: float = 1.0,
) -> int:
    """Estimate shots needed for reference truth.

    For reference truth to be reliable, its SE should be much smaller
    than the target precision: SE_ref ≤ se_ratio * epsilon.

    Args:
        target_precision: Target precision epsilon.
        se_ratio: Desired ratio SE_ref / epsilon.
        max_variance: Maximum expected observable variance (≤1 for Paulis).

    Returns:
        Recommended number of shots for reference truth.
    """
    # SE = sqrt(var / n) ≤ se_ratio * epsilon
    # n ≥ var / (se_ratio * epsilon)^2
    required_shots = max_variance / (se_ratio * target_precision) ** 2
    return int(np.ceil(required_shots))
