"""Shadow-based estimator implementation."""

import hashlib
import logging
import time
import uuid
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit, qasm3, transpile
from qiskit.providers import Backend
from qiskit_aer import AerSimulator

from quartumse import __version__
from quartumse.connectors import (
    SamplerPrimitive,
    create_backend_snapshot,
    create_runtime_sampler,
    is_ibm_runtime_backend,
    resolve_backend,
)
from quartumse.estimator.base import EstimationResult, Estimator
from quartumse.mitigation import MeasurementErrorMitigation
from quartumse.reporting.manifest import (
    BackendSnapshot,
    CircuitFingerprint,
    ManifestSchema,
    MitigationConfig,
    ProvenanceManifest,
    ResourceUsage,
    ShadowsConfig,
    compute_file_checksum,
)
from quartumse.reporting.shot_data import ShotDataWriter
from quartumse.shadows.config import ShadowConfig, ShadowVersion
from quartumse.shadows.core import ClassicalShadows, Observable
from quartumse.shadows.v0_baseline import RandomLocalCliffordShadows
from quartumse.shadows.v1_noise_aware import NoiseAwareRandomLocalCliffordShadows

LOGGER = logging.getLogger(__name__)


class ShadowEstimator(Estimator):
    """
    Observable estimator using classical shadows.

    Automatically selects shadow version based on config and orchestrates:
    1. Shadow measurement generation
    2. Circuit execution
    3. Shadow reconstruction
    4. Observable estimation
    5. Provenance tracking
    """

    def __init__(
        self,
        backend: Backend | str,
        shadow_config: ShadowConfig | None = None,
        mitigation_config: MitigationConfig | None = None,
        data_dir: str | Path | None = None,
    ):
        """
        Initialize shadow estimator.

        Args:
            backend: Qiskit backend or backend name (e.g., "aer_simulator")
            shadow_config: Classical shadows configuration
            mitigation_config: Error mitigation configuration
            data_dir: Directory for storing shot data and manifests
        """
        # Handle backend
        self._backend_descriptor: str | None = None
        self._backend_snapshot: BackendSnapshot | None = None

        if isinstance(backend, str):
            self._backend_descriptor = backend
            if ":" in backend:
                resolved_backend, snapshot = resolve_backend(backend)
                backend = resolved_backend
                self._backend_snapshot = snapshot
            elif backend == "aer_simulator":
                backend = AerSimulator()
                self._backend_snapshot = create_backend_snapshot(backend)
            else:
                raise ValueError(f"Unknown backend string: {backend}")
        else:
            self._backend_descriptor = getattr(backend, "name", None)

        super().__init__(backend, shadow_config)

        self._runtime_sampler: SamplerPrimitive | None = None
        self._runtime_sampler_checked = False
        self._use_runtime_sampler = is_ibm_runtime_backend(self.backend)

        self.shadow_config = shadow_config or ShadowConfig.model_validate({})
        self.mitigation_config = mitigation_config or MitigationConfig()
        self.data_dir = Path(data_dir) if data_dir else Path("./data")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.measurement_error_mitigation: MeasurementErrorMitigation | None = None
        self._mem_required = (
            self.shadow_config.version == ShadowVersion.V1_NOISE_AWARE
            or self.shadow_config.apply_inverse_channel
            or ("MEM" in self.mitigation_config.techniques)
        )
        if self._mem_required:
            self.measurement_error_mitigation = MeasurementErrorMitigation(self.backend)

        # Initialize shadow implementation based on version
        self.shadow_impl: ClassicalShadows = self._create_shadow_implementation()

        # Initialize shot data writer
        self.shot_data_writer = ShotDataWriter(self.data_dir)

    def _get_runtime_sampler(self) -> SamplerPrimitive | None:
        """Initialise (if necessary) and return the IBM Runtime sampler."""

        if not self._use_runtime_sampler:
            return None

        if not self._runtime_sampler_checked:
            self._runtime_sampler = create_runtime_sampler(self.backend)
            self._runtime_sampler_checked = True

        return self._runtime_sampler

    def _create_shadow_implementation(self) -> ClassicalShadows:
        """Factory for shadow implementations."""
        version = self.shadow_config.version

        if version == ShadowVersion.V0_BASELINE:
            return RandomLocalCliffordShadows(self.shadow_config)
        elif version == ShadowVersion.V1_NOISE_AWARE:
            if self.measurement_error_mitigation is None:
                self.measurement_error_mitigation = MeasurementErrorMitigation(self.backend)
            return NoiseAwareRandomLocalCliffordShadows(
                self.shadow_config, self.measurement_error_mitigation
            )
        elif version == ShadowVersion.V2_FERMIONIC:
            # TODO: Implement v2
            raise NotImplementedError("Shadows v2 (fermionic) not yet implemented")
        elif version == ShadowVersion.V3_ADAPTIVE:
            # TODO: Implement adaptive shadows
            raise NotImplementedError("Adaptive shadows not yet implemented")
        elif version == ShadowVersion.V4_ROBUST:
            # TODO: Implement v4
            raise NotImplementedError("Shadows v4 (robust) not yet implemented")
        else:
            raise ValueError(f"Unknown shadow version: {version}")

    def estimate(
        self,
        circuit: QuantumCircuit,
        observables: list[Observable],
        target_precision: float | None = None,
        save_manifest: bool = True,
    ) -> EstimationResult:
        """
        Estimate observables using classical shadows.

        Workflow:
        1. Generate shadow measurement circuits
        2. Transpile and execute on backend
        3. Reconstruct shadow snapshots
        4. Estimate all observables
        5. Generate provenance manifest
        """
        experiment_id = str(uuid.uuid4())
        start_time = time.time()

        # Determine shadow size
        if target_precision:
            required_sizes = [
                self.shadow_impl.estimate_shadow_size_needed(obs, target_precision)
                for obs in observables
            ]
            shadow_size = max(required_sizes) if required_sizes else self.shadow_config.shadow_size
            if shadow_size <= 0:
                raise ValueError("Shadow size estimation produced a non-positive value")
            self.shadow_config.shadow_size = shadow_size
            self.shadow_impl.config.shadow_size = shadow_size
        else:
            shadow_size = self.shadow_config.shadow_size
            self.shadow_impl.config.shadow_size = shadow_size

        # Generate shadow measurement circuits
        shadow_circuits = self.shadow_impl.generate_measurement_circuits(circuit, shadow_size)

        # Calibrate measurement error mitigation if required
        if isinstance(self.shadow_impl, NoiseAwareRandomLocalCliffordShadows):
            mem_params = self.mitigation_config.parameters
            mem_shots = int(mem_params.get("mem_shots", 4096))
            mem_qubits_param = mem_params.get("mem_qubits")
            if mem_qubits_param is None:
                mem_qubits = list(range(circuit.num_qubits))
            elif isinstance(mem_qubits_param, (list, tuple)):
                mem_qubits = [int(q) for q in mem_qubits_param]
            else:
                mem_qubits = [int(mem_qubits_param)]

            mem_force = bool(mem_params.get("mem_force_calibration", False))
            run_options = mem_params.get("mem_run_options", {})
            mem_confusion_path_str = self.mitigation_config.confusion_matrix_path

            if mem_confusion_path_str and not mem_force:
                try:
                    self.shadow_impl.mem.load_confusion_matrix(mem_confusion_path_str)
                    metadata = self.shadow_impl.mem.get_confusion_metadata()
                    if isinstance(metadata.get("shots_per_state"), (int, float)):
                        mem_shots = int(metadata["shots_per_state"])
                        mem_params["mem_shots"] = mem_shots
                    if isinstance(metadata.get("qubits"), (list, tuple)):
                        mem_qubits = [int(q) for q in metadata["qubits"]]
                        mem_params["mem_qubits"] = mem_qubits
                except FileNotFoundError:
                    LOGGER.warning(
                        "Configured confusion matrix %s not found; recalibrating.",
                        mem_confusion_path_str,
                    )
                    mem_confusion_path_str = None

            if (
                self.shadow_impl.mem.confusion_matrix is None
                or mem_force
                or not mem_confusion_path_str
            ):
                mem_dir = self.data_dir / "mem"
                mem_dir.mkdir(parents=True, exist_ok=True)
                confusion_matrix_path = mem_dir / f"{experiment_id}.npz"
                saved_confusion_path = self.shadow_impl.mem.calibrate(
                    mem_qubits,
                    shots=mem_shots,
                    run_options=run_options,
                    output_path=confusion_matrix_path,
                )
                mem_confusion_path = (
                    saved_confusion_path
                    if saved_confusion_path is not None
                    else confusion_matrix_path
                )
                self.mitigation_config.confusion_matrix_path = str(mem_confusion_path.resolve())
                mem_confusion_path_str = self.mitigation_config.confusion_matrix_path
                self.shadow_impl.mem.confusion_matrix_path = Path(mem_confusion_path_str)
            else:
                self.mitigation_config.confusion_matrix_path = mem_confusion_path_str

            if "MEM" not in self.mitigation_config.techniques:
                self.mitigation_config.techniques.append("MEM")
            mem_params["mem_qubits"] = mem_qubits
            mem_params["mem_shots"] = mem_shots

        # Transpile for backend
        transpiled_circuits = transpile(shadow_circuits, backend=self.backend)

        # Respect backend batching limits
        max_experiments = None
        backend_config = None
        if hasattr(self.backend, "configuration"):
            try:
                backend_config = self.backend.configuration()
            except Exception:
                backend_config = None

        if backend_config is not None:
            max_experiments = getattr(backend_config, "max_experiments", None)

        if isinstance(max_experiments, np.integer):
            max_experiments = int(max_experiments)

        if not isinstance(max_experiments, int) or max_experiments <= 0:
            # Use safe default batch size for IBM backends to avoid submission failures
            max_experiments = 500
            print(
                f"Warning: Backend max_experiments unavailable or invalid. "
                f"Using safe default batch size: {max_experiments}"
            )

        measurement_outcomes_list: list[np.ndarray] = []

        sampler = self._get_runtime_sampler()

        for start_idx in range(0, len(transpiled_circuits), max_experiments):
            circuit_batch = transpiled_circuits[start_idx : start_idx + max_experiments]
            if sampler is not None:
                job = sampler.run(list(circuit_batch), shots=1)
                result = job.result()

                for batch_idx, _ in enumerate(circuit_batch):
                    counts = result[batch_idx].data.meas.get_counts()
                    bitstring = list(counts.keys())[0].replace(" ", "")
                    outcomes = np.array([int(b) for b in bitstring[::-1]], dtype=int)
                    measurement_outcomes_list.append(outcomes)
            else:
                job = self.backend.run(circuit_batch, shots=1)  # Each circuit is one shadow
                result = job.result()

                for batch_idx, _ in enumerate(circuit_batch):
                    counts = result.get_counts(batch_idx)
                    bitstring = list(counts.keys())[0].replace(" ", "")
                    outcomes = np.array([int(b) for b in bitstring[::-1]], dtype=int)
                    measurement_outcomes_list.append(outcomes)

        if len(measurement_outcomes_list) != shadow_size:
            raise RuntimeError(
                "Collected measurement outcomes do not match the requested shadow size."
            )

        measurement_outcomes = np.asarray(measurement_outcomes_list, dtype=int)

        measurement_bases = self.shadow_impl.measurement_bases
        if measurement_bases is None:
            raise ValueError("Shadow implementation did not record measurement bases.")
        measurement_bases = np.asarray(measurement_bases, dtype=int)
        self.shadow_impl.measurement_bases = measurement_bases

        # Save shot data to Parquet
        shot_data_path = self.shot_data_writer.save_shadow_measurements(
            experiment_id=experiment_id,
            measurement_bases=measurement_bases,
            measurement_outcomes=measurement_outcomes,
            num_qubits=circuit.num_qubits,
        )

        # Reconstruct shadows
        self.shadow_impl.reconstruct_classical_shadow(measurement_outcomes, measurement_bases)

        # Estimate all observables
        estimates: dict[str, dict[str, object]] = {}
        for obs in observables:
            estimate = self.shadow_impl.estimate_observable(obs)
            estimates[str(obs)] = {
                "expectation_value": estimate.expectation_value,
                "variance": estimate.variance,
                "ci_95": estimate.confidence_interval,
                "ci_width": estimate.ci_width,
            }

        execution_time = time.time() - start_time

        # Create provenance manifest
        if save_manifest:
            manifest = self._create_manifest(
                experiment_id,
                circuit,
                observables,
                estimates,
                shadow_size,
                execution_time,
                shot_data_path,
            )
            manifest_path = self.data_dir / "manifests" / f"{experiment_id}.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest.to_json(manifest_path)
        else:
            manifest_path = None

        return EstimationResult(
            observables=estimates,
            shots_used=shadow_size,
            execution_time=execution_time,
            backend_name=self.backend.name,
            experiment_id=experiment_id,
            manifest_path=str(manifest_path) if manifest_path else None,
            shot_data_path=str(shot_data_path),
            mitigation_confusion_matrix_path=self.mitigation_config.confusion_matrix_path,
        )

    def estimate_shots_needed(self, observables: list[Observable], target_precision: float) -> int:
        """Estimate shadow size needed for target precision."""
        # Use worst-case observable
        max_shadow_size = 0
        for obs in observables:
            size = self.shadow_impl.estimate_shadow_size_needed(obs, target_precision)
            max_shadow_size = max(max_shadow_size, size)

        return max_shadow_size

    def replay_from_manifest(
        self,
        manifest_path: str | Path,
        observables: list[Observable] | None = None,
    ) -> EstimationResult:
        """
        Replay an experiment from a saved manifest and shot data.

        This allows re-estimation of observables from previously collected shot data
        without re-executing circuits on the backend.

        Args:
            manifest_path: Path to the provenance manifest JSON file
            observables: Optional new list of observables to estimate. If None,
                        uses observables from the original manifest.

        Returns:
            EstimationResult with re-estimated observables
        """
        manifest_path = Path(manifest_path)
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        # Load manifest
        manifest = ProvenanceManifest.from_json(manifest_path)
        experiment_id = manifest.schema.experiment_id

        # Load shot data
        measurement_bases, measurement_outcomes, num_qubits = (
            self.shot_data_writer.load_shadow_measurements(experiment_id)
        )

        if manifest.schema.shadows is None:
            raise ValueError(
                "Manifest does not contain classical shadows configuration information."
            )

        # Reconstruct shadows with loaded data
        # Create temporary shadow implementation if needed
        shadow_payload = manifest.schema.shadows.model_dump()
        shadow_payload["random_seed"] = manifest.schema.random_seed
        shadow_config = ShadowConfig.model_validate(shadow_payload)

        resolved_confusion_matrix_path: str | None = (
            manifest.schema.mitigation.confusion_matrix_path
        )

        if shadow_config.version == ShadowVersion.V0_BASELINE:
            shadow_impl = RandomLocalCliffordShadows(shadow_config)
        elif shadow_config.version == ShadowVersion.V1_NOISE_AWARE:
            confusion_matrix_path_str = manifest.schema.mitigation.confusion_matrix_path

            if not confusion_matrix_path_str:
                raise FileNotFoundError(
                    "Noise-aware manifest does not include a persisted confusion matrix path. "
                    "Re-run estimation or provide the saved calibration artifact before replaying."
                )

            raw_confusion_path = Path(confusion_matrix_path_str)
            candidate_paths = [raw_confusion_path]

            if not raw_confusion_path.is_absolute():
                candidate_paths.append((manifest_path.parent / raw_confusion_path).resolve())
                candidate_paths.append((self.data_dir / raw_confusion_path).resolve())

            candidate_paths.append((self.data_dir / "mem" / raw_confusion_path.name).resolve())
            candidate_paths.append(
                (manifest_path.parent / "mem" / raw_confusion_path.name).resolve()
            )

            confusion_matrix_path: Path | None = None
            for candidate in candidate_paths:
                if candidate and candidate.exists():
                    confusion_matrix_path = candidate
                    break

            if confusion_matrix_path is None:
                raise FileNotFoundError(
                    "Unable to locate the persisted confusion matrix required for noise-aware replay. "
                    f"Looked for {raw_confusion_path} and related paths."
                )

            with np.load(confusion_matrix_path, allow_pickle=False) as archive:
                if "confusion_matrix" not in archive:
                    raise ValueError(
                        "Confusion matrix archive is missing the 'confusion_matrix' dataset."
                    )
                confusion_matrix = archive["confusion_matrix"]

            mem = MeasurementErrorMitigation(self.backend)
            mem.confusion_matrix = confusion_matrix
            mem.confusion_matrix_path = confusion_matrix_path.resolve()
            mem._calibrated_qubits = tuple(range(num_qubits))

            shadow_impl = NoiseAwareRandomLocalCliffordShadows(shadow_config, mem)
            resolved_confusion_matrix_path = str(confusion_matrix_path.resolve())
        else:
            raise NotImplementedError(
                f"Replay for shadow version {shadow_config.version.value} is not implemented"
            )
        shadow_impl.measurement_bases = measurement_bases
        shadow_impl.reconstruct_classical_shadow(measurement_outcomes, measurement_bases)

        # Use observables from manifest if not provided
        if observables is None:
            observables = [
                Observable(obs_dict["pauli"], obs_dict.get("coefficient", 1.0))
                for obs_dict in manifest.schema.observables
            ]

        # Estimate all observables
        estimates: dict[str, dict[str, object]] = {}
        for obs in observables:
            estimate = shadow_impl.estimate_observable(obs)
            estimates[str(obs)] = {
                "expectation_value": estimate.expectation_value,
                "variance": estimate.variance,
                "ci_95": estimate.confidence_interval,
                "ci_width": estimate.ci_width,
            }

        return EstimationResult(
            observables=estimates,
            shots_used=manifest.schema.shadows.shadow_size,
            execution_time=0.0,  # No execution time for replay
            backend_name=manifest.schema.backend.backend_name,
            experiment_id=experiment_id,
            manifest_path=str(manifest_path),
            shot_data_path=manifest.schema.shot_data_path,
            mitigation_confusion_matrix_path=resolved_confusion_matrix_path,
        )

    def _create_manifest(
        self,
        experiment_id: str,
        circuit: QuantumCircuit,
        observables: list[Observable],
        estimates: dict[str, dict[str, object]],
        shadow_size: int,
        execution_time: float,
        shot_data_path: Path,
    ) -> ProvenanceManifest:
        """Create provenance manifest for the experiment."""
        import sys

        import qiskit

        # Circuit fingerprint
        try:
            qasm_str = qasm3.dumps(circuit)
        except Exception:
            qasm_str = circuit.qasm()

        gate_counts: dict[str, int] = {}
        for instruction in circuit.data:
            gate_name = instruction.operation.name
            gate_counts[gate_name] = gate_counts.get(gate_name, 0) + 1

        circuit_hash = hashlib.sha256(qasm_str.encode()).hexdigest()[:16]

        circuit_fp = CircuitFingerprint(
            qasm3=qasm_str,
            num_qubits=circuit.num_qubits,
            depth=circuit.depth(),
            gate_counts=gate_counts,
            circuit_hash=circuit_hash,
        )

        # Backend snapshot
        backend_snapshot = self._backend_snapshot or create_backend_snapshot(self.backend)

        # Shadows config
        shadows_config = ShadowsConfig.model_validate(
            {
                "version": self.shadow_config.version.value,
                "shadow_size": shadow_size,
                "measurement_ensemble": self.shadow_config.measurement_ensemble.value,
                "noise_model_path": self.shadow_config.noise_model_path,
                "inverse_channel_applied": self.shadow_config.apply_inverse_channel,
                "fermionic_mode": self.shadow_config.fermionic_mode,
                "rdm_order": self.shadow_config.rdm_order,
                "adaptive": self.shadow_config.adaptive,
                "target_observables": self.shadow_config.target_observables,
                "bayesian_inference": self.shadow_config.bayesian_inference,
                "bootstrap_samples": self.shadow_config.bootstrap_samples,
            }
        )

        # Resource usage
        resource_usage = ResourceUsage.model_validate(
            {
                "total_shots": shadow_size,
                "execution_time_seconds": execution_time,
                "queue_time_seconds": None,
                "estimated_cost_usd": None,
                "credits_used": None,
                "classical_compute_seconds": None,
            }
        )

        metadata = {}
        if self._backend_descriptor:
            metadata["backend_descriptor"] = self._backend_descriptor

        # Create manifest
        shot_checksum = compute_file_checksum(shot_data_path)

        mitigation_config = self.mitigation_config.model_copy(deep=True)
        confusion_path = mitigation_config.confusion_matrix_path
        if confusion_path:
            mitigation_config.confusion_matrix_checksum = compute_file_checksum(confusion_path)

        manifest_schema = ManifestSchema(
            experiment_id=experiment_id,
            experiment_name=None,
            circuit=circuit_fp,
            observables=[
                {"pauli": obs.pauli_string, "coefficient": obs.coefficient} for obs in observables
            ],
            backend=backend_snapshot,
            mitigation=mitigation_config,
            shadows=shadows_config,
            shot_data_path=str(shot_data_path),
            shot_data_checksum=shot_checksum,
            results_summary=estimates,
            resource_usage=resource_usage,
            metadata=metadata,
            random_seed=self.shadow_config.random_seed,
            quartumse_version=__version__,
            qiskit_version=qiskit.__version__,
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        )

        return ProvenanceManifest(manifest_schema)
