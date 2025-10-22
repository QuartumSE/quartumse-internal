"""Tests for the noise-aware classical shadows estimator."""

from __future__ import annotations

from pathlib import Path

import pytest

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from quartumse.estimator.shadow_estimator import ShadowEstimator
from quartumse.reporting.manifest import MitigationConfig, ProvenanceManifest
from quartumse.shadows.config import ShadowConfig, ShadowVersion
from quartumse.shadows.core import Observable
from quartumse.shadows.v1_noise_aware import NoiseAwareRandomLocalCliffordShadows


def test_shadow_estimator_noise_aware_runs_mem_pipeline(tmp_path):
    backend = AerSimulator(seed_simulator=321)

    shadow_config = ShadowConfig(
        version=ShadowVersion.V1_NOISE_AWARE,
        shadow_size=8,
        random_seed=11,
        apply_inverse_channel=True,
    )
    mitigation_config = MitigationConfig(parameters={"mem_shots": 512})

    estimator = ShadowEstimator(
        backend=backend,
        shadow_config=shadow_config,
        mitigation_config=mitigation_config,
        data_dir=tmp_path,
    )

    circuit = QuantumCircuit(1)
    circuit.h(0)

    observable = Observable("Z")
    result = estimator.estimate(circuit, [observable], save_manifest=True)

    assert isinstance(estimator.shadow_impl, NoiseAwareRandomLocalCliffordShadows)
    assert estimator.measurement_error_mitigation is not None
    assert estimator.measurement_error_mitigation.confusion_matrix is not None

    distributions = estimator.shadow_impl.noise_corrected_distributions
    assert distributions is not None
    assert distributions.shape[0] == shadow_config.shadow_size

    assert "MEM" in estimator.mitigation_config.techniques

    confusion_path_str = estimator.mitigation_config.confusion_matrix_path
    assert confusion_path_str is not None
    confusion_path = Path(confusion_path_str)
    assert confusion_path.exists()
    assert confusion_path.suffix == ".npz"
    assert estimator.measurement_error_mitigation.confusion_matrix_path == confusion_path

    assert result.experiment_id is not None
    assert result.manifest_path is not None
    assert result.shot_data_path is not None
    assert Path(result.shot_data_path).exists()
    assert result.mitigation_confusion_matrix_path == confusion_path_str

    manifest_path = Path(result.manifest_path)
    manifest = ProvenanceManifest.from_json(manifest_path)
    assert "MEM" in manifest.schema.mitigation.techniques
    assert manifest.schema.mitigation.confusion_matrix_path == confusion_path_str


def test_noise_aware_replay_matches_original_estimates(tmp_path):
    backend = AerSimulator(seed_simulator=123)

    shadow_config = ShadowConfig(
        version=ShadowVersion.V1_NOISE_AWARE,
        shadow_size=12,
        random_seed=21,
        apply_inverse_channel=True,
    )

    estimator = ShadowEstimator(
        backend=backend,
        shadow_config=shadow_config,
        mitigation_config=MitigationConfig(parameters={"mem_shots": 256}),
        data_dir=tmp_path,
    )

    circuit = QuantumCircuit(1)
    circuit.h(0)

    observable = Observable("Z")
    original_result = estimator.estimate(circuit, [observable], save_manifest=True)

    replay_estimator = ShadowEstimator(
        backend=backend,
        shadow_config=ShadowConfig(version=ShadowVersion.V1_NOISE_AWARE),
        data_dir=tmp_path,
    )

    manifest_path = Path(original_result.manifest_path)
    replayed_result = replay_estimator.replay_from_manifest(manifest_path)

    obs_key = str(observable)
    assert obs_key in original_result.observables
    assert obs_key in replayed_result.observables

    original_value = original_result.observables[obs_key]["expectation_value"]
    replayed_value = replayed_result.observables[obs_key]["expectation_value"]
    assert abs(original_value - replayed_value) < 1e-10

    assert replayed_result.mitigation_confusion_matrix_path == (
        original_result.mitigation_confusion_matrix_path
    )
    assert replayed_result.shots_used == original_result.shots_used


def test_noise_aware_replay_missing_confusion_matrix(tmp_path):
    backend = AerSimulator(seed_simulator=456)

    shadow_config = ShadowConfig(
        version=ShadowVersion.V1_NOISE_AWARE,
        shadow_size=6,
        random_seed=5,
        apply_inverse_channel=True,
    )

    estimator = ShadowEstimator(
        backend=backend,
        shadow_config=shadow_config,
        mitigation_config=MitigationConfig(parameters={"mem_shots": 128}),
        data_dir=tmp_path,
    )

    circuit = QuantumCircuit(1)
    circuit.h(0)

    observable = Observable("Z")
    original_result = estimator.estimate(circuit, [observable], save_manifest=True)

    confusion_path = Path(original_result.mitigation_confusion_matrix_path)
    confusion_path.unlink()  # Simulate missing calibration artifact

    replay_estimator = ShadowEstimator(
        backend=backend,
        shadow_config=ShadowConfig(version=ShadowVersion.V1_NOISE_AWARE),
        data_dir=tmp_path,
    )

    manifest_path = Path(original_result.manifest_path)
    with pytest.raises(FileNotFoundError):
        replay_estimator.replay_from_manifest(manifest_path)
