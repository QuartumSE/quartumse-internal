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
from typing import Dict, List, Tuple, Optional

import numpy as np
from qiskit import QuantumCircuit, transpile

from quartumse import ShadowEstimator
from quartumse.shadows import ShadowConfig
from quartumse.shadows.config import ShadowVersion
from quartumse.shadows.core import Observable
from quartumse.reporting.manifest import MitigationConfig
from quartumse.connectors import resolve_backend, is_ibm_runtime_backend, create_runtime_sampler
from quartumse.mitigation import ReadoutCalibrationManager


_CALIBRATION_MANAGER = ReadoutCalibrationManager()

# ---------- Generic helpers ----------

def allocate_shots(total_shots: int, n: int) -> List[int]:
    base = total_shots // n
    rem = total_shots % n
    return [base + (1 if i < rem else 0) for i in range(n)]

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
) -> Tuple[Dict, Dict]:
    use_mem = (variant.lower() == "v1")

    shadow_config = ShadowConfig(
        version=ShadowVersion.V1_NOISE_AWARE if use_mem else ShadowVersion.V0_BASELINE,
        shadow_size=shadow_size,
        random_seed=42,
        apply_inverse_channel=use_mem,
    )
    mitigation_config = None

    backend, backend_snapshot = resolve_backend(backend_descriptor)

    calibration_shots = 0
    calibration_manifest_path: Optional[Path] = None
    calibration_confusion_path: Optional[Path] = None
    calibration_reused = False
    calibration_created_at: Optional[str] = None

    if use_mem:
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

    meta = {
        "backend_name": estimator.backend.name,
        "experiment_id": getattr(res, "experiment_id", None),
        "manifest_path": getattr(res, "manifest_path", None),
        "shot_data_path": getattr(res, "shot_data_path", None),
        "measurement_shots": int(shadow_size),
        "calibration_shots": int(calibration_shots),
        "total_shots": int(total_shots),
        "elapsed_sec": float(elapsed),
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
    return out, meta

def compute_metrics(observables: List[Observable],
                    baseline: Dict[str, Dict],
                    approach: Dict[str, Dict],
                    baseline_total_shots: int,
                    approach_total_shots: int) -> Dict:
    # CI coverage if present
    in_ci_flags = []
    errors = []
    for obs in observables:
        key = str(obs)
        b = baseline.get(key, {})
        a = approach.get(key, {})
        exp_true = 0.0  # Placeholder unless provided by caller
        # If caller provided expected values, they can recompute MAE later
        # Here, compute relative improvement based on baseline vs approach estimates if needed
        if a.get("ci"):
            lo, hi = a["ci"]
            in_ci_flags.append(lo <= exp_true <= hi)
        # If expected is unknown here, errors list will be filled by caller.
        pass
    coverage = (np.mean(in_ci_flags) if in_ci_flags else None)
    # SSR left to caller who knows expected values
    return {"ci_coverage": coverage}
