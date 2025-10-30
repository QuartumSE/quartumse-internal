"""Tests for backend-aware batching in the shadow estimator."""

from __future__ import annotations

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from quartumse.estimator.shadow_estimator import ShadowEstimator
from quartumse.shadows.config import ShadowConfig
from quartumse.shadows.core import Observable


class _ConfigWithMaxExperiments:
    """Lightweight wrapper to inject a max_experiments limit."""

    def __init__(self, base_config, max_experiments: int):
        self._base_config = base_config
        self.max_experiments = max_experiments

    def __getattr__(self, item):  # pragma: no cover - passthrough convenience
        return getattr(self._base_config, item)


def test_shadow_estimator_batches_by_backend_limit(monkeypatch, tmp_path):
    backend = AerSimulator(seed_simulator=999)

    original_configuration = backend.configuration

    def limited_configuration():
        base = original_configuration()
        return _ConfigWithMaxExperiments(base, max_experiments=2)

    monkeypatch.setattr(backend, "configuration", limited_configuration)

    run_batch_sizes = []
    original_run = backend.run

    def tracking_run(circuits, *args, **kwargs):
        batch_size = len(circuits) if isinstance(circuits, (list, tuple)) else 1
        run_batch_sizes.append(batch_size)
        return original_run(circuits, *args, **kwargs)

    monkeypatch.setattr(backend, "run", tracking_run)

    shadow_config = ShadowConfig(shadow_size=5, random_seed=42)
    estimator = ShadowEstimator(
        backend=backend,
        shadow_config=shadow_config,
        data_dir=tmp_path,
    )

    circuit = QuantumCircuit(1)
    circuit.h(0)

    observable = Observable("Z")
    result = estimator.estimate(circuit, [observable], save_manifest=False)

    # The estimator should have split the execution across multiple jobs.
    assert len(run_batch_sizes) > 1
    assert all(size <= 2 for size in run_batch_sizes)
    assert sum(run_batch_sizes) == shadow_config.shadow_size

    measurement_bases, measurement_outcomes, num_qubits = (
        estimator.shot_data_writer.load_shadow_measurements(result.experiment_id)
    )

    assert num_qubits == 1
    assert measurement_bases.shape[0] == shadow_config.shadow_size
    assert measurement_outcomes.shape[0] == shadow_config.shadow_size
    assert result.shots_used == shadow_config.shadow_size
