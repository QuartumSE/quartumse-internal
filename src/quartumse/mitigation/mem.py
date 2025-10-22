"""Measurement Error Mitigation (MEM) utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional, Sequence, Union

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.providers import Backend

from quartumse.connectors import create_runtime_sampler, is_ibm_runtime_backend


LOGGER = logging.getLogger(__name__)


class MeasurementErrorMitigation:
    """
    Measurement error mitigation using confusion matrix inversion.

    Calibrates a confusion matrix and applies it to correct noisy measurements.
    """

    def __init__(self, backend: Backend):
        self.backend = backend
        self.confusion_matrix: Optional[np.ndarray] = None
        self._calibrated_qubits: Optional[tuple[int, ...]] = None
        self._runtime_sampler = None
        self._runtime_sampler_checked = False
        self._use_runtime_sampler = is_ibm_runtime_backend(backend)
        self.confusion_matrix_path: Optional[Path] = None

    def _get_runtime_sampler(self):
        """Initialise (if necessary) and return an IBM Runtime sampler."""

        if not self._use_runtime_sampler:
            return None

        if not self._runtime_sampler_checked:
            self._runtime_sampler = create_runtime_sampler(self.backend)
            self._runtime_sampler_checked = True

        return self._runtime_sampler

    def calibrate(
        self,
        qubits: Sequence[int],
        shots: int = 4096,
        run_options: Optional[Dict[str, object]] = None,
        *,
        output_path: Optional[Union[str, Path]] = None,
    ) -> Optional[Path]:
        """
        Calibrate confusion matrix by preparing and measuring basis states.

        Args:
            qubits: List of qubit indices to calibrate
            shots: Number of calibration shots per basis state
            run_options: Backend execution options
            output_path: Optional path where the confusion matrix should be
                persisted. If provided the directory is created automatically
                and the matrix is saved as a compressed ``.npz`` archive.

        Returns:
            Path to the persisted confusion matrix if ``output_path`` is provided.
            The calibrated confusion matrix is stored on the instance as
            :attr:`confusion_matrix`.
        """

        if not qubits:
            raise ValueError("At least one qubit must be provided for calibration")

        run_options = dict(run_options or {})

        num_qubits = len(qubits)
        num_states = 2**num_qubits

        calibration_circuits: list[QuantumCircuit] = []
        for prepared_index in range(num_states):
            qc = QuantumCircuit(num_qubits, num_qubits)

            for qubit_idx in range(num_qubits):
                if (prepared_index >> qubit_idx) & 1:
                    qc.x(qubit_idx)

            qc.measure(range(num_qubits), range(num_qubits))
            calibration_circuits.append(qc)

        transpiled_circuits = transpile(
            calibration_circuits,
            backend=self.backend,
            initial_layout=list(qubits),
        )

        sampler = self._get_runtime_sampler()
        if sampler is not None:
            try:
                job = sampler.run(list(transpiled_circuits), shots=shots, **run_options)
            except TypeError:
                if run_options:
                    LOGGER.warning(
                        "SamplerV2.run does not accept run options %s; submitting without them.",
                        run_options,
                    )
                job = sampler.run(list(transpiled_circuits), shots=shots)
            result = job.result()

            def _get_counts(batch_index: int):
                return result[batch_index].data.meas.get_counts()

        else:
            job = self.backend.run(transpiled_circuits, shots=shots, **run_options)
            result = job.result()

            def _get_counts(batch_index: int):
                return result.get_counts(batch_index)

        confusion = np.zeros((num_states, num_states), dtype=float)
        for prepared_index in range(num_states):
            counts = _get_counts(prepared_index)
            total = sum(counts.values())
            if total == 0:
                continue

            for bitstring, count in counts.items():
                measured_index = self._bitstring_to_index(bitstring)
                confusion[measured_index, prepared_index] = count / total

        self.confusion_matrix = confusion
        self._calibrated_qubits = tuple(qubits)

        self.confusion_matrix_path = None
        if output_path is not None:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(path, confusion_matrix=confusion)
            self.confusion_matrix_path = path.resolve()

        return self.confusion_matrix_path

    def apply(self, counts: Dict[str, int]) -> Dict[str, float]:
        """
        Apply mitigation to measurement counts.

        Args:
            counts: Raw measurement counts

        Returns:
            Mitigated (possibly non-integer) counts
        """
        if self.confusion_matrix is None:
            raise ValueError("Must calibrate before applying mitigation")

        num_states = self.confusion_matrix.shape[0]
        num_qubits = int(np.log2(num_states))

        counts_vector = np.zeros(num_states, dtype=float)
        for bitstring, count in counts.items():
            state_index = self._bitstring_to_index(bitstring)
            counts_vector[state_index] += count

        total_counts = counts_vector.sum()
        if total_counts == 0:
            return {}

        measured_probabilities = counts_vector / total_counts

        try:
            inverse_confusion = np.linalg.inv(self.confusion_matrix)
        except np.linalg.LinAlgError:
            inverse_confusion = np.linalg.pinv(self.confusion_matrix)

        corrected_probabilities = inverse_confusion @ measured_probabilities
        corrected_probabilities = np.clip(corrected_probabilities, 0.0, None)

        probability_sum = corrected_probabilities.sum()
        if probability_sum > 0:
            corrected_probabilities = corrected_probabilities / probability_sum

        mitigated_counts = corrected_probabilities * total_counts

        mitigated_dict: Dict[str, float] = {}
        for state_index, value in enumerate(mitigated_counts):
            if value <= 1e-12:
                continue
            bitstring = self._index_to_bitstring(state_index, num_qubits)
            mitigated_dict[bitstring] = float(value)

        return mitigated_dict

    @staticmethod
    def _bitstring_to_index(bitstring: str) -> int:
        """Map a Qiskit-style bitstring to integer index (little-endian)."""

        index = 0
        for qubit_idx, bit in enumerate(reversed(bitstring)):
            if bit == "1":
                index |= 1 << qubit_idx
        return index

    @staticmethod
    def _index_to_bitstring(index: int, num_qubits: int) -> str:
        """Convert an index to Qiskit-style bitstring ordering."""

        return format(index, f"0{num_qubits}b")
