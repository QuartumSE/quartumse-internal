"""Stage-1 executor orchestrating baseline and classical shadows runs."""

from __future__ import annotations

import hashlib
import math
import platform
import time
import uuid
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd
import qiskit
from qiskit import QuantumCircuit, qasm3
from qiskit_aer import AerSimulator

from quartumse import __version__ as QUARTUMSE_VERSION
from quartumse.connectors import create_backend_snapshot, get_linear_chain, resolve_backend
from quartumse.estimator import ShadowEstimator
from quartumse.mitigation import ReadoutCalibrationManager
from quartumse.reporting.manifest import (
    CircuitFingerprint,
    ManifestSchema,
    MitigationConfig,
    ProvenanceManifest,
    ResourceUsage,
    compute_file_checksum,
)
from quartumse.shadows import ShadowConfig
from quartumse.shadows.config import ShadowVersion
from quartumse.shadows.core import Observable

from ._observables import metadata_defined_observables
from ._runners import run_direct_pauli
from .metadata_schema import ExperimentMetadata


def _slugify(value: str) -> str:
    """Return a filesystem-safe slug for ``value``."""

    cleaned: List[str] = []
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
        elif char in {" ", "-", "_"}:
            cleaned.append("-")
    slug = "".join(cleaned).strip("-")
    return slug or "experiment"


def _infer_num_qubits(metadata: ExperimentMetadata) -> int:
    """Infer the number of qubits from calibration metadata."""

    shots_per_state = metadata.budget.calibration.shots_per_state
    calibration_total = metadata.budget.calibration.total
    if shots_per_state <= 0 or calibration_total <= 0:
        raise ValueError("Calibration budget must be positive to infer qubit count")

    states_per_qubit = calibration_total / shots_per_state
    if not states_per_qubit.is_integer():
        raise ValueError(
            "Calibration budget does not correspond to a full tensor-product basis"
        )

    log_value = math.log2(states_per_qubit)
    if not math.isclose(log_value, round(log_value)):
        raise ValueError("Calibration budget implies a non-integer qubit count")

    return int(round(log_value))


def _ghz_circuit(num_qubits: int) -> QuantumCircuit:
    """Construct an ``num_qubits``-qubit GHZ state preparation circuit."""

    circuit = QuantumCircuit(num_qubits, name=f"ghz_{num_qubits}")
    circuit.h(0)
    for index in range(num_qubits - 1):
        circuit.cx(index, index + 1)
    return circuit


def _ghz_observables(num_qubits: int) -> List[Observable]:
    """Return stabiliser observables for a GHZ state."""

    observables: List[Observable] = []
    for target in range(num_qubits):
        pauli = "".join("Z" if index == target else "I" for index in range(num_qubits))
        observables.append(Observable(pauli))

    observables.append(Observable("Z" * num_qubits))
    return observables


def _metadata_observables(metadata: ExperimentMetadata) -> List[Observable]:
    """Return additional observables requested via metadata."""

    extras = metadata_defined_observables(metadata)
    unique: Dict[str, Observable] = {}
    for observable in extras:
        pauli = observable.pauli_string
        if pauli not in unique:
            unique[pauli] = observable
    return list(unique.values())


def _circuit_fingerprint(circuit: QuantumCircuit) -> CircuitFingerprint:
    """Create a :class:`CircuitFingerprint` for ``circuit``."""

    try:
        qasm_str = qasm3.dumps(circuit)
    except Exception:  # pragma: no cover - fallback for legacy Qiskit
        qasm_str = circuit.qasm()

    gate_counts: Dict[str, int] = {}
    for instruction in circuit.data:
        name = instruction.operation.name
        gate_counts[name] = gate_counts.get(name, 0) + 1

    return CircuitFingerprint(
        qasm3=qasm_str,
        num_qubits=circuit.num_qubits,
        depth=circuit.depth(),
        gate_counts=gate_counts,
    )


def _baseline_manifest(
    *,
    experiment_id: str,
    circuit: QuantumCircuit,
    observables: Iterable[Observable],
    backend_snapshot,
    shot_path: Path,
    results: Dict[str, Dict[str, float]],
    execution_time: float,
    metadata: ExperimentMetadata,
) -> ProvenanceManifest:
    """Create a provenance manifest for the baseline run."""

    resource_usage = ResourceUsage(
        total_shots=sum(entry["shots"] for entry in results.values()),
        execution_time_seconds=execution_time,
    )

    shot_checksum = compute_file_checksum(shot_path)

    manifest_schema = ManifestSchema(
        experiment_id=experiment_id,
        experiment_name=metadata.experiment,
        circuit=_circuit_fingerprint(circuit),
        observables=[
            {"pauli": obs.pauli_string, "coefficient": obs.coefficient} for obs in observables
        ],
        backend=backend_snapshot,
        mitigation=MitigationConfig(),
        shadows=None,
        shot_data_path=str(shot_path.resolve()),
        shot_data_checksum=shot_checksum,
        results_summary=results,
        resource_usage=resource_usage,
        metadata={
            "pipeline_stage": "stage-1",
            "approach": "baseline_direct_pauli",
            "context": metadata.context,
            "device": metadata.device,
        },
        quartumse_version=QUARTUMSE_VERSION,
        qiskit_version=qiskit.__version__,
        python_version=platform.python_version(),
    )
    manifest_schema.tags = ["stage-1", "baseline"]
    return ProvenanceManifest(manifest_schema)


def _resolve_backend(descriptor: str):
    """Resolve ``descriptor`` into a backend and snapshot."""

    if descriptor == "aer_simulator":
        backend = AerSimulator()
        snapshot = create_backend_snapshot(backend)
        return backend, snapshot

    backend, snapshot = resolve_backend(descriptor)
    return backend, snapshot


def execute_experiment(
    metadata: ExperimentMetadata | Dict[str, object],
    output_dir: Path,
    backend: Optional[str] = None,
) -> Dict[str, Path]:
    """Execute Stage-1 baseline, shadows v0, and shadows v1+MEM runs."""

    if not isinstance(metadata, ExperimentMetadata):
        metadata = ExperimentMetadata.model_validate(metadata)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    backend_descriptor = backend or metadata.device
    if not backend_descriptor:
        raise ValueError("Backend descriptor must be provided via metadata or argument")

    backend_instance, backend_snapshot = _resolve_backend(backend_descriptor)

    inferred_qubits = _infer_num_qubits(metadata)
    if metadata.num_qubits is not None:
        num_qubits = metadata.num_qubits
        if num_qubits != inferred_qubits:
            raise ValueError(
                "Explicit num_qubits override does not match calibration budget inference"
            )
    else:
        num_qubits = inferred_qubits

    total_shots = metadata.budget.total_shots
    v0_shots = metadata.budget.v0_shadow_size
    v1_measurement_shots = metadata.budget.v1_shadow_size
    calibration_total = metadata.budget.calibration.total
    expected_calibration_total = metadata.budget.calibration.shots_per_state * (2**num_qubits)
    if expected_calibration_total != calibration_total:
        raise ValueError("Calibration total must match shots_per_state * 2**num_qubits")

    if v0_shots != total_shots:
        raise ValueError("v0 shadow size must match the total shot budget")
    if v1_measurement_shots + calibration_total != total_shots:
        raise ValueError("v1 measurement and calibration shots must exhaust the budget")

    chain = get_linear_chain(backend_instance, num_qubits)

    circuit = _ghz_circuit(num_qubits)
    observables = _ghz_observables(num_qubits)
    extra_observables = _metadata_observables(metadata)
    if extra_observables:
        existing = {obs.pauli_string: obs for obs in observables}
        for observable in extra_observables:
            if observable.pauli_string in existing:
                continue
            observables.append(observable)

    # Baseline direct Pauli run
    baseline_start = time.time()
    baseline_result = run_direct_pauli(
        circuit,
        observables,
        backend_instance,
        total_shots=total_shots,
    )
    baseline_elapsed = time.time() - baseline_start

    if baseline_result.get("total_shots_used") != total_shots:
        raise RuntimeError("Baseline execution did not consume the full shot budget")

    raw_results = baseline_result["results_by_obs"]
    normalized_results: Dict[str, Dict[str, float]] = {
        label: {"shots": int(data["shots"]), "expectation": float(data["expectation"])}
        for label, data in raw_results.items()
    }
    baseline_records = [
        {"observable": label, **values} for label, values in normalized_results.items()
    ]

    baseline_df = pd.DataFrame(baseline_records)
    slug = _slugify(metadata.experiment)
    baseline_parquet_path = output_dir / "baseline" / f"{slug}.parquet"
    baseline_parquet_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_df.to_parquet(baseline_parquet_path, engine="pyarrow", compression="snappy")

    baseline_experiment_id = f"{slug}-baseline-{uuid.uuid4().hex[:8]}"
    baseline_manifest = _baseline_manifest(
        experiment_id=baseline_experiment_id,
        circuit=circuit,
        observables=observables,
        backend_snapshot=backend_snapshot,
        shot_path=baseline_parquet_path,
        results=normalized_results,
        execution_time=baseline_elapsed,
        metadata=metadata,
    )
    baseline_manifest_path = output_dir / "manifests" / f"{baseline_experiment_id}.json"
    baseline_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_manifest.to_json(baseline_manifest_path)

    # Shadows v0 run
    shadow_config_v0 = ShadowConfig(
        version=ShadowVersion.V0_BASELINE,
        shadow_size=v0_shots,
        random_seed=42,
    )
    estimator_v0 = ShadowEstimator(
        backend=backend_instance,
        shadow_config=shadow_config_v0,
        data_dir=output_dir,
    )
    result_v0 = estimator_v0.estimate(circuit=circuit, observables=observables, save_manifest=True)
    manifest_v0_path = Path(result_v0.manifest_path).resolve()

    # Shadows v1 + MEM run
    calibration_manager = ReadoutCalibrationManager(base_dir=output_dir / "calibrations")
    calibration_record = calibration_manager.ensure_calibration(
        backend_instance,
        qubits=chain,
        shots=metadata.budget.calibration.shots_per_state,
    )
    mitigation_config = calibration_record.to_mitigation_config(MitigationConfig())

    shadow_config_v1 = ShadowConfig(
        version=ShadowVersion.V1_NOISE_AWARE,
        shadow_size=v1_measurement_shots,
        random_seed=7,
        apply_inverse_channel=True,
    )
    estimator_v1 = ShadowEstimator(
        backend=backend_instance,
        shadow_config=shadow_config_v1,
        mitigation_config=mitigation_config,
        data_dir=output_dir,
    )
    result_v1 = estimator_v1.estimate(circuit=circuit, observables=observables, save_manifest=True)
    manifest_v1_path = Path(result_v1.manifest_path).resolve()

    total_v1_shots = result_v1.shots_used + (
        0 if calibration_record.reused else calibration_record.total_shots
    )
    if total_v1_shots != total_shots:
        raise RuntimeError("v1 execution did not respect the total shot budget")

    # Result hash combining all manifest payloads
    digest = hashlib.sha256()
    for manifest_path in (manifest_v0_path, manifest_v1_path, baseline_manifest_path):
        digest.update(Path(manifest_path).read_bytes())
    result_hash_path = output_dir / "result_hash.txt"
    result_hash_path.write_text(digest.hexdigest())

    return {
        "manifest_v0": manifest_v0_path,
        "manifest_v1": manifest_v1_path,
        "manifest_baseline": baseline_manifest_path,
        "result_hash": result_hash_path,
    }

