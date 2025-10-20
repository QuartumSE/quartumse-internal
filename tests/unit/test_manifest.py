"""Unit tests for provenance manifest."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from quartumse.reporting.manifest import (
    BackendSnapshot,
    CircuitFingerprint,
    ManifestSchema,
    MitigationConfig,
    ProvenanceManifest,
    ResourceUsage,
    ShadowsConfig,
)


class TestCircuitFingerprint:
    """Test circuit fingerprint creation."""

    def test_circuit_fingerprint_creation(self):
        """Test creating a circuit fingerprint."""
        fp = CircuitFingerprint(
            qasm3="OPENQASM 3.0; qubit[2] q; h q[0]; cx q[0], q[1];",
            num_qubits=2,
            depth=2,
            gate_counts={"h": 1, "cx": 1},
        )

        assert fp.num_qubits == 2
        assert fp.depth == 2
        assert fp.circuit_hash is not None
        assert len(fp.circuit_hash) == 16  # Truncated SHA256

    def test_circuit_hash_auto_generation(self):
        """Test that circuit hash is auto-generated from QASM."""
        fp1 = CircuitFingerprint(
            qasm3="OPENQASM 3.0; qubit[2] q; h q[0];",
            num_qubits=2,
            depth=1,
            gate_counts={"h": 1},
        )

        fp2 = CircuitFingerprint(
            qasm3="OPENQASM 3.0; qubit[2] q; h q[0];",
            num_qubits=2,
            depth=1,
            gate_counts={"h": 1},
        )

        # Same QASM should produce same hash
        assert fp1.circuit_hash == fp2.circuit_hash


class TestManifestSchema:
    """Test manifest schema validation."""

    def test_minimal_manifest_creation(self):
        """Test creating a minimal valid manifest."""
        circuit_fp = CircuitFingerprint(
            qasm3="OPENQASM 3.0; qubit[1] q; h q[0];",
            num_qubits=1,
            depth=1,
            gate_counts={"h": 1},
        )

        backend = BackendSnapshot(
            backend_name="aer_simulator",
            backend_version="0.13.0",
            num_qubits=5,
            basis_gates=["id", "rz", "sx", "cx"],
            calibration_timestamp=datetime.utcnow(),
            properties_hash="test_hash",
        )

        resource_usage = ResourceUsage(total_shots=1000, execution_time_seconds=1.5)

        manifest = ManifestSchema(
            experiment_id="test-123",
            circuit=circuit_fp,
            observables=[{"pauli": "Z"}],
            backend=backend,
            mitigation=MitigationConfig(),
            shot_data_path="data/shots/test.parquet",
            results_summary={"Z": 0.5},
            resource_usage=resource_usage,
            quartumse_version="0.1.0",
            qiskit_version="1.0.0",
            python_version="3.10.0",
        )

        assert manifest.experiment_id == "test-123"
        assert manifest.circuit.num_qubits == 1
        assert manifest.resource_usage.total_shots == 1000

    def test_manifest_json_serialization(self):
        """Test that manifest can be serialized to JSON."""
        circuit_fp = CircuitFingerprint(
            qasm3="OPENQASM 3.0;",
            num_qubits=1,
            depth=1,
            gate_counts={},
        )

        backend = BackendSnapshot(
            backend_name="test_backend",
            backend_version="1.0",
            num_qubits=5,
            basis_gates=["h", "cx"],
            calibration_timestamp=datetime.utcnow(),
            properties_hash="hash",
        )

        resource_usage = ResourceUsage(total_shots=100, execution_time_seconds=1.0)

        manifest = ManifestSchema(
            experiment_id="test",
            circuit=circuit_fp,
            observables=[],
            backend=backend,
            mitigation=MitigationConfig(),
            shot_data_path="test.parquet",
            results_summary={},
            resource_usage=resource_usage,
            quartumse_version="0.1.0",
            qiskit_version="1.0.0",
            python_version="3.10.0",
        )

        # Should be serializable
        json_str = manifest.model_dump_json()
        assert json_str is not None
        assert "test" in json_str


class TestProvenanceManifest:
    """Test provenance manifest high-level API."""

    def test_manifest_creation_and_save(self):
        """Test creating and saving a manifest."""
        circuit_fp = CircuitFingerprint(
            qasm3="OPENQASM 3.0;",
            num_qubits=2,
            depth=3,
            gate_counts={"h": 1, "cx": 1},
        )

        backend = BackendSnapshot(
            backend_name="aer_simulator",
            backend_version="0.13.0",
            num_qubits=5,
            basis_gates=["h", "cx"],
            calibration_timestamp=datetime.utcnow(),
            properties_hash="test",
        )

        manifest = ProvenanceManifest.create(
            experiment_id="test-manifest-001",
            circuit_fingerprint=circuit_fp,
            backend_snapshot=backend,
            observables=[{"pauli": "ZZ"}],
            shot_data_path="test.parquet",
            results_summary={"ZZ": 1.0},
            resource_usage=ResourceUsage(total_shots=500, execution_time_seconds=2.0),
            quartumse_version="0.1.0",
            qiskit_version="1.0.0",
            python_version="3.10.0",
        )

        assert manifest.schema.experiment_id == "test-manifest-001"

        # Test saving and loading
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "manifest.json"
            manifest.to_json(path)

            assert path.exists()

            # Load back
            loaded = ProvenanceManifest.from_json(path)
            assert loaded.schema.experiment_id == "test-manifest-001"
            assert loaded.schema.circuit.num_qubits == 2

    def test_manifest_tags(self):
        """Test adding tags to manifest."""
        circuit_fp = CircuitFingerprint(qasm3="", num_qubits=1, depth=1, gate_counts={})
        backend = BackendSnapshot(
            backend_name="test",
            backend_version="1.0",
            num_qubits=5,
            basis_gates=[],
            calibration_timestamp=datetime.utcnow(),
            properties_hash="",
        )

        manifest = ProvenanceManifest.create(
            experiment_id="test",
            circuit_fingerprint=circuit_fp,
            backend_snapshot=backend,
            observables=[],
            shot_data_path="",
            results_summary={},
            resource_usage=ResourceUsage(total_shots=1, execution_time_seconds=1.0),
            quartumse_version="0.1.0",
            qiskit_version="1.0.0",
            python_version="3.10.0",
        )

        manifest.add_tag("ghz")
        manifest.add_tag("phase-1")
        manifest.add_tag("ghz")  # Duplicate

        assert len(manifest.schema.tags) == 2
        assert "ghz" in manifest.schema.tags
        assert "phase-1" in manifest.schema.tags
