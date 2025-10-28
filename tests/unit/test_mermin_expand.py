"""Tests for expanding Mermin observables into Pauli decompositions."""

from __future__ import annotations

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Pauli, Statevector

from experiments.pipeline._observables import expand_mermin_to_pauli


def _expectation(state: Statevector, pauli: str) -> float:
    operator = Pauli(pauli).to_matrix()
    value = np.vdot(state.data, operator @ state.data)
    return float(np.real_if_close(value))


def test_expand_mermin_expression_equivalence() -> None:
    """Expanded terms reproduce the expected Bell-state Mermin value."""

    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.cx(0, 1)
    state = Statevector.from_instruction(circuit)

    terms = expand_mermin_to_pauli("mermin: XX - YY")
    assert terms == [("XX", 1.0), ("YY", -1.0)]

    expectation = sum(coefficient * _expectation(state, pauli) for pauli, coefficient in terms)
    assert expectation == pytest.approx(2.0, rel=1e-12, abs=1e-12)


def test_expand_mermin_invalid_expression() -> None:
    with pytest.raises(ValueError):
        expand_mermin_to_pauli("mermin: sqrt(2)")

