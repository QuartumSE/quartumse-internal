"""Ground truth computation via statevector simulation (Measurements Bible §3.4).

This module provides exact expectation value computation for Pauli observables
using statevector simulation. Ground truth is essential for:
- Bias-variance decomposition (Task 6)
- Coverage calibration
- Validating estimator correctness

Memory requirements:
- Statevector: ~16 * 2^n bytes (complex128)
- Density matrix: ~16 * 4^n bytes (complex128)

For n > ~25 qubits, use reference truth with high-precision sampling instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Pauli, SparsePauliOp, Statevector

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

    def __init__(
        self,
        memory_limit_bytes: int | None = None,
        max_qubits: int = 25,
    ) -> None:
        """Initialize statevector backend.

        Args:
            memory_limit_bytes: Maximum memory for simulation (default: no limit).
            max_qubits: Maximum qubits supported (default: 25 for ~500MB).
        """
        self.memory_limit_bytes = memory_limit_bytes
        self.max_qubits = max_qubits

    def _check_feasibility(self, n_qubits: int) -> None:
        """Check if statevector simulation is feasible."""
        if n_qubits > self.max_qubits:
            raise ValueError(
                f"Statevector simulation not feasible for {n_qubits} qubits "
                f"(max: {self.max_qubits}). Use reference truth instead."
            )

        # Memory estimate: 16 bytes per complex128 amplitude
        memory_required = 16 * (2**n_qubits)
        if self.memory_limit_bytes and memory_required > self.memory_limit_bytes:
            raise ValueError(
                f"Statevector requires ~{memory_required / 1e9:.2f} GB, "
                f"exceeds limit of {self.memory_limit_bytes / 1e9:.2f} GB"
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
        for obs in observable_set.observables:
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
    max_qubits: int = 25,
) -> GroundTruthResult:
    """Convenience function to compute ground truth.

    Args:
        circuit: State preparation circuit.
        observable_set: Set of observables.
        circuit_id: Identifier for the circuit.
        max_qubits: Maximum qubits for statevector simulation.

    Returns:
        GroundTruthResult with exact expectations.
    """
    backend = StatevectorBackend(max_qubits=max_qubits)
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
