"""Pytest configuration and fixtures."""

import pytest
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from quartumse.shadows import ShadowConfig
from quartumse.shadows.core import Observable


@pytest.fixture
def backend():
    """Aer simulator backend."""
    return AerSimulator()


@pytest.fixture
def shadow_config():
    """Default shadow configuration."""
    return ShadowConfig(shadow_size=100, random_seed=42)


@pytest.fixture
def ghz_circuit_3q():
    """3-qubit GHZ circuit."""
    qc = QuantumCircuit(3)
    qc.h(0)
    qc.cx(0, 1)
    qc.cx(0, 2)
    return qc


@pytest.fixture
def ghz_circuit_4q():
    """4-qubit GHZ circuit."""
    qc = QuantumCircuit(4)
    qc.h(0)
    for i in range(1, 4):
        qc.cx(0, i)
    return qc


@pytest.fixture
def simple_observables_3q():
    """Simple observables for 3-qubit system."""
    return [
        Observable("ZII", coefficient=1.0),
        Observable("IZI", coefficient=1.0),
        Observable("IIZ", coefficient=1.0),
        Observable("ZZI", coefficient=1.0),
    ]


@pytest.fixture
def bell_circuit():
    """Bell state circuit."""
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    return qc


@pytest.fixture
def simple_observables_2q():
    """Simple observables for 2-qubit system."""
    return [
        Observable("ZI", coefficient=1.0),
        Observable("IZ", coefficient=1.0),
        Observable("ZZ", coefficient=1.0),
        Observable("XX", coefficient=1.0),
    ]
def pytest_addoption(parser):
    """Register no-op coverage options for offline test environments."""

    parser.addoption(
        "--cov",
        action="append",
        default=[],
        help="No-op stub to satisfy pytest configuration when pytest-cov is unavailable.",
    )
    parser.addoption(
        "--cov-report",
        action="append",
        default=[],
        help="No-op stub to satisfy pytest configuration when pytest-cov is unavailable.",
    )

