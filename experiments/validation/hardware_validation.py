"""
Hardware Validation Experiment for QuartumSE Phase 1

Validates on IBM Quantum hardware:
- Shot efficiency (classical shadows vs baseline)
- Noise mitigation (MEM effectiveness)
- Full provenance tracking
- Phase 1 exit criterion: SSR ≥ 1.1×

Circuit: GHZ-3 state
Observables: ZII, IZI, IIZ, ZZI, ZIZ, IZZ
Approaches: Baseline (1000 shots), Shadows v0 (500 shots), Shadows v1+MEM (500 shots)
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.primitives import Sampler

from quartumse import ShadowEstimator
from quartumse.shadows import ShadowConfig
from quartumse.shadows.config import ShadowVersion
from quartumse.shadows.core import Observable
from quartumse.reporting.manifest import MitigationConfig
from quartumse.connectors import resolve_backend
from quartumse.utils.metrics import compute_ssr


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


def run_baseline_measurement(
    circuit: QuantumCircuit,
    observables: List[Observable],
    backend,
    shots: int = 1000
) -> Dict[str, float]:
    """Run baseline direct Pauli measurement (ground truth)."""
    print("\n" + "="*60)
    print("BASELINE: Direct Pauli Measurement")
    print("="*60)
    print(f"Shots per observable: {shots}")
    print(f"Total observables: {len(observables)}")
    print(f"Total shots: {shots * len(observables)}")
    print()

    results = {}
    start_time = time.time()

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

        # Transpile and execute
        transpiled = transpile(measure_circuit, backend)
        sampler = Sampler()
        job = sampler.run(transpiled, shots=shots)
        result = job.result()
        counts = result.quasi_dists[0]

        # Compute expectation value
        expectation = 0.0
        for bitstring_int, probability in counts.items():
            # Convert to binary and compute parity
            bitstring = format(bitstring_int, f'0{circuit.num_qubits}b')
            parity = 1.0
            for qubit_idx, pauli in enumerate(obs.pauli_string):
                if pauli != "I":
                    bit = int(bitstring[-(qubit_idx + 1)])  # Qiskit little-endian
                    parity *= 1 - 2 * bit
            expectation += probability * parity

        expectation *= obs.coefficient
        results[str(obs)] = expectation

        expected = analytical_ghz_expectation(obs)
        error = abs(expectation - expected)
        print(f"{str(obs):<10} Measured: {expectation:>7.4f}  Expected: {expected:>6.2f}  Error: {error:.4f}")

    elapsed = time.time() - start_time
    print(f"\nBaseline execution time: {elapsed:.2f}s")

    return results


def run_shadows_experiment(
    circuit: QuantumCircuit,
    observables: List[Observable],
    backend_descriptor: str,
    variant: str,  # "v0" or "v1"
    shadow_size: int = 500,
    mem_shots: int = 512,
    data_dir: str = "./validation_data"
) -> Tuple[Dict, Dict]:
    """Run classical shadows experiment (v0 or v1+MEM)."""

    use_mem = (variant == "v1")

    print("\n" + "="*60)
    print(f"CLASSICAL SHADOWS: {'v1 (Noise-Aware + MEM)' if use_mem else 'v0 (Baseline)'}")
    print("="*60)
    print(f"Shadow size: {shadow_size}")
    if use_mem:
        print(f"MEM calibration shots: {mem_shots}")
        print(f"Total shots: {shadow_size + (2**circuit.num_qubits * mem_shots)}")
    else:
        print(f"Total shots: {shadow_size}")
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
    print(f"Manifest saved: {result.manifest_path}")
    print(f"Shot data saved: {result.shot_data_path}")

    if use_mem and estimator.measurement_error_mitigation:
        print(f"\nMEM confusion matrix shape: {estimator.measurement_error_mitigation.confusion_matrix.shape}")
        print(f"MEM in techniques: {'MEM' in estimator.mitigation_config.techniques}")

    print("\nResults:")
    shadows_results = {}
    for obs_str, data in result.observables.items():
        exp_val = data['expectation_value']
        ci = data['confidence_interval']
        ci_width = data['ci_width']

        # Get analytical expectation
        obs = next(o for o in observables if str(o) == obs_str)
        expected = analytical_ghz_expectation(obs)
        error = abs(exp_val - expected)
        in_ci = ci[0] <= expected <= ci[1]

        shadows_results[obs_str] = {
            'expectation': exp_val,
            'ci': ci,
            'ci_width': ci_width,
            'expected': expected,
            'error': error,
            'in_ci': in_ci
        }

        ci_marker = "✓" if in_ci else "✗"
        print(f"{obs_str:<10} {exp_val:>7.4f} ± {ci_width/2:>6.4f}  Expected: {expected:>6.2f}  Error: {error:.4f} {ci_marker}")

    return shadows_results, {
        'manifest_path': str(result.manifest_path),
        'shot_data_path': str(result.shot_data_path),
        'experiment_id': result.experiment_id,
        'backend_name': estimator.backend.name,
        'backend_snapshot': estimator._backend_snapshot,
    }


def compute_metrics(
    baseline_results: Dict[str, float],
    shadows_results: Dict[str, Dict],
    baseline_shots: int,
    shadow_shots: int
) -> Dict:
    """Compute validation metrics (SSR, CI coverage, MAE)."""

    # CI Coverage
    ci_coverage = np.mean([data['in_ci'] for data in shadows_results.values()])

    # Mean Absolute Error
    mae = np.mean([data['error'] for data in shadows_results.values()])

    # SSR computation (per observable, then average)
    ssrs = []
    for obs_str, shadow_data in shadows_results.items():
        baseline_val = baseline_results.get(obs_str, 0.0)
        shadow_val = shadow_data['expectation']
        expected = shadow_data['expected']

        baseline_error = max(abs(baseline_val - expected), 1e-9)
        shadow_error = max(abs(shadow_val - expected), 1e-9)

        # SSR = (baseline_shots / shadow_shots) * (shadow_error / baseline_error)
        # If shadow is better: SSR > 1
        obs_ssr = (baseline_shots / shadow_shots) * (baseline_error / shadow_error)
        ssrs.append(obs_ssr)

    avg_ssr = np.mean(ssrs)

    return {
        'ci_coverage': ci_coverage,
        'mean_absolute_error': mae,
        'ssr_per_observable': ssrs,
        'ssr_average': avg_ssr,
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
    baseline_shots = 1000
    shadow_shots = 500
    mem_shots = 512
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

    # Connect to backend
    print(f"Connecting to backend: {backend_descriptor}...")
    backend, snapshot = resolve_backend(backend_descriptor)
    print(f"✓ Connected to: {backend.name}")
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
            'backend': backend.name,
            'circuit': 'GHZ-3',
            'num_qubits': num_qubits,
            'baseline_shots': baseline_shots,
            'shadow_shots': shadow_shots,
            'mem_shots': mem_shots,
        }
    }

    # 1. Baseline
    baseline_results = run_baseline_measurement(
        circuit, observables, backend, baseline_shots
    )
    validation_results['baseline'] = baseline_results

    # 2. Shadows v0
    shadows_v0_results, v0_metadata = run_shadows_experiment(
        circuit, observables, backend_descriptor, "v0",
        shadow_shots, data_dir=data_dir
    )
    v0_metrics = compute_metrics(baseline_results, shadows_v0_results, baseline_shots, shadow_shots)
    validation_results['shadows_v0'] = {
        'results': shadows_v0_results,
        'metrics': v0_metrics,
        'metadata': v0_metadata
    }

    # 3. Shadows v1 + MEM
    shadows_v1_results, v1_metadata = run_shadows_experiment(
        circuit, observables, backend_descriptor, "v1",
        shadow_shots, mem_shots, data_dir=data_dir
    )
    v1_metrics = compute_metrics(baseline_results, shadows_v1_results, baseline_shots, shadow_shots)
    validation_results['shadows_v1_mem'] = {
        'results': shadows_v1_results,
        'metrics': v1_metrics,
        'metadata': v1_metadata
    }

    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    print()
    print(f"{'Approach':<25} {'CI Coverage':<15} {'MAE':<12} {'SSR':<12} {'Status'}")
    print("-"*80)

    v0_status = "✓ PASS" if v0_metrics['ssr_average'] >= 1.1 else "✗ FAIL"
    v1_status = "✓ PASS" if v1_metrics['ssr_average'] >= 1.1 else "✗ FAIL"

    print(f"{'Shadows v0 (Baseline)':<25} {v0_metrics['ci_coverage']:>13.1%} {v0_metrics['mean_absolute_error']:>11.4f} {v0_metrics['ssr_average']:>11.2f}× {v0_status}")
    print(f"{'Shadows v1 (+ MEM)':<25} {v1_metrics['ci_coverage']:>13.1%} {v1_metrics['mean_absolute_error']:>11.4f} {v1_metrics['ssr_average']:>11.2f}× {v1_status}")
    print()

    print("MEM Effectiveness:")
    mae_reduction = ((v0_metrics['mean_absolute_error'] - v1_metrics['mean_absolute_error'])
                     / v0_metrics['mean_absolute_error'] * 100)
    print(f"  MAE reduction: {mae_reduction:+.1f}%")
    print()

    print("Phase 1 Exit Criterion:")
    phase1_pass = v1_metrics['ssr_average'] >= 1.1 and v1_metrics['ci_coverage'] >= 0.80
    print(f"  SSR ≥ 1.1×: {v1_metrics['ssr_average']:.2f}× {'✓ PASS' if v1_metrics['ssr_average'] >= 1.1 else '✗ FAIL'}")
    print(f"  CI Coverage ≥ 80%: {v1_metrics['ci_coverage']:.1%} {'✓ PASS' if v1_metrics['ci_coverage'] >= 0.80 else '✗ FAIL'}")
    print(f"  Overall: {'✓ PHASE 1 COMPLETE' if phase1_pass else '✗ NEEDS IMPROVEMENT'}")
    print()

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
        print("Set with: export QISKIT_IBM_TOKEN='your_token_here'")
        exit(1)

    main()
