"""Tests for IBM connector utilities."""

from quartumse.connectors import create_backend_snapshot, resolve_backend
from quartumse.reporting.manifest import BackendSnapshot


def test_resolve_backend_descriptor_falls_back_to_aer():
    """`ibm:aer_simulator` should resolve to a local Aer backend."""

    backend, snapshot = resolve_backend("ibm:aer_simulator")

    # The Aer simulator exposes the same interface as hardware backends.
    assert backend.name == "aer_simulator"
    assert isinstance(snapshot, BackendSnapshot)
    assert snapshot.backend_name == backend.name
    assert snapshot.calibration_timestamp is not None


def test_create_backend_snapshot_returns_metadata():
    """Snapshot helper should surface configuration even without calibrations."""

    backend, _ = resolve_backend("ibm:aer_simulator")
    snapshot = create_backend_snapshot(backend)

    assert snapshot.backend_name == backend.name
    assert isinstance(snapshot.basis_gates, list)
    assert snapshot.properties_hash is not None
