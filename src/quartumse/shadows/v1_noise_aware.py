"""Classical Shadows v1: Noise-aware variant with MEM corrections."""

from __future__ import annotations

from typing import List, Optional

import numpy as np

from quartumse.mitigation import MeasurementErrorMitigation
from quartumse.shadows.config import ShadowConfig
from quartumse.shadows.core import Observable
from quartumse.shadows.v0_baseline import RandomLocalCliffordShadows


class NoiseAwareRandomLocalCliffordShadows(RandomLocalCliffordShadows):
    """Noise-aware classical shadows using measurement error mitigation."""

    def __init__(self, config: ShadowConfig, mem: MeasurementErrorMitigation):
        super().__init__(config)
        self.mem = mem
        self.noise_corrected_distributions: Optional[np.ndarray] = None

    def reconstruct_classical_shadow(
        self, measurement_outcomes: np.ndarray, measurement_bases: np.ndarray
    ) -> np.ndarray:
        """Reconstruct classical shadows and store MEM-corrected distributions."""

        reconstructed = super().reconstruct_classical_shadow(
            measurement_outcomes, measurement_bases
        )

        num_shadows, num_qubits = measurement_outcomes.shape
        num_states = 2**num_qubits
        corrected = np.zeros((num_shadows, num_states), dtype=float)

        for shadow_idx in range(num_shadows):
            outcome_bits = measurement_outcomes[shadow_idx]
            bitstring = "".join(str(bit) for bit in outcome_bits[::-1])
            corrected_counts = self.mem.apply({bitstring: 1})

            if not corrected_counts:
                continue

            for state_bitstring, value in corrected_counts.items():
                state_index = self._bitstring_to_index(state_bitstring)
                corrected[shadow_idx, state_index] = value

            total = corrected[shadow_idx].sum()
            if total > 0:
                corrected[shadow_idx] /= total

        self.noise_corrected_distributions = corrected
        return reconstructed

    def _pauli_expectation_single_shadow(
        self, shadow_idx: int, observable: Observable
    ) -> float:
        """Compute Pauli expectation using MEM-corrected distributions."""

        if self.measurement_bases is None:
            raise ValueError("No measurement bases recorded; cannot compute expectation.")

        if (
            self.noise_corrected_distributions is None
            or shadow_idx >= len(self.noise_corrected_distributions)
        ):
            return super()._pauli_expectation_single_shadow(shadow_idx, observable)

        distribution = self.noise_corrected_distributions[shadow_idx]
        if distribution.sum() == 0:
            return super()._pauli_expectation_single_shadow(shadow_idx, observable)

        pauli_string = observable.pauli_string
        relevant_qubits: List[int] = []
        pauli_to_basis = {"X": 1, "Y": 2, "Z": 0}
        support_size = 0  # Count non-identity Paulis

        for qubit_idx, pauli in enumerate(pauli_string):
            if pauli == "I":
                continue
            support_size += 1
            required_basis = pauli_to_basis.get(pauli)
            if required_basis is None:
                return 0.0

            measured_basis = int(self.measurement_bases[shadow_idx, qubit_idx])
            if measured_basis != required_basis:
                return 0.0

            relevant_qubits.append(qubit_idx)

        if not relevant_qubits:
            return observable.coefficient

        expectation = 0.0
        for state_index, probability in enumerate(distribution):
            if probability <= 0:
                continue

            parity = 1.0
            for qubit_idx in relevant_qubits:
                bit = (state_index >> qubit_idx) & 1
                parity *= 1 - 2 * bit

            expectation += probability * parity

        # Apply 3^k scaling factor for classical shadows inverse channel
        scaling_factor = 3 ** support_size
        return float(scaling_factor * expectation * observable.coefficient)

    @staticmethod
    def _bitstring_to_index(bitstring: str) -> int:
        """Convert Qiskit bitstring ordering to little-endian index."""

        index = 0
        for qubit_idx, bit in enumerate(reversed(bitstring)):
            if bit == "1":
                index |= 1 << qubit_idx
        return index
