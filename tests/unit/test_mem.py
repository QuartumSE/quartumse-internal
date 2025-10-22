"""Unit tests for measurement error mitigation utilities."""

from __future__ import annotations

import numpy as np
import pytest
from qiskit_aer import AerSimulator

from quartumse.mitigation import MeasurementErrorMitigation


def test_mem_calibration_returns_confusion_matrix_identity_close(tmp_path):
    backend = AerSimulator(seed_simulator=123)
    mem = MeasurementErrorMitigation(backend)

    output_path = tmp_path / "confusion" / "matrix.npz"
    saved_path = mem.calibrate(
        qubits=[0, 1],
        shots=4096,
        run_options={"seed_simulator": 123},
        output_path=output_path,
    )

    assert saved_path is not None
    assert saved_path.exists()
    assert saved_path.suffix == ".npz"
    assert mem.confusion_matrix_path == saved_path
    assert mem.confusion_matrix is not None
    assert mem.confusion_matrix.shape == (4, 4)

    with np.load(saved_path) as data:
        persisted = data["confusion_matrix"]

    assert np.allclose(mem.confusion_matrix, persisted)
    assert np.allclose(mem.confusion_matrix, np.eye(4), atol=0.05)


def test_mem_apply_inverts_confusion_matrix():
    backend = AerSimulator()
    mem = MeasurementErrorMitigation(backend)
    mem.confusion_matrix = np.array([[0.9, 0.2], [0.1, 0.8]])

    corrected = mem.apply({"0": 720, "1": 280})

    assert corrected["0"] == pytest.approx(742.85714286, rel=1e-6)
    assert corrected["1"] == pytest.approx(257.14285714, rel=1e-6)
    assert pytest.approx(sum(corrected.values()), rel=1e-9) == 1000.0
