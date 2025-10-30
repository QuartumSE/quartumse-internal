"""Unit tests for Stage-2 verifier utilities."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from experiments.pipeline.verifier import verify_experiment
from quartumse.estimator import ShadowEstimator
from quartumse.reporting.manifest import ProvenanceManifest
from quartumse.shadows import ShadowConfig
from quartumse.shadows.core import Observable


def _create_manifest(tmp_path: Path) -> Path:
    """Generate a manifest using the shadow estimator."""

    estimator = ShadowEstimator(
        backend=AerSimulator(),
        shadow_config=ShadowConfig(shadow_size=32, random_seed=1234),
        data_dir=tmp_path,
    )

    circuit = QuantumCircuit(1)
    circuit.h(0)

    observables = [Observable("Z"), Observable("X")]
    result = estimator.estimate(circuit, observables, save_manifest=True)
    assert result.manifest_path is not None

    return Path(result.manifest_path)


class TestVerifyExperiment:
    """Tests for the manifest verifier."""

    def test_positive_verification(self, tmp_path: Path) -> None:
        manifest_path = _create_manifest(tmp_path)

        report = verify_experiment(manifest_path)

        assert report["manifest_exists"]
        assert report["manifest_valid"]
        assert report["shot_data_exists"]
        assert report["shot_data_checksum_matches"]
        assert report["replay_matches"]
        assert report["max_abs_diff"] is not None
        assert report["max_abs_diff"] < 1e-12
        assert report["errors"] == []

    def test_missing_shot_data_detected(self, tmp_path: Path) -> None:
        manifest_path = _create_manifest(tmp_path)

        manifest = ProvenanceManifest.from_json(manifest_path)
        shot_path = Path(manifest.schema.shot_data_path)
        shot_path.unlink()

        report = verify_experiment(manifest_path)

        assert not report["shot_data_exists"]
        assert not report["replay_matches"]
        assert report["shot_data_checksum_matches"] is False
        assert any("Shot data" in err for err in report["errors"])

    def test_detects_modified_expectations(self, tmp_path: Path) -> None:
        manifest_path = _create_manifest(tmp_path)

        manifest_data = json.loads(manifest_path.read_text())
        results = manifest_data["results_summary"]
        observable_key = next(iter(results))
        results[observable_key]["expectation_value"] += 0.05
        manifest_path.write_text(json.dumps(manifest_data, indent=2))

        report = verify_experiment(manifest_path)

        assert not report["replay_matches"]
        assert report["max_abs_diff"] is not None
        assert report["max_abs_diff"] >= 0.05 - 1e-12
        assert any("Replay expectation values" in err for err in report["errors"])
        assert report["shot_data_checksum_matches"]

    def test_detects_shot_checksum_mismatch(self, tmp_path: Path) -> None:
        manifest_path = _create_manifest(tmp_path)

        manifest_data = json.loads(manifest_path.read_text())
        manifest_data["shot_data_checksum"] = "0" * 64
        manifest_path.write_text(json.dumps(manifest_data, indent=2))

        report = verify_experiment(manifest_path)

        assert report["shot_data_exists"]
        assert report["shot_data_checksum_matches"] is False
        assert any("checksum" in err.lower() for err in report["errors"])

    def test_detects_mem_checksum_mismatch(self, tmp_path: Path) -> None:
        manifest_path = _create_manifest(tmp_path)

        manifest_data = json.loads(manifest_path.read_text())
        mem_path = tmp_path / "confusion.json"
        mem_path.write_text(
            json.dumps({"confusion_matrix": [[1.0, 0.0], [0.0, 1.0]]}), encoding="utf-8"
        )

        mitigation = manifest_data.setdefault("mitigation", {})
        mitigation.setdefault("techniques", []).append("MEM")
        mitigation["confusion_matrix_path"] = str(mem_path)
        mitigation["confusion_matrix_checksum"] = hashlib.sha256(mem_path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest_data, indent=2))

        report_ok = verify_experiment(manifest_path)
        assert report_ok["mem_confusion_matrix_exists"] is True
        assert report_ok["mem_confusion_matrix_checksum_matches"] is True

        mem_path.write_text(
            json.dumps({"confusion_matrix": [[0.9, 0.1], [0.2, 0.8]]}),
            encoding="utf-8",
        )

        report_bad = verify_experiment(manifest_path)
        assert report_bad["mem_confusion_matrix_exists"] is True
        assert report_bad["mem_confusion_matrix_checksum_matches"] is False
        assert any("checksum" in err.lower() for err in report_bad["errors"])
