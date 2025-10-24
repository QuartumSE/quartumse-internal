"""
Common utilities for QuartumSE IBM experiments.
Requires QuartumSE package with:
- ShadowEstimator
- ShadowConfig, ShadowVersion
- Observable
- MitigationConfig
- resolve_backend
"""

import os
import time
import json
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from quartumse import ShadowEstimator
from quartumse.shadows import ShadowConfig
from quartumse.shadows.config import ShadowVersion
from quartumse.shadows.core import Observable
from quartumse.reporting.manifest import MitigationConfig
from quartumse.reporting.reference_registry import ReferenceDatasetRegistry
from quartumse.connectors import (
    resolve_backend,
    is_ibm_runtime_backend,
    create_runtime_sampler,
    create_backend_snapshot,
)
from quartumse.mitigation import ReadoutCalibrationManager
from quartumse.utils.metrics import (
    MetricsSummary,
    build_observable_comparison,
    summarise_observable_comparisons,
)


_CALIBRATION_MANAGER = ReadoutCalibrationManager()

# ---------- Generic helpers ----------

def allocate_shots(total_shots: int, n: int) -> List[int]:
    base = total_shots // n
    rem = total_shots % n
    return [base + (1 if i < rem else 0) for i in range(n)]


def load_budgeting_summary(
    runtime_payload: Dict[str, Any],
    experiments: List[str],
    *,
    log_fn: Optional[Any] = None,
) -> Dict[str, Any]:
    """Normalise CLI budgeting hints and derive per-experiment shot envelopes.

    Args:
        runtime_payload: Parsed JSON from ``quartumse runtime-status --json``.
        experiments: Ordered list of experiment labels to allocate measurement shots across.
        log_fn: Optional callable (e.g., ``logger.info``) used to emit a shared
            budgeting summary. When omitted, the summary is not logged.

    Returns:
        Dictionary containing measurement and calibration shot counts as well as
        the per-experiment allocation map.
    """

    budgeting = runtime_payload.get("budgeting")
    if not isinstance(budgeting, dict):
        raise ValueError("Runtime payload is missing 'budgeting' hints; rerun the CLI with budgeting support enabled")

    shot_capacity = budgeting.get("shot_capacity") or {}
    measurement_shots = shot_capacity.get("measurement_shots_available")
    if measurement_shots is None:
        raise ValueError("Budgeting payload does not include 'measurement_shots_available'")

    calibration_shots = shot_capacity.get("calibration_shots") or 0
    total_measurement_shots = int(measurement_shots)
    total_calibration_shots = int(calibration_shots)
    total_batch_shots = total_measurement_shots + total_calibration_shots

    allocation: Dict[str, int] = {}
    if experiments:
        shot_splits = allocate_shots(total_measurement_shots, len(experiments))
        allocation = {name: shots for name, shots in zip(experiments, shot_splits)}

    summary = {
        "backend": runtime_payload.get("queue", {}).get("backend_name"),
        "collected_at": runtime_payload.get("collected_at"),
        "total_measurement_shots": total_measurement_shots,
        "total_calibration_shots": total_calibration_shots,
        "total_batch_shots": total_batch_shots,
        "measurement_shots_per_experiment": allocation,
        "assumptions": budgeting.get("assumptions", {}),
        "timing": budgeting.get("timing", {}),
        "fallbacks": budgeting.get("fallbacks", []),
    }

    if log_fn is not None:
        lines = [
            "Runtime budgeting summary:",
            f"  Backend: {summary['backend']} (captured {summary['collected_at']})",
            f"  Measurement shots available: {total_measurement_shots}",
            f"  Calibration shots reserved: {total_calibration_shots}",
        ]

        usable_seconds = summary["timing"].get("usable_batch_seconds") if isinstance(summary["timing"], dict) else None
        if usable_seconds is not None:
            lines.append(f"  Usable batch seconds: {usable_seconds}")

        if allocation:
            lines.append("  Shots per experiment:")
            for name, shots in allocation.items():
                lines.append(f"    - {name}: {shots}")

        fallbacks = summary.get("fallbacks")
        if fallbacks:
            lines.append("  Fallback hints:")
            for item in fallbacks:
                condition = item.get("condition")
                action = item.get("action")
                lines.append(f"    - {condition}: {action}")

        for line in lines:
            log_fn(line)

    return summary

def run_baseline_direct(circuits: List[Tuple[str, QuantumCircuit, List[Observable]]],
                        backend,
                        shots_per_circuit: List[int]) -> Dict[str, Dict]:
    """
    Run direct measurement circuits. Each entry contains (label, circuit, obs_list) where
    circuit already includes measurement in the appropriate basis for those observables.
    """
    results = {}
    sampler = None
    if is_ibm_runtime_backend(backend):
        sampler = create_runtime_sampler(backend)

    for (label, qc, obs_list), shots in zip(circuits, shots_per_circuit):
        tqc = transpile(qc, backend)

        if sampler is not None:
            job = sampler.run([tqc], shots=shots)
            result = job.result()
            counts = result[0].data.meas.get_counts()
        else:
            job = backend.run(tqc, shots=shots)
            result = job.result()
            counts = result.get_counts()

        # Compute expectations for the obs_list
        for obs in obs_list:
            exp = estimate_expectation_from_counts(counts, obs, shots)
            results[str(obs)] = {
                "expectation": float(exp),
                "shots": int(shots),
            }
    return results

def estimate_expectation_from_counts(counts, obs: Observable, shots: int) -> float:
    # Expectation of tensor product of Z and I after basis rotations already applied.
    total = 0.0
    for bitstring, ct in counts.items():
        p = ct / shots
        parity = 1.0
        for q, pchar in enumerate(obs.pauli_string):
            if pchar != "I":
                bit = int(bitstring[-(q+1)])
                parity *= (1 - 2*bit)
        total += p * parity
    return obs.coefficient * total

def run_shadows(
    circuit: QuantumCircuit,
    observables: List[Observable],
    backend_descriptor: str,
    variant: str,
    shadow_size: int,
    mem_shots: int = 512,
    data_dir: str = "./validation_data",
    *,
    calibration_max_age_hours: Optional[float] = None,
    force_new_calibration: bool = False,
    reference_slug: Optional[str] = None,
    reference_tags: Optional[List[str]] = None,
    reference_metadata: Optional[Dict[str, Any]] = None,
    allow_reuse: bool = True,
) -> Tuple[Dict, Dict]:
    use_mem = (variant.lower() == "v1")

    shadow_config = ShadowConfig(
        version=ShadowVersion.V1_NOISE_AWARE if use_mem else ShadowVersion.V0_BASELINE,
        shadow_size=shadow_size,
        random_seed=42,
        apply_inverse_channel=use_mem,
    )
    mitigation_config = None

    if backend_descriptor == "aer_simulator":
        backend = AerSimulator()
        backend_snapshot = create_backend_snapshot(backend)
    else:
        backend, backend_snapshot = resolve_backend(backend_descriptor)

    registry = ReferenceDatasetRegistry(data_dir) if reference_slug else None
    dataset_manifest: Optional[Path] = None
    manifest_obj = None
    dataset_meta: Dict[str, Any] = {}
    reference_reused = False

    calibration_shots = 0
    calibration_manifest_path: Optional[Path] = None
    calibration_confusion_path: Optional[Path] = None
    calibration_reused = False
    calibration_created_at: Optional[str] = None

    if registry and reference_slug and allow_reuse:
        existing_manifest = registry.lookup(reference_slug)
        if existing_manifest and existing_manifest.exists():
            estimator = ShadowEstimator(
                backend=backend,
                shadow_config=shadow_config,
                mitigation_config=mitigation_config,
                data_dir=data_dir,
            )
            if backend_snapshot is not None:
                estimator._backend_snapshot = backend_snapshot
            res = estimator.replay_from_manifest(existing_manifest, observables=observables)
            reference_reused = True
            dataset_manifest = existing_manifest
            manifest_obj = registry.load_manifest(existing_manifest)
            dataset_meta = manifest_obj.schema.metadata.get("reference_dataset", {}) if manifest_obj else {}
            calibration_shots = int(dataset_meta.get("calibration_shots", 0) or 0)
            registry.mark_used(reference_slug, existing_manifest)
        else:
            res = None
    else:
        res = None

    if not reference_reused and use_mem:
        base_config = MitigationConfig()
        max_age = (
            timedelta(hours=calibration_max_age_hours)
            if calibration_max_age_hours is not None
            else None
        )
        calibration_record = _CALIBRATION_MANAGER.ensure_calibration(
            backend,
            qubits=list(range(circuit.num_qubits)),
            shots=mem_shots,
            max_age=max_age,
            force=force_new_calibration,
        )
        mitigation_config = calibration_record.to_mitigation_config(base_config)
        mitigation_config.parameters["mem_shots"] = calibration_record.shots_per_state
        mitigation_config.parameters["mem_qubits"] = list(calibration_record.qubits)
        calibration_confusion_path = calibration_record.path
        calibration_manifest_path = calibration_confusion_path.with_suffix(".manifest.json")
        calibration_reused = calibration_record.reused
        calibration_created_at = calibration_record.created_at.isoformat()
        if not calibration_record.reused:
            calibration_shots = calibration_record.total_shots
        else:
            calibration_shots = 0

    total_shots = shadow_size + calibration_shots

    if not reference_reused:
        estimator = ShadowEstimator(
            backend=backend,
            shadow_config=shadow_config,
            mitigation_config=mitigation_config,
            data_dir=data_dir
        )
        if backend_snapshot is not None:
            estimator._backend_snapshot = backend_snapshot
        start = time.time()
        res = estimator.estimate(circuit=circuit, observables=observables, save_manifest=True)
        elapsed = time.time() - start
        dataset_manifest = Path(res.manifest_path) if getattr(res, "manifest_path", None) else None
        dataset_meta = manifest_obj.schema.metadata.get("reference_dataset", {}) if manifest_obj else {}
    else:
        elapsed = 0.0

    if res is None:
        raise RuntimeError("Shadow estimation failed to produce a result")

    if reference_reused and manifest_obj is None and dataset_manifest is not None:
        # Ensure manifest object is loaded for metadata if it wasn't already
        manifest_obj = registry.load_manifest(dataset_manifest) if registry else None
        dataset_meta = manifest_obj.schema.metadata.get("reference_dataset", {}) if manifest_obj else {}

    out = {}
    for obs_str, data in res.observables.items():
        exp = data.get("expectation_value")
        ci = data.get("ci_95") or data.get("confidence_interval")
        ci_width = data.get("ci_width")
        out[obs_str] = {
            "expectation": float(exp),
            "ci": ci,
            "ci_width": float(ci_width) if ci_width is not None else None
        }

    measurement_shots = int(res.shots_used)
    total_shots = measurement_shots + int(calibration_shots)

    manifest_path_str = getattr(res, "manifest_path", None)
    if reference_reused and dataset_manifest is not None:
        manifest_path_str = str(dataset_manifest)

    shot_data_path = getattr(res, "shot_data_path", None)
    if reference_reused and manifest_obj is not None:
        shot_data_path = manifest_obj.schema.shot_data_path

    meta = {
        "backend_name": (
            manifest_obj.schema.backend.backend_name
            if manifest_obj is not None
            else backend.name if hasattr(backend, "name") else backend_descriptor
        ),
        "experiment_id": getattr(res, "experiment_id", None),
        "manifest_path": manifest_path_str,
        "shot_data_path": shot_data_path,
        "measurement_shots": measurement_shots,
        "calibration_shots": int(calibration_shots),
        "total_shots": int(total_shots),
        "elapsed_sec": float(elapsed),
        "reference_slug": reference_slug,
        "reference_reused": reference_reused,
    }
    if use_mem and calibration_confusion_path is not None:
        meta.update(
            {
                "calibration_confusion_matrix": str(calibration_confusion_path),
                "calibration_manifest": str(calibration_manifest_path) if calibration_manifest_path else None,
                "calibration_reused": calibration_reused,
                "calibration_created_at": calibration_created_at,
            }
        )
    elif use_mem and dataset_meta:
        meta.update(
            {
                "calibration_confusion_matrix": dataset_meta.get("calibration_confusion_matrix"),
                "calibration_manifest": dataset_meta.get("calibration_manifest"),
                "calibration_reused": dataset_meta.get("calibration_reused", False),
                "calibration_created_at": dataset_meta.get("calibration_created_at"),
            }
        )

    if registry and reference_slug and dataset_manifest and not reference_reused:
        tags = list(reference_tags or [])
        if not tags:
            tags = [variant]
        metadata_payload = {
            "variant": variant,
            "backend_descriptor": backend_descriptor,
            "shadow_size": shadow_size,
            "num_qubits": circuit.num_qubits,
            "observable_count": len(observables),
        }
        if reference_metadata:
            metadata_payload.update(reference_metadata)
        if use_mem:
            metadata_payload.update(
                {
                    "calibration_confusion_matrix": str(calibration_confusion_path) if calibration_confusion_path else None,
                    "calibration_manifest": str(calibration_manifest_path) if calibration_manifest_path else None,
                    "calibration_reused": calibration_reused,
                    "calibration_created_at": calibration_created_at,
                }
            )
        manifest_obj = registry.register_reference(
            reference_slug,
            dataset_manifest,
            tags=tags,
            metadata=metadata_payload,
            calibration_shots=calibration_shots,
        )
        dataset_meta = manifest_obj.schema.metadata.get("reference_dataset", {})

    if dataset_meta:
        meta["reference_dataset"] = dataset_meta
        meta.setdefault("reference_tags", dataset_meta.get("tags"))

    return out, meta

def compute_metrics(
    observables: List[Observable],
    baseline: Dict[str, Dict],
    approach: Dict[str, Dict],
    baseline_total_shots: int,
    approach_total_shots: int,
) -> MetricsSummary:
    """Compute SSR, variance reduction and CI coverage for an experiment run."""

    comparisons = []
    for obs in observables:
        key = str(obs)
        baseline_payload = baseline.get(key, {})
        approach_payload = approach.get(key, {})

        comparison = build_observable_comparison(
            key,
            baseline_payload,
            approach_payload,
            baseline_total_shots=baseline_total_shots,
            approach_total_shots=approach_total_shots,
        )
        comparisons.append(comparison)

    return summarise_observable_comparisons(comparisons)
