"""Unit tests for measurement error mitigation utilities."""

from __future__ import annotations

import numpy as np
import pytest
from qiskit_aer import AerSimulator

from quartumse.mitigation import MeasurementErrorMitigation


def test_mem_calibration_returns_confusion_matrix_identity_close():
    backend = AerSimulator(seed_simulator=123)
    mem = MeasurementErrorMitigation(backend)

    confusion = mem.calibrate(
        qubits=[0, 1], shots=4096, run_options={"seed_simulator": 123}
    )

    assert confusion.shape == (4, 4)
    assert np.allclose(confusion, np.eye(4), atol=0.05)


def test_mem_apply_inverts_confusion_matrix():
    backend = AerSimulator()
    mem = MeasurementErrorMitigation(backend)
    mem.confusion_matrix = np.array([[0.9, 0.2], [0.1, 0.8]])

    corrected = mem.apply({"0": 720, "1": 280})

    assert corrected["0"] == pytest.approx(742.85714286, rel=1e-6)
    assert corrected["1"] == pytest.approx(257.14285714, rel=1e-6)
    assert pytest.approx(sum(corrected.values()), rel=1e-9) == 1000.0
