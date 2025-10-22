"""
Hardware validation experiment for QuartumSE Phase 1.

The redesigned study asks: **Given a fixed 5,000-shot budget, which
workflow delivers the best accuracy on real IBM hardware?**

Circuit: GHZ-3 state
Observables: ZII, IZI, IIZ, ZZI, ZIZ, IZZ
Approaches (all constrained to 5,000 total shots):
- Baseline direct measurements (≈834/833 shots per Pauli)
- Shadows v0 (5,000 classical-shadow circuits)
- Shadows v1 + MEM (4,096 calibration + 904 classical shadows)
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
from qiskit import QuantumCircuit, transpile

from quartumse import ShadowEstimator
from quartumse.shadows import ShadowConfig
from quartumse.shadows.config import ShadowVersion
from quartumse.shadows.core import Observable
from quartumse.reporting.manifest import MitigationConfig
from quartumse.connectors import resolve_backend
from quartumse.utils.metrics import compute_ssr


def _extract_backend_name(candidate) -> Optional[str]:
    """Best-effort helper to coerce a backend-like object into a name string."""

    if candidate is None:
        return None

    if isinstance(candidate, str):
        return candidate.strip()

    direct_name = getattr(candidate, "backend_name", None)
    if isinstance(direct_name, str):
        return direct_name.strip()

    name_attr = getattr(candidate, "name", None)
    extracted_name = None
    if callable(name_attr):
        try:
            extracted_name = name_attr()
        except TypeError:
            extracted_name = None
    elif name_attr is not None:
        extracted_name = name_attr

    if isinstance(extracted_name, str):
        return extracted_name.strip()

    return None


def _extract_job_backend_name(job) -> Optional[str]:
    """Return the backend name associated with an IBM Runtime job, if available."""

    if job is None:
        return None

    backend_candidate = getattr(job, "backend", None)
    backend_obj = None
    if callable(backend_candidate):
        try:
            backend_obj = backend_candidate()
        except TypeError:
            backend_obj = None
    elif backend_candidate is not None:
        backend_obj = backend_candidate

    backend_name = _extract_backend_name(backend_obj)
    if backend_name:
        return backend_name

    direct_backend_name = getattr(job, "backend_name", None)
    if isinstance(direct_backend_name, str):
        return direct_backend_name.strip()

    return None


def create_ghz_circuit(num_qubits: int = 3) -> QuantumCircuit:
    """Create GHZ state: (|000...⟩ + |111...⟩) / √2"""
    qc = QuantumCircuit(num_qubits)
    qc.h(0)
    for i in range(num_qubits - 1):
        qc.cx(i, i + 1)
    return qc


def analytical_ghz_expectation(observable: Observable) -> float:
    """Analytical expectation value for GHZ state."""
    pauli_string = observable.pauli_string

    # Only Z-type observables are non-zero for GHZ
    if any(p not in {"I", "Z"} for p in pauli_string):
        return 0.0

    num_z = pauli_string.count("Z")
    if num_z == 0:
        return observable.coefficient
    if num_z % 2 == 0:
        return observable.coefficient
    return 0.0


def allocate_shots(total_shots: int, observables: List[Observable]) -> Dict[str, int]:
    """Evenly distribute a fixed shot budget across observables."""

    if total_shots <= 0:
        raise ValueError("Total shots must be positive")

    base = total_shots // len(observables)
    remainder = total_shots % len(observables)

    allocation: Dict[str, int] = {}
    for idx, obs in enumerate(observables):
        extra = 1 if idx < remainder else 0
        allocation[str(obs)] = base + extra

    # Sanity check
    allocated_total = sum(allocation.values())
    if allocated_total != total_shots:
        raise ValueError(
            f"Shot allocation mismatch: expected {total_shots}, got {allocated_total}"
        )

    return allocation


def run_baseline_measurement(
    circuit: QuantumCircuit,
    observables: List[Observable],
    backend,
    shot_allocation: Dict[str, int],
    *,
    expected_backend_name: Optional[str] = None,
) -> Dict[str, Dict[str, float]]:
    """Run baseline direct Pauli measurement (ground truth)."""
    print("\n" + "="*60)
    print("BASELINE: Direct Pauli Measurement")
    print("="*60)
    print("Shot allocation per observable:")
    for obs in observables:
        print(f"  {str(obs):<10} {shot_allocation[str(obs)]:>5}")
    total_shots = sum(shot_allocation.values())
    print(f"Total observables: {len(observables)}")
    print(f"Total shots: {total_shots}")
    print()

    target_backend_name = expected_backend_name or _extract_backend_name(backend)
    target_backend_normalized = (
        target_backend_name.lower().strip() if target_backend_name else None
    )

    if target_backend_name:
        print(f"Target IBM backend for baseline: {target_backend_name}")

    results: Dict[str, Dict[str, float]] = {}
    start_time = time.time()
    observed_backend_normalized: Optional[str] = None
    observed_backend_label: Optional[str] = None

    for obs in observables:
        # Create measurement circuit for this Pauli string
        measure_circuit = circuit.copy()

        # Apply basis rotations
        for qubit_idx, pauli in enumerate(obs.pauli_string):
            if pauli == "X":
                measure_circuit.h(qubit_idx)
            elif pauli == "Y":
                measure_circuit.sdg(qubit_idx)
                measure_circuit.h(qubit_idx)
            # Z basis needs no rotation

        measure_circuit.measure_all()

        shots = shot_allocation[str(obs)]

        # Transpile and execute on the resolved backend
        transpiled = transpile(measure_circuit, backend)
        job = backend.run(transpiled, shots=shots)
        job_backend_name = _extract_job_backend_name(job)
        result = job.result()
        result_backend_name = _extract_backend_name(result)
        submission_backend_name = (
            job_backend_name
            or result_backend_name
            or target_backend_name
        )

        if submission_backend_name:
            print(
                f"Submitting {str(obs):<10} on backend '{submission_backend_name}' ({shots} shots)"
            )
        else:
            print(
                f"Submitting {str(obs):<10} on backend <unknown> ({shots} shots)"
            )

        if submission_backend_name:
            normalized_submission = submission_backend_name.strip().lower()
            if (
                target_backend_normalized is not None
                and normalized_submission != target_backend_normalized
            ):
                raise RuntimeError(
                    "Baseline measurement observed execution on backend "
                    f"'{submission_backend_name}', but expected '{target_backend_name}'."
                )

            if observed_backend_normalized is None:
                observed_backend_normalized = normalized_submission
                observed_backend_label = submission_backend_name
            elif normalized_submission != observed_backend_normalized:
                raise RuntimeError(
                    "Baseline measurement backend changed mid-run: "
                    f"'{observed_backend_label}' → '{submission_backend_name}'."
                )

        counts = result.get_counts()

        # Compute expectation value
        expectation = 0.0
        for bitstring, count in counts.items():
            probability = count / shots
            parity = 1.0
            for qubit_idx, pauli in enumerate(obs.pauli_string):
                if pauli != "I":
                    bit = int(bitstring[-(qubit_idx + 1)])
                    parity *= 1 - 2 * bit
            expectation += probability * parity

        expectation *= obs.coefficient
        results[str(obs)] = {
            'expectation': expectation,
            'expected': analytical_ghz_expectation(obs),
            'error': abs(expectation - analytical_ghz_expectation(obs)),
            'shots': shots,
        }

        expected = results[str(obs)]['expected']
        error = results[str(obs)]['error']
        print(f"{str(obs):<10} Measured: {expectation:>7.4f}  Expected: {expected:>6.2f}  Error: {error:.4f}")

    elapsed = time.time() - start_time
    print(f"\nBaseline execution time: {elapsed:.2f}s")

    return results


def run_shadows_experiment(
    circuit: QuantumCircuit,
    observables: List[Observable],
    backend_descriptor: str,
    variant: str,  # "v0" or "v1"
    shadow_size: int = 5000,
    mem_shots: int = 512,
    data_dir: str = "./validation_data"
) -> Tuple[Dict, Dict]:
    """Run classical shadows experiment (v0 or v1+MEM)."""

    use_mem = (variant == "v1")
    calibration_shots = (2 ** circuit.num_qubits) * mem_shots if use_mem else 0
    total_shots = shadow_size + calibration_shots

    print("\n" + "="*60)
    print(f"CLASSICAL SHADOWS: {'v1 (Noise-Aware + MEM)' if use_mem else 'v0 (Baseline)'}")
    print("="*60)
    print(f"Shadow size: {shadow_size}")
    if use_mem:
        print(f"MEM calibration shots: {calibration_shots} ({mem_shots} per basis state)")
    print(f"Total shots: {total_shots}")
    print()

    # Configure shadows
    shadow_config = ShadowConfig(
        version=ShadowVersion.V1_NOISE_AWARE if use_mem else ShadowVersion.V0_BASELINE,
        shadow_size=shadow_size,
        random_seed=42,
        apply_inverse_channel=use_mem,
    )

    mitigation_config = None
    if use_mem:
        mitigation_config = MitigationConfig(
            techniques=[],  # Auto-populated by estimator
            parameters={"mem_shots": mem_shots}
        )

    # Create estimator
    estimator = ShadowEstimator(
        backend=backend_descriptor,
        shadow_config=shadow_config,
        mitigation_config=mitigation_config,
        data_dir=data_dir
    )

    print(f"Backend: {estimator.backend.name}")
    if estimator._backend_snapshot:
        print(f"Calibration timestamp: {estimator._backend_snapshot.calibration_timestamp}")
        if estimator._backend_snapshot.readout_errors:
            avg_readout_error = np.mean(list(estimator._backend_snapshot.readout_errors.values()))
            print(f"Average readout error: {avg_readout_error:.4f}")
    print()

    # Run estimation
    start_time = time.time()
    result = estimator.estimate(
        circuit=circuit,
        observables=observables,
        save_manifest=True
    )
    elapsed = time.time() - start_time

    print(f"Execution time: {elapsed:.2f}s")
    manifest_path = result.manifest_path
    if manifest_path:
        print(f"Manifest saved: {manifest_path}")
    shot_data_path = result.shot_data_path
    if shot_data_path:
        print(f"Shot data saved: {shot_data_path}")

    if use_mem and estimator.measurement_error_mitigation:
        print(f"\nMEM confusion matrix shape: {estimator.measurement_error_mitigation.confusion_matrix.shape}")
        print(f"MEM in techniques: {'MEM' in estimator.mitigation_config.techniques}")

    print("\nResults:")
    shadows_results = {}
    for obs_str, data in result.observables.items():
        exp_val = data['expectation_value']
        ci = data.get('ci_95') or data.get('confidence_interval')
        ci_width = data.get('ci_width')

        # Get analytical expectation
        obs = next(o for o in observables if str(o) == obs_str)
        expected = analytical_ghz_expectation(obs)
        error = abs(exp_val - expected)
        in_ci = None
        if ci is not None:
            lower, upper = ci
            in_ci = lower <= expected <= upper

        shadows_results[obs_str] = {
            'expectation': exp_val,
            'ci': ci,
            'ci_width': ci_width,
            'expected': expected,
            'error': error,
            'in_ci': in_ci
        }

        ci_display = "N/A"
        if ci_width is not None:
            ci_display = f"± {ci_width / 2:>6.4f}"
        ci_marker = "-"
        if in_ci is not None:
            ci_marker = "✓" if in_ci else "✗"
        print(f"{obs_str:<10} {exp_val:>7.4f} {ci_display:>12}  Expected: {expected:>6.2f}  Error: {error:.4f} {ci_marker}")

    return shadows_results, {
        'manifest_path': manifest_path,
        'shot_data_path': shot_data_path,
        'experiment_id': result.experiment_id,
        'backend_name': estimator.backend.name,
        'backend_snapshot': estimator._backend_snapshot,
        'measurement_shots': shadow_size,
        'calibration_shots': calibration_shots,
        'total_shots': total_shots,
    }


def compute_metrics(
    baseline_results: Dict[str, Dict[str, float]],
    shadows_results: Dict[str, Dict],
    baseline_total_shots: int,
    approach_total_shots: int
) -> Dict:
    """Compute validation metrics (SSR, CI coverage, MAE)."""

    # CI Coverage
    ci_flags = [data['in_ci'] for data in shadows_results.values() if data['in_ci'] is not None]
    ci_coverage = np.mean(ci_flags) if ci_flags else None

    # Mean Absolute Error
    mae = np.mean([data['error'] for data in shadows_results.values()])

    # SSR computation (per observable, then average)
    ssrs = []
    for obs_str, shadow_data in shadows_results.items():
        baseline_info = baseline_results.get(obs_str, {})
        expected = shadow_data['expected']
        baseline_val = baseline_info.get('expectation', expected)
        shadow_val = shadow_data['expectation']

        baseline_error = max(abs(baseline_val - expected), 1e-9)
        shadow_error = max(abs(shadow_val - expected), 1e-9)

        shot_ratio = baseline_total_shots / approach_total_shots if approach_total_shots else float('inf')
        obs_ssr = shot_ratio * (baseline_error / shadow_error)
        ssrs.append(obs_ssr)

    avg_ssr = float(np.mean(ssrs)) if ssrs else None

    return {
        'ci_coverage': ci_coverage,
        'mean_absolute_error': mae,
        'ssr_per_observable': ssrs,
        'ssr_average': avg_ssr,
        'total_shots': approach_total_shots,
    }


def main():
    """Run comprehensive hardware validation experiment."""

    print("="*80)
    print("QuartumSE Hardware Validation - Phase 1 Exit Criterion")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Configuration
    backend_descriptor = "ibm:ibm_torino"
    num_qubits = 3
    total_shots_budget = 5000
    shadow_shots_v0 = total_shots_budget  # Shadows v0 uses all measurement shots
    shadow_shots_v1 = 904  # Shadows v1 measurement shots after allocating calibration budget
    mem_shots = 512  # Shots per basis state for MEM calibration (8 * 512 = 4096)
    data_dir = "./validation_data"

    Path(data_dir).mkdir(parents=True, exist_ok=True)

    # Create circuit and observables
    circuit = create_ghz_circuit(num_qubits)
    observables = [
        Observable("ZII", coefficient=1.0),
        Observable("IZI", coefficient=1.0),
        Observable("IIZ", coefficient=1.0),
        Observable("ZZI", coefficient=1.0),
        Observable("ZIZ", coefficient=1.0),
        Observable("IZZ", coefficient=1.0),
    ]

    print("Circuit: GHZ-3 State")
    print(circuit)
    print()
    print(f"Observables: {len(observables)}")
    for obs in observables:
        expected = analytical_ghz_expectation(obs)
        print(f"  {obs} → {expected:.2f}")
    print()

    baseline_allocation = allocate_shots(total_shots_budget, observables)
    calibration_total = (2 ** num_qubits) * mem_shots

    print(f"Fixed shot budget per approach: {total_shots_budget}")
    print(f"  Baseline total measurement shots: {total_shots_budget}")
    print(f"  Shadows v0 measurement shots: {shadow_shots_v0}")
    print(f"  Shadows v1 measurement shots: {shadow_shots_v1}")
    print(f"  Shadows v1 calibration shots: {calibration_total}")
    print()

    # Connect to backend
    print(f"Connecting to backend: {backend_descriptor}...")
    backend, snapshot = resolve_backend(backend_descriptor)

    _, _, requested_backend_name = backend_descriptor.partition(":")
    requested_backend_name = requested_backend_name.strip()
    resolved_backend_name = _extract_backend_name(backend)

    if not requested_backend_name:
        raise ValueError(
            f"Backend descriptor '{backend_descriptor}' is missing an IBM backend name."
        )

    if not resolved_backend_name:
        raise RuntimeError(
            "Resolved backend did not expose a name. An IBM Runtime backend is required for hardware validation."
        )

    if resolved_backend_name.strip().lower() != requested_backend_name.lower():
        raise RuntimeError(
            "Resolved backend does not match requested IBM Runtime target: "
            f"expected '{requested_backend_name}', got '{resolved_backend_name}'."
        )

    print(f"✓ Connected to: {resolved_backend_name}")
    print(f"  Qubits: {snapshot.num_qubits}")
    print(f"  Calibration: {snapshot.calibration_timestamp}")
    if snapshot.readout_errors:
        avg_readout = np.mean(list(snapshot.readout_errors.values()))
        print(f"  Avg readout error: {avg_readout:.4f}")
    print()

    # Run experiments
    validation_results = {
        'experiment_info': {
            'date': datetime.now().isoformat(),
            'backend': resolved_backend_name,
            'circuit': 'GHZ-3',
            'num_qubits': num_qubits,
            'total_shot_budget': total_shots_budget,
            'baseline_shot_allocation': baseline_allocation,
            'shadows_v0_measurement_shots': shadow_shots_v0,
            'shadows_v1_measurement_shots': shadow_shots_v1,
            'shadows_v1_calibration_shots': calibration_total,
            'mem_shots_per_basis': mem_shots,
        }
    }

    # 1. Baseline
    baseline_results = run_baseline_measurement(
        circuit,
        observables,
        backend,
        baseline_allocation,
        expected_backend_name=resolved_backend_name,
    )
    baseline_total_shots = sum(baseline_allocation.values())
    baseline_mae = float(np.mean([data['error'] for data in baseline_results.values()])) if baseline_results else 0.0
    validation_results['baseline'] = {
        'results': baseline_results,
        'shot_allocation': baseline_allocation,
        'metrics': {
            'mean_absolute_error': baseline_mae,
            'total_shots': baseline_total_shots,
        }
    }

    # 2. Shadows v0
    shadows_v0_results, v0_metadata = run_shadows_experiment(
        circuit, observables, backend_descriptor, "v0",
        shadow_shots_v0, data_dir=data_dir
    )
    v0_total_shots = v0_metadata.get('total_shots', shadow_shots_v0)
    v0_metrics = compute_metrics(baseline_results, shadows_v0_results, baseline_total_shots, v0_total_shots)
    validation_results['shadows_v0'] = {
        'results': shadows_v0_results,
        'metrics': v0_metrics,
        'metadata': v0_metadata
    }

    # 3. Shadows v1 + MEM
    shadows_v1_results, v1_metadata = run_shadows_experiment(
        circuit, observables, backend_descriptor, "v1",
        shadow_shots_v1, mem_shots, data_dir=data_dir
    )
    v1_total_shots = v1_metadata.get('total_shots', shadow_shots_v1 + calibration_total)
    v1_metrics = compute_metrics(baseline_results, shadows_v1_results, baseline_total_shots, v1_total_shots)
    validation_results['shadows_v1_mem'] = {
        'results': shadows_v1_results,
        'metrics': v1_metrics,
        'metadata': v1_metadata
    }

    # Summary
    def format_ci(value: Optional[float]) -> str:
        return "N/A" if value is None else f"{value:.1%}"

    def format_ssr(value: Optional[float]) -> str:
        return "N/A" if value is None else f"{value:.2f}×"

    def format_shots(value: Optional[int]) -> str:
        return "N/A" if value is None else f"{value:,}"

    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    print()
    print(f"{'Approach':<25} {'Total Shots':>12} {'CI Coverage':>15} {'MAE':>12} {'SSR':>12} {'Status'}")
    print("-"*92)

    print(
        f"{'Baseline (Direct)':<25} "
        f"{format_shots(baseline_total_shots):>12} "
        f"{format_ci(None):>15} "
        f"{baseline_mae:>12.4f} "
        f"{'1.00×':>12} "
        f"{'✓ PASS'}"
    )

    v0_status = "✓ PASS" if (v0_metrics['ssr_average'] or 0) >= 1.1 else "✗ FAIL"
    v1_status = "✓ PASS" if (v1_metrics['ssr_average'] or 0) >= 1.1 else "✗ FAIL"

    print(
        f"{'Shadows v0 (Baseline)':<25} "
        f"{format_shots(v0_metrics.get('total_shots')):>12} "
        f"{format_ci(v0_metrics['ci_coverage']):>15} "
        f"{v0_metrics['mean_absolute_error']:>12.4f} "
        f"{format_ssr(v0_metrics['ssr_average']):>12} "
        f"{v0_status}"
    )
    print(
        f"{'Shadows v1 (+ MEM)':<25} "
        f"{format_shots(v1_metrics.get('total_shots')):>12} "
        f"{format_ci(v1_metrics['ci_coverage']):>15} "
        f"{v1_metrics['mean_absolute_error']:>12.4f} "
        f"{format_ssr(v1_metrics['ssr_average']):>12} "
        f"{v1_status}"
    )
    print()

    print("MEM Effectiveness:")
    mae_reduction = None
    if v0_metrics['mean_absolute_error'] > 0:
        mae_reduction = (
            (v0_metrics['mean_absolute_error'] - v1_metrics['mean_absolute_error'])
            / v0_metrics['mean_absolute_error'] * 100
        )
    if mae_reduction is not None:
        print(f"  MAE reduction vs v0: {mae_reduction:+.1f}%")
    else:
        print("  MAE reduction vs v0: N/A")
    print()

    print("Phase 1 Exit Criterion:")
    v1_ssr = v1_metrics['ssr_average'] or 0
    v1_ci = v1_metrics['ci_coverage'] or 0
    phase1_pass = v1_ssr >= 1.1 and v1_ci >= 0.80
    print(f"  SSR ≥ 1.1×: {v1_ssr:.2f}× {'✓ PASS' if v1_ssr >= 1.1 else '✗ FAIL'}")
    print(f"  CI Coverage ≥ 80%: {v1_ci:.1%} {'✓ PASS' if v1_ci >= 0.80 else '✗ FAIL'}")
    print(f"  Overall: {'✓ PHASE 1 COMPLETE' if phase1_pass else '✗ NEEDS IMPROVEMENT'}")
    print()

    mae_by_approach = {
        'Baseline (Direct)': baseline_mae,
        'Shadows v0 (Baseline)': v0_metrics['mean_absolute_error'],
        'Shadows v1 (+ MEM)': v1_metrics['mean_absolute_error'],
    }
    best_approach, best_mae = min(mae_by_approach.items(), key=lambda item: item[1])
    print(f"Best accuracy under fixed 5,000-shot budget: {best_approach} (MAE={best_mae:.4f})")
    print()

    validation_results['summary'] = {
        'baseline_mae': baseline_mae,
        'baseline_total_shots': baseline_total_shots,
        'shadows_v0_metrics': v0_metrics,
        'shadows_v1_metrics': v1_metrics,
        'mae_by_approach': mae_by_approach,
        'best_approach': best_approach,
    }

    # Save results
    results_path = Path(data_dir) / "hardware_validation_results.json"
    with open(results_path, 'w') as f:
        # Convert numpy types to native Python for JSON serialization
        def convert_numpy(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(item) for item in obj]
            return obj

        json.dump(convert_numpy(validation_results), f, indent=2, default=str)

    print(f"Results saved: {results_path}")
    print()
    print("="*80)
    print("VALIDATION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    # Load IBM token from environment
    if not os.environ.get('QISKIT_IBM_TOKEN'):
        print("Error: QISKIT_IBM_TOKEN not set")
        print("Set with: export QISKIT_IBM_TOKEN=<YOUR_TOKEN>")
        print("(You can also keep it in a local .env file and run: source .env)")
        exit(1)

    main()
