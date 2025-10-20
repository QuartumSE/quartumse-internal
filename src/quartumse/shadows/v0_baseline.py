"""
Classical Shadows v0: Baseline Random Local Clifford Implementation

Reference: Huang, Kueng, Preskill (2020) - "Predicting Many Properties of a Quantum System"
arXiv:2002.08953

This implements the standard classical shadows protocol:
1. Apply random single-qubit Clifford gates before measurement
2. Measure in computational basis
3. Reconstruct state snapshots via inverse channel
4. Estimate observables by averaging Pauli expectations
"""

from typing import List, Optional

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import HGate, SGate, SdgGate

from quartumse.shadows.config import ShadowConfig
from quartumse.shadows.core import ClassicalShadows, Observable, ShadowEstimate


class RandomLocalCliffordShadows(ClassicalShadows):
    """
    Baseline classical shadows using random local Clifford measurements.

    Each shadow measurement:
    - Apply random single-qubit Clifford (rotates to X, Y, or Z basis)
    - Measure in computational basis
    - Invert to get density matrix snapshot

    Supports Pauli observable estimation with variance guarantees.
    """

    def __init__(self, config: ShadowConfig):
        super().__init__(config)
        self.rng = np.random.default_rng(config.random_seed)

        # Single-qubit Clifford group representatives for basis rotation
        # 0: Z basis (I), 1: X basis (H), 2: Y basis (HS†)
        self.basis_gates = {
            0: lambda qc, q: None,  # Identity (measure Z)
            1: lambda qc, q: qc.h(q),  # Hadamard (measure X)
            2: lambda qc, q: [qc.sdg(q), qc.h(q)],  # HS† (measure Y)
        }

        # Inverse channel matrices for reconstruction
        # |b⟩⟨b| -> 3|b⟩⟨b| - I (for single qubit)
        self._build_inverse_channel()

    def _build_inverse_channel(self) -> None:
        """Precompute inverse channel for single-qubit reconstruction."""
        # For computational basis outcome b, snapshot is: ρ̂ = 3|b⟩⟨b| - I
        self.inverse_channel = {
            0: 3 * np.array([[1, 0], [0, 0]], dtype=complex) - np.eye(2),  # |0⟩
            1: 3 * np.array([[0, 0], [0, 1]], dtype=complex) - np.eye(2),  # |1⟩
        }

    def generate_measurement_circuits(
        self, base_circuit: QuantumCircuit, num_shadows: int
    ) -> List[QuantumCircuit]:
        """
        Generate shadow measurement circuits with random local Clifford rotations.

        Each circuit:
        - Copies the base state preparation
        - Applies random single-qubit Clifford to each qubit
        - Measures all qubits
        """
        num_qubits = base_circuit.num_qubits
        circuits = []
        measurement_bases = []

        for _ in range(num_shadows):
            # Create a copy of the base circuit
            shadow_circuit = base_circuit.copy()

            # Sample random basis for each qubit (0=Z, 1=X, 2=Y)
            bases = self.rng.integers(0, 3, size=num_qubits)
            measurement_bases.append(bases)

            # Apply basis rotation gates
            for qubit_idx in range(num_qubits):
                basis = bases[qubit_idx]
                gate_fn = self.basis_gates[basis]
                gate_fn(shadow_circuit, qubit_idx)

            # Measure all qubits
            shadow_circuit.measure_all()

            circuits.append(shadow_circuit)

        # Store bases for reconstruction
        self.measurement_bases = np.array(measurement_bases)

        return circuits

    def reconstruct_classical_shadow(
        self, measurement_outcomes: np.ndarray, measurement_bases: np.ndarray
    ) -> np.ndarray:
        """
        Reconstruct shadow snapshots from measurement outcomes.

        Args:
            measurement_outcomes: Shape (num_shadows, num_qubits) - binary outcomes
            measurement_bases: Shape (num_shadows, num_qubits) - basis indices

        Returns:
            Array of shadow snapshots (we store reduced representations)
        """
        num_shadows, num_qubits = measurement_outcomes.shape

        # For efficiency, we don't store full density matrices
        # Instead, store (basis, outcome) pairs and reconstruct on-demand
        self.measurement_outcomes = measurement_outcomes
        self.measurement_bases = measurement_bases

        # Placeholder: full implementation would compute Pauli expectations
        # For now, we store data and compute during estimation
        return np.stack([measurement_outcomes, measurement_bases], axis=-1)

    def _pauli_expectation_single_shadow(
        self, shadow_idx: int, observable: Observable
    ) -> float:
        """
        Compute Pauli expectation for a single shadow snapshot.

        For random Pauli measurements, the estimator is:
        - If measured in compatible basis: use outcome
        - Otherwise: 0 (or unbiased random)
        """
        pauli_string = observable.pauli_string
        num_qubits = len(pauli_string)

        expectation = 1.0

        for qubit_idx in range(num_qubits):
            pauli = pauli_string[qubit_idx]
            if pauli == "I":
                continue  # Identity doesn't affect expectation

            # Map Pauli to basis index
            pauli_to_basis = {"X": 1, "Y": 2, "Z": 0}
            required_basis = pauli_to_basis.get(pauli)

            measured_basis = self.measurement_bases[shadow_idx, qubit_idx]
            outcome = self.measurement_outcomes[shadow_idx, qubit_idx]

            if measured_basis == required_basis:
                # Compatible measurement: use outcome (0 -> +1, 1 -> -1)
                sign = 1 - 2 * outcome
                expectation *= sign
            else:
                # Incompatible measurement: estimator is 0
                return 0.0

        return expectation * observable.coefficient

    def estimate_observable(
        self, observable: Observable, shadow_data: Optional[np.ndarray] = None
    ) -> ShadowEstimate:
        """
        Estimate observable expectation value from shadow snapshots.

        Uses median-of-means if configured for robustness.
        """
        if self.measurement_outcomes is None or self.measurement_bases is None:
            raise ValueError("No measurement data. Generate circuits and run first.")

        num_shadows = len(self.measurement_outcomes)

        # Compute expectation for each shadow
        expectations = np.array(
            [self._pauli_expectation_single_shadow(i, observable) for i in range(num_shadows)]
        )

        # Compute statistics
        if self.config.median_of_means and num_shadows >= self.config.num_groups:
            # Median-of-means for robustness
            group_size = num_shadows // self.config.num_groups
            group_means = [
                np.mean(expectations[i * group_size : (i + 1) * group_size])
                for i in range(self.config.num_groups)
            ]
            mean_estimate = np.median(group_means)
            variance = np.var(expectations)
        else:
            # Standard mean estimator
            mean_estimate = np.mean(expectations)
            variance = np.var(expectations)

        # Confidence interval
        ci = self.compute_confidence_interval(
            mean_estimate, variance, num_shadows, self.config.confidence_level
        )

        return ShadowEstimate(
            expectation_value=mean_estimate,
            variance=variance,
            confidence_interval=ci,
            shadow_size=num_shadows,
            metadata={
                "observable": str(observable),
                "method": "random_local_clifford",
                "median_of_means": self.config.median_of_means,
            },
        )

    def compute_variance_bound(self, observable: Observable, shadow_size: int) -> float:
        """
        Variance bound for random local Clifford shadows.

        For a Pauli observable with support k (number of non-identity Paulis):
        Var[estimator] ≤ 4^k / M

        where M is the shadow size.
        """
        support_size = sum(1 for p in observable.pauli_string if p != "I")
        return 4**support_size / shadow_size

    def estimate_shadow_size_needed(
        self, observable: Observable, target_precision: float, confidence: float = 0.95
    ) -> int:
        """
        Estimate shadow size needed to achieve target precision.

        Uses Chebyshev inequality and variance bound.
        """
        support_size = sum(1 for p in observable.pauli_string if p != "I")

        # From concentration: Pr[|est - true| > ε] ≤ Var / ε²
        # For confidence δ, set Var / ε² ≤ δ
        delta = 1 - confidence
        variance_bound_coeff = 4**support_size

        # M ≥ variance_bound_coeff / (ε² * δ)
        shadow_size = int(np.ceil(variance_bound_coeff / (target_precision**2 * delta)))

        return shadow_size
