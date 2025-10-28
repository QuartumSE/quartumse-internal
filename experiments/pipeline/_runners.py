"""Execution helpers for experiment pipeline runners."""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, TypedDict, Union

from qiskit import ClassicalRegister, QuantumCircuit, transpile
from qiskit.providers import Backend
from qiskit.result import Counts

from quartumse.shadows.core import Observable


logger = logging.getLogger(__name__)


class ObservableRunResult(TypedDict):
    """Result container for a single observable run."""

    shots: int
    expectation: float


class DirectPauliResult(TypedDict):
    """Return type for :func:`run_direct_pauli`."""

    results_by_obs: Dict[str, ObservableRunResult]
    total_shots_used: int


ObservableLike = Union[Observable, str]


def _ensure_observable(obj: ObservableLike) -> Observable:
    """Normalize observable inputs to :class:`Observable` objects."""
    if isinstance(obj, Observable):
        return obj
    return Observable(str(obj))


def _basis_rotation(pauli: str, circuit: QuantumCircuit, qubit: int) -> None:
    """Apply basis rotation to measure the provided Pauli."""
    if pauli == "X":
        circuit.h(qubit)
    elif pauli == "Y":
        circuit.sdg(qubit)
        circuit.h(qubit)
    elif pauli not in {"I", "Z"}:
        raise ValueError(f"Unsupported Pauli '{pauli}' in observable")


def _expectation_from_counts(counts: Counts) -> float:
    """Compute Pauli expectation value from measurement counts."""
    total_shots = sum(counts.values())
    if total_shots == 0:
        return 0.0

    expectation = 0.0
    for bitstring, count in counts.items():
        cleaned = bitstring.replace(" ", "")
        parity = (-1) ** cleaned.count("1")
        expectation += parity * count

    return expectation / total_shots


def _allocate_shots(total_shots: int, num_observables: int) -> List[int]:
    """Evenly split the total shot budget across observables."""
    if num_observables <= 0:
        raise ValueError("No observables provided for direct Pauli runner")

    base, remainder = divmod(total_shots, num_observables)
    return [base + (1 if idx < remainder else 0) for idx in range(num_observables)]


def run_direct_pauli(
    circuit: QuantumCircuit,
    observables: Iterable[ObservableLike],
    backend: Backend,
    total_shots: int = 5000,
) -> DirectPauliResult:
    """Execute direct Pauli measurements with an even shot split.

    Args:
        circuit: The state-preparation circuit.
        observables: Iterable of observables (Pauli strings or :class:`Observable`).
        backend: Backend instance to execute the jobs on.
        total_shots: Total shot budget to split across observables.

    Returns:
        Dictionary with keys ``results_by_obs`` and ``total_shots_used``.
    """

    observables_list = [_ensure_observable(obs) for obs in observables]
    allocations = _allocate_shots(total_shots, len(observables_list))

    backend_name = getattr(backend, "name", None)
    if callable(backend_name):
        backend_name = backend_name()

    results: Dict[str, ObservableRunResult] = {}
    total_shots_used = 0

    for allocation, observable in zip(allocations, observables_list):
        obs_label = observable.pauli_string
        logger.info(
            "Direct Pauli allocation: observable %s -> %d shots on backend %s",
            obs_label,
            allocation,
            backend_name,
        )

        if allocation == 0:
            results[obs_label] = {"shots": allocation, "expectation": 0.0}
            continue

        measured_qubits: List[int] = [
            idx for idx, pauli in enumerate(observable.pauli_string) if pauli != "I"
        ]

        if not measured_qubits:
            results[obs_label] = {
                "shots": allocation,
                "expectation": float(observable.coefficient),
            }
            total_shots_used += allocation
            continue

        measurement_circuit = circuit.copy()
        classical_register = ClassicalRegister(len(measured_qubits), "m")
        measurement_circuit.add_register(classical_register)

        for reg_idx, qubit_idx in enumerate(measured_qubits):
            pauli = observable.pauli_string[qubit_idx]
            _basis_rotation(pauli, measurement_circuit, qubit_idx)
            measurement_circuit.measure(qubit_idx, classical_register[reg_idx])

        transpiled_circuit = transpile(measurement_circuit, backend)

        logger.info(
            "Submitting direct Pauli job for observable %s to backend %s with %d shots",
            obs_label,
            backend_name,
            allocation,
        )
        job = backend.run(transpiled_circuit, shots=allocation)
        result = job.result()
        counts = result.get_counts(transpiled_circuit)
        expectation = _expectation_from_counts(counts) * observable.coefficient

        results[obs_label] = {
            "shots": allocation,
            "expectation": expectation,
        }
        total_shots_used += allocation

    return {
        "results_by_obs": results,
        "total_shots_used": total_shots_used,
    }
