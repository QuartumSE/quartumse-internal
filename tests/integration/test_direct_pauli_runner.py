"""Integration tests for the direct Pauli runner."""

import logging

import pytest
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from experiments.pipeline._runners import run_direct_pauli
from quartumse.shadows.core import Observable


@pytest.fixture
def seeded_backend() -> AerSimulator:
    backend = AerSimulator(seed_simulator=123)
    return backend


def test_even_shot_split_and_expectations(seeded_backend: AerSimulator) -> None:
    circuit = QuantumCircuit(3)

    observables = [
        Observable("ZII"),
        Observable("IZI"),
        Observable("IIZ"),
        Observable("ZZI"),
        Observable("ZIZ"),
        Observable("IZZ"),
    ]

    result = run_direct_pauli(circuit, observables, seeded_backend, total_shots=5000)

    assert result["total_shots_used"] == 5000
    results_by_obs = result["results_by_obs"]

    expected_allocations = [834, 834, 833, 833, 833, 833]
    for obs, expected_shots in zip(observables, expected_allocations, strict=False):
        obs_result = results_by_obs[obs.pauli_string]
        assert obs_result["shots"] == expected_shots
        assert obs_result["expectation"] == pytest.approx(1.0, rel=0, abs=0)


def test_basis_rotations_and_logging(
    seeded_backend: AerSimulator, caplog: pytest.LogCaptureFixture
) -> None:
    circuit = QuantumCircuit(1)
    circuit.h(0)
    circuit.s(0)

    observables = [Observable("X"), Observable("Y")]

    with caplog.at_level(logging.INFO):
        result = run_direct_pauli(circuit, observables, seeded_backend, total_shots=1000)

    results_by_obs = result["results_by_obs"]

    assert results_by_obs["X"]["expectation"] == pytest.approx(0.0, abs=0.1)
    assert results_by_obs["Y"]["expectation"] == pytest.approx(1.0, abs=0.05)

    allocations = [entry["shots"] for entry in results_by_obs.values()]
    assert sorted(allocations) == [500, 500]

    name_attr = getattr(seeded_backend, "name", None)
    backend_name = name_attr() if callable(name_attr) else name_attr
    assert any(str(backend_name) in record.message for record in caplog.records)
    for obs in observables:
        assert any(obs.pauli_string in record.message for record in caplog.records)
