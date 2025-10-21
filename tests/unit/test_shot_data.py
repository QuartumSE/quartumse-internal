"""Tests for shot data persistence and replay functionality."""

import tempfile
from pathlib import Path

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from quartumse import ShadowEstimator
from quartumse.reporting.shot_data import ShotDataDiagnostics, ShotDataWriter
from quartumse.shadows import ShadowConfig
from quartumse.shadows.core import Observable


class TestShotDataWriter:
    """Test ShotDataWriter functionality."""

    def test_save_and_load_shadow_measurements(self):
        """Test saving and loading shadow measurements to/from Parquet."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ShotDataWriter(Path(tmpdir))

            # Create test data
            experiment_id = "test-experiment-123"
            shadow_size = 100
            num_qubits = 3

            # Random measurement bases (0=Z, 1=X, 2=Y)
            measurement_bases = np.random.randint(0, 3, size=(shadow_size, num_qubits))

            # Random measurement outcomes (0 or 1)
            measurement_outcomes = np.random.randint(0, 2, size=(shadow_size, num_qubits))

            # Save to Parquet
            parquet_path = writer.save_shadow_measurements(
                experiment_id, measurement_bases, measurement_outcomes, num_qubits
            )

            assert parquet_path.exists()
            assert parquet_path.suffix == ".parquet"

            # Load back
            loaded_bases, loaded_outcomes, loaded_num_qubits = (
                writer.load_shadow_measurements(experiment_id)
            )

            # Verify data integrity
            np.testing.assert_array_equal(measurement_bases, loaded_bases)
            np.testing.assert_array_equal(measurement_outcomes, loaded_outcomes)
            assert num_qubits == loaded_num_qubits

    def test_load_nonexistent_experiment(self):
        """Test loading from nonexistent experiment ID raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ShotDataWriter(Path(tmpdir))

            with pytest.raises(FileNotFoundError):
                writer.load_shadow_measurements("nonexistent-id")


class TestShadowEstimatorPersistence:
    """Test ShadowEstimator shot data persistence."""

    def test_estimate_saves_shot_data(self):
        """Test that estimate() saves shot data to Parquet."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            backend = "ibm:aer_simulator"
            shadow_config = ShadowConfig(shadow_size=50, random_seed=42)
            estimator = ShadowEstimator(
                backend=backend, shadow_config=shadow_config, data_dir=tmpdir
            )

            # Create simple 2-qubit circuit
            circuit = QuantumCircuit(2)
            circuit.h(0)
            circuit.cx(0, 1)

            # Observables
            observables = [Observable("ZZ"), Observable("XX")]

            # Run estimation
            result = estimator.estimate(circuit, observables, save_manifest=True)

            # Check that shot data was saved
            shots_dir = Path(tmpdir) / "shots"
            assert shots_dir.exists()

            parquet_files = list(shots_dir.glob("*.parquet"))
            assert len(parquet_files) == 1

            # Verify manifest references the correct shot file
            from quartumse.reporting.manifest import ProvenanceManifest

            manifest_path = Path(result.manifest_path)
            manifest = ProvenanceManifest.from_json(manifest_path)
            experiment_id = manifest.schema.experiment_id

            shot_path = Path(manifest.schema.shot_data_path)
            assert shot_path.exists()
            assert shot_path == estimator.shot_data_writer.shots_dir / f"{experiment_id}.parquet"

            loaded_bases, loaded_outcomes, loaded_num_qubits = (
                estimator.shot_data_writer.load_shadow_measurements(experiment_id)
            )

            assert loaded_num_qubits == 2
            assert loaded_bases.shape == (50, 2)
            assert loaded_outcomes.shape == (50, 2)

            # Diagnostics should be computable
            diagnostics = estimator.shot_data_writer.summarize_shadow_measurements(experiment_id)
            assert isinstance(diagnostics, ShotDataDiagnostics)
            assert diagnostics.total_shots == 50

            # Manifest validation should succeed when file is present
            assert manifest.validate()

            # Removing the shot file should trigger validation failure
            shot_path.unlink()
            with pytest.raises(FileNotFoundError):
                manifest.validate()

    def test_replay_from_manifest(self):
        """Test replaying an experiment from saved manifest and shot data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            backend = AerSimulator()
            shadow_config = ShadowConfig(shadow_size=100, random_seed=42)
            estimator = ShadowEstimator(
                backend=backend, shadow_config=shadow_config, data_dir=tmpdir
            )

            # Create GHZ state
            circuit = QuantumCircuit(3)
            circuit.h(0)
            circuit.cx(0, 1)
            circuit.cx(1, 2)

            # Observables
            original_observables = [Observable("ZZZ"), Observable("XXX")]

            # Run original estimation
            original_result = estimator.estimate(
                circuit, original_observables, save_manifest=True
            )

            # Replay from manifest with same observables
            replayed_result = estimator.replay_from_manifest(
                manifest_path=original_result.manifest_path,
                observables=original_observables,
            )

            # Results should match (same shot data, same observables)
            for obs in original_observables:
                obs_str = str(obs)
                original_exp = original_result.observables[obs_str]["expectation_value"]
                replayed_exp = replayed_result.observables[obs_str]["expectation_value"]

                # Should be identical since we're using the same shot data
                assert abs(original_exp - replayed_exp) < 1e-10

    def test_replay_with_different_observables(self):
        """Test replaying with different observables than original."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            backend = AerSimulator()
            shadow_config = ShadowConfig(shadow_size=100, random_seed=42)
            estimator = ShadowEstimator(
                backend=backend, shadow_config=shadow_config, data_dir=tmpdir
            )

            # Create Bell state
            circuit = QuantumCircuit(2)
            circuit.h(0)
            circuit.cx(0, 1)

            # Original observables
            original_observables = [Observable("ZZ")]

            # Run original estimation
            original_result = estimator.estimate(
                circuit, original_observables, save_manifest=True
            )

            # Replay with different observable (leveraging classical shadows' reusability)
            new_observables = [Observable("XX"), Observable("YY")]

            replayed_result = estimator.replay_from_manifest(
                manifest_path=original_result.manifest_path, observables=new_observables
            )

            # Should have estimates for new observables
            assert str(Observable("XX")) in replayed_result.observables
            assert str(Observable("YY")) in replayed_result.observables

            # Original observable should not be in the replayed result
            assert str(Observable("ZZ")) not in replayed_result.observables

    def test_replay_without_observables_uses_manifest(self):
        """Test replaying without specifying observables uses manifest's observables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup
            backend = AerSimulator()
            shadow_config = ShadowConfig(shadow_size=100, random_seed=42)
            estimator = ShadowEstimator(
                backend=backend, shadow_config=shadow_config, data_dir=tmpdir
            )

            # Create circuit
            circuit = QuantumCircuit(2)
            circuit.h(0)

            # Observables
            observables = [Observable("ZI"), Observable("IZ")]

            # Run original estimation
            original_result = estimator.estimate(circuit, observables, save_manifest=True)

            # Replay without specifying observables
            replayed_result = estimator.replay_from_manifest(
                manifest_path=original_result.manifest_path
            )

            # Should have same observables as original
            assert set(replayed_result.observables.keys()) == set(
                original_result.observables.keys()
            )


def test_summarize_shadow_measurements_computes_expected_statistics():
    """ShotDataWriter should compute intuitive diagnostics from toy data."""

    with tempfile.TemporaryDirectory() as tmpdir:
        writer = ShotDataWriter(Path(tmpdir))

        experiment_id = "diag-test"
        measurement_bases = np.array([[0, 1], [0, 1], [2, 2]])
        measurement_outcomes = np.array([[0, 1], [0, 1], [1, 0]])

        writer.save_shadow_measurements(
            experiment_id, measurement_bases, measurement_outcomes, num_qubits=2
        )

        diagnostics = writer.summarize_shadow_measurements(experiment_id)

        assert diagnostics.total_shots == 3
        assert diagnostics.num_qubits == 2
        assert diagnostics.measurement_basis_distribution["ZX"] == 2
        assert diagnostics.measurement_basis_distribution["YY"] == 1

        # Top bitstrings should include the repeated 01 outcome
        assert diagnostics.bitstring_histogram.get("01", 0) >= 2

        marginals = diagnostics.qubit_marginals
        assert pytest.approx(marginals[0]["0"], 1e-6) == 2 / 3
        assert pytest.approx(marginals[1]["1"], 1e-6) == 2 / 3
