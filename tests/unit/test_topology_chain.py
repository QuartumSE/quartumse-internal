"""Tests for topology-aware linear chain selection."""

import logging
from types import SimpleNamespace

import pytest

from quartumse.connectors.topology import get_linear_chain


class DummyBackend:
    """Minimal backend stub providing configuration and metadata."""

    def __init__(self, num_qubits, coupling_map=None, name="dummy"):
        self._configuration = SimpleNamespace(num_qubits=num_qubits, coupling_map=coupling_map)
        self.num_qubits = num_qubits
        self.name = name

    def configuration(self):
        return self._configuration


def test_linear_chain_exact_path():
    backend = DummyBackend(5, coupling_map=[[0, 1], [1, 2], [2, 3], [3, 4]])
    chain = get_linear_chain(backend, 4)
    assert chain in ([0, 1, 2, 3], [1, 2, 3, 4])


def test_linear_chain_multi_hop_path():
    backend = DummyBackend(4, coupling_map=[[0, 1, 2, 3]])
    chain = get_linear_chain(backend, 3)
    assert chain == [0, 1, 2] or chain == [1, 2, 3]


def test_linear_chain_fallback_logs(caplog):
    backend = DummyBackend(4, coupling_map=None)
    with caplog.at_level(logging.INFO):
        chain = get_linear_chain(backend, 3)
    assert chain == [0, 1, 2]
    assert "greedy linear chain" in caplog.text


def test_linear_chain_invalid_length():
    backend = DummyBackend(3, coupling_map=[[0, 1]])
    with pytest.raises(ValueError):
        get_linear_chain(backend, 0)


def test_linear_chain_capacity_failure():
    backend = DummyBackend(3, coupling_map=[[0, 1]])
    with pytest.raises(ValueError):
        get_linear_chain(backend, 4)
