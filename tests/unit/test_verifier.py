"""Unit tests for Stage-2 verifier utilities."""

from __future__ import annotations

import json
from pathlib import Path

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from quartumse.estimator import ShadowEstimator
from quartumse.reporting.manifest import ProvenanceManifest
from quartumse.shadows import ShadowConfig
from quartumse.shadows.core import Observable

from experiments.pipeline.verifier import verify_experiment


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

