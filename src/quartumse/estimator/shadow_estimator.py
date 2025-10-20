"""Shadow-based estimator implementation."""

import hashlib
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from qiskit import QuantumCircuit, qasm3, transpile
from qiskit.providers import Backend
from qiskit_aer import AerSimulator

from quartumse import __version__
from quartumse.estimator.base import Estimator, EstimationResult
from quartumse.reporting.manifest import (
    BackendSnapshot,
    CircuitFingerprint,
    ManifestSchema,
    MitigationConfig,
    ProvenanceManifest,
    ResourceUsage,
    ShadowsConfig,
)
from quartumse.reporting.shot_data import ShotDataWriter
from quartumse.shadows.config import ShadowConfig, ShadowVersion
from quartumse.shadows.core import Observable
from quartumse.shadows.v0_baseline import RandomLocalCliffordShadows


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
        backend: Union[Backend, str],
        shadow_config: Optional[ShadowConfig] = None,
        mitigation_config: Optional[MitigationConfig] = None,
        data_dir: Optional[Union[str, Path]] = None,
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
        if isinstance(backend, str):
            if backend == "aer_simulator":
                backend = AerSimulator()
            else:
                raise ValueError(f"Unknown backend string: {backend}")

        super().__init__(backend, shadow_config)

        self.shadow_config = shadow_config or ShadowConfig()
        self.mitigation_config = mitigation_config or MitigationConfig()
        self.data_dir = Path(data_dir) if data_dir else Path("./data")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize shadow implementation based on version
        self.shadow_impl = self._create_shadow_implementation()
        
        # Initialize shot data writer
        self.shot_data_writer = ShotDataWriter(self.data_dir)

    def _create_shadow_implementation(self):
        """Factory for shadow implementations."""
        version = self.shadow_config.version

        if version == ShadowVersion.V0_BASELINE:
            return RandomLocalCliffordShadows(self.shadow_config)
        elif version == ShadowVersion.V1_NOISE_AWARE:
            # TODO: Implement v1
            raise NotImplementedError("Shadows v1 (noise-aware) not yet implemented")
        elif version == ShadowVersion.V2_FERMIONIC:
            # TODO: Implement v2
            raise NotImplementedError("Shadows v2 (fermionic) not yet implemented")
        elif version == ShadowVersion.V3_ADAPTIVE:
            # TODO: Implement v3
            raise NotImplementedError("Shadows v3 (adaptive) not yet implemented")
        elif version == ShadowVersion.V4_ROBUST:
            # TODO: Implement v4
            raise NotImplementedError("Shadows v4 (robust) not yet implemented")
        else:
            raise ValueError(f"Unknown shadow version: {version}")

    def estimate(
        self,
        circuit: QuantumCircuit,
        observables: List[Observable],
        target_precision: Optional[float] = None,
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
            # Use worst-case observable (largest support)
            max_support = max(
                sum(1 for p in obs.pauli_string if p != "I") for obs in observables
            )
            shadow_size = self.shadow_impl.estimate_shadow_size_needed(
                Observable("I" * (len(observables[0].pauli_string) - max_support) + "Z" * max_support),
                target_precision,
            )
            self.shadow_config.shadow_size = shadow_size
        else:
            shadow_size = self.shadow_config.shadow_size

        # Generate shadow measurement circuits
        shadow_circuits = self.shadow_impl.generate_measurement_circuits(circuit, shadow_size)

        # Transpile for backend
        transpiled_circuits = transpile(shadow_circuits, backend=self.backend)

        # Execute
        job = self.backend.run(transpiled_circuits, shots=1)  # Each circuit is one shadow
        result = job.result()

        # Extract measurement outcomes
        measurement_outcomes = []
        for i in range(shadow_size):
            counts = result.get_counts(i)
            # Get the single outcome (since shots=1)
            bitstring = list(counts.keys())[0]
            outcomes = np.array([int(b) for b in bitstring[::-1]])  # Reverse for qubit ordering
            measurement_outcomes.append(outcomes)

        measurement_outcomes = np.array(measurement_outcomes)

        # Save shot data to Parquet
        shot_data_path = self.shot_data_writer.save_shadow_measurements(
            experiment_id=experiment_id,
            measurement_bases=self.shadow_impl.measurement_bases,
            measurement_outcomes=measurement_outcomes,
            num_qubits=circuit.num_qubits,
        )

        # Reconstruct shadows
        self.shadow_impl.reconstruct_classical_shadow(
            measurement_outcomes, self.shadow_impl.measurement_bases
        )

        # Estimate all observables
        estimates = {}
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
            manifest_path=str(manifest_path) if manifest_path else None,
        )

    def estimate_shots_needed(
        self, observables: List[Observable], target_precision: float
    ) -> int:
        """Estimate shadow size needed for target precision."""
        # Use worst-case observable
        max_shadow_size = 0
        for obs in observables:
            size = self.shadow_impl.estimate_shadow_size_needed(obs, target_precision)
            max_shadow_size = max(max_shadow_size, size)

        return max_shadow_size


    def replay_from_manifest(
        self,
        manifest_path: Union[str, Path],
        observables: Optional[List[Observable]] = None,
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

        # Reconstruct shadows with loaded data
        # Create temporary shadow implementation if needed
        shadow_config = ShadowConfig(
            version=ShadowVersion(manifest.schema.shadows.version),
            shadow_size=manifest.schema.shadows.shadow_size,
            random_seed=manifest.schema.random_seed,
        )
        shadow_impl = RandomLocalCliffordShadows(shadow_config)
        shadow_impl.measurement_bases = measurement_bases
        shadow_impl.reconstruct_classical_shadow(measurement_outcomes, measurement_bases)

        # Use observables from manifest if not provided
        if observables is None:
            observables = [
                Observable(obs_dict["pauli"], obs_dict.get("coefficient", 1.0))
                for obs_dict in manifest.schema.observables
            ]

        # Estimate all observables
        estimates = {}
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
            manifest_path=str(manifest_path),
        )

    def _create_manifest(
        self,
        experiment_id: str,
        circuit: QuantumCircuit,
        observables: List[Observable],
        estimates: Dict,
        shadow_size: int,
        execution_time: float,
    ) -> ProvenanceManifest:
        """Create provenance manifest for the experiment."""
        import platform
        import sys

        import qiskit

        # Circuit fingerprint
        try:
            qasm_str = qasm3.dumps(circuit)
        except:
            qasm_str = circuit.qasm()

        gate_counts = {}
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
        backend_version = getattr(self.backend, "version", "unknown")
        if not isinstance(backend_version, str):
            backend_version = str(backend_version)
            
        backend_snapshot = BackendSnapshot(
            backend_name=self.backend.name,
            backend_version=backend_version,
            num_qubits=self.backend.configuration().n_qubits,
            basis_gates=self.backend.configuration().basis_gates,
            calibration_timestamp=time.time(),
            properties_hash="",  # TODO: Capture full properties
        )

        # Shadows config
        shadows_config = ShadowsConfig(
            version=self.shadow_config.version.value,
            shadow_size=shadow_size,
            measurement_ensemble=self.shadow_config.measurement_ensemble.value,
            inverse_channel_applied=self.shadow_config.apply_inverse_channel,
            adaptive=self.shadow_config.adaptive,
            bayesian_inference=self.shadow_config.bayesian_inference,
        )

        # Resource usage
        resource_usage = ResourceUsage(
            total_shots=shadow_size,
            execution_time_seconds=execution_time,
        )

        # Create manifest
        manifest_schema = ManifestSchema(
            experiment_id=experiment_id,
            circuit=circuit_fp,
            observables=[{"pauli": obs.pauli_string, "coefficient": obs.coefficient} for obs in observables],
            backend=backend_snapshot,
            mitigation=self.mitigation_config,
            shadows=shadows_config,
            shot_data_path=f"data/shots/{experiment_id}.parquet",
            results_summary=estimates,
            resource_usage=resource_usage,
            random_seed=self.shadow_config.random_seed,
            quartumse_version=__version__,
            qiskit_version=qiskit.__version__,
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        )

        return ProvenanceManifest(manifest_schema)
