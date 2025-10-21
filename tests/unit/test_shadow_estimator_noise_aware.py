"""Tests for the noise-aware classical shadows estimator."""

from __future__ import annotations

from pathlib import Path

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

    manifest_path = Path(result.manifest_path)
    manifest = ProvenanceManifest.from_json(manifest_path)
    assert "MEM" in manifest.schema.mitigation.techniques
