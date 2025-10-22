import importlib.util
from pathlib import Path
import types

import pytest
from qiskit import QuantumCircuit

MODULE_PATH = Path(__file__).resolve().parents[3] / "experiments" / "validation" / "hardware_validation.py"
spec = importlib.util.spec_from_file_location("hardware_validation", MODULE_PATH)
hardware_validation = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(hardware_validation)  # type: ignore[attr-defined]


class FakeObservable:
    def __init__(self, pauli_string: str, coefficient: float = 1.0):
        self.pauli_string = pauli_string
        self.coefficient = coefficient

    def __str__(self) -> str:
        return self.pauli_string


class FakeResult:
    def __init__(self, backend_name: str, shots: int, num_qubits: int):
        self.backend_name = backend_name
        self._shots = shots
        self._num_qubits = num_qubits

    def get_counts(self):
        return {"0" * self._num_qubits: self._shots}


class FakeJob:
    def __init__(self, backend_name: str, shots: int, num_qubits: int):
        self._backend_name = backend_name
        self._shots = shots
        self._num_qubits = num_qubits

    def backend(self):
        return types.SimpleNamespace(name=self._backend_name)

    def result(self):
        return FakeResult(self._backend_name, self._shots, self._num_qubits)


class FakeBackend:
    def __init__(self):
        self.name = "ibm_fake"
        self._calls = 0

    def run(self, circuit, shots):
        self._calls += 1
        backend_name = "ibm_fake" if self._calls == 1 else "ibm_fake_alt"
        return FakeJob(backend_name, shots, circuit.num_qubits)


def test_run_baseline_measurement_detects_backend_switch(monkeypatch):
    qc = QuantumCircuit(1)
    observables = [FakeObservable("Z"), FakeObservable("I")]
    shot_allocation = {str(obs): 4 for obs in observables}

    fake_backend = FakeBackend()

    monkeypatch.setattr(hardware_validation, "transpile", lambda circuit, backend: circuit)

    with pytest.raises(RuntimeError, match="expected"):
        hardware_validation.run_baseline_measurement(
            qc,
            observables,
            fake_backend,
            shot_allocation,
            expected_backend_name="ibm_fake",
        )
