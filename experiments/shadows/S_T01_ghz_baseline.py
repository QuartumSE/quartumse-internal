"""

import argparse

S-T01: Classical Shadows on GHZ States (Baseline v0)

Experiment Overview:
- Prepare GHZ states with 3, 4, 5 qubits
- Estimate observables: ⟨Z_i⟩, ⟨Z_i Z_j⟩, purity
- Compare classical shadows vs direct measurement
- Target: SSR ≥ 1.2 on simulator, CI coverage ≥ 0.9

This validates the baseline classical shadows implementation.
"""

import sys
import time
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from qiskit import QuantumCircuit

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from quartumse import ShadowEstimator
from quartumse.shadows import ShadowConfig
from quartumse.shadows.core import Observable
from quartumse.utils.metrics import compute_ssr


def _load_experiment_config(config_path: Optional[Union[str, Path]]) -> Dict[str, Any]:
    """Load YAML configuration if present."""

    if not config_path:
        return {}

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise ValueError("Experiment config must be a mapping at the top level")

    return data


def _resolve_backend_descriptor(config: Dict[str, Any], override: Optional[str]) -> str:
    """Determine the backend descriptor from config and overrides."""

    if override:
        return override

    backend_cfg = config.get("backend") if config else None
    if isinstance(backend_cfg, str):
        return backend_cfg
    if isinstance(backend_cfg, dict):
        provider = backend_cfg.get("provider", "local")
        name = backend_cfg.get("name")
        if name and provider and provider.lower() != "local":
            return f"{provider}:{name}"
        if name:
            return name

    return "aer_simulator"


def create_ghz_circuit(num_qubits: int) -> QuantumCircuit:
    """
    Create GHZ state: |GHZ⟩ = (|00...0⟩ + |11...1⟩) / √2

    Args:
        num_qubits: Number of qubits

    Returns:
        GHZ preparation circuit
    """
    qc = QuantumCircuit(num_qubits)
    qc.h(0)  # Hadamard on first qubit
    for i in range(1, num_qubits):
        qc.cx(0, i)  # CNOT chain
    return qc


def direct_measurement_baseline(
    circuit: QuantumCircuit, observable: Observable, shots: int, backend
) -> dict:
    """
    Baseline: direct measurement in Pauli basis.

    Measures the observable directly by rotating to eigenbasis.
    """
    # For simplicity, measure in Z basis (assumes Pauli string is all Z/I)
    # Full implementation would rotate based on Pauli string
    qc = circuit.copy()
    qc.measure_all()

    job = backend.run(qc, shots=shots)
    counts = job.result().get_counts()

    # Compute expectation value
    total = sum(counts.values())
    expectation = 0.0

    for bitstring, count in counts.items():
        # Compute parity for Z observable
        parity = 1
        for i, pauli in enumerate(observable.pauli_string):
            if pauli == "Z":
                bit = int(bitstring[::-1][i])
                parity *= 1 - 2 * bit  # 0 -> +1, 1 -> -1
        expectation += parity * count / total

    # Variance estimate (binomial)
    variance = (1 - expectation**2) / shots

    return {
        "expectation": expectation * observable.coefficient,
        "variance": variance,
        "shots": shots,
    }


def run_experiment(
    config_path: Optional[Union[str, Path]] = None,
    backend_override: Optional[str] = None,
) -> None:
    """Run S-T01 experiment."""
    print("=" * 80)
    print("S-T01: Classical Shadows on GHZ States (Baseline v0)")
    print("=" * 80)

    config = _load_experiment_config(config_path)
    backend_descriptor = _resolve_backend_descriptor(config, backend_override)
    print(f"Backend descriptor: {backend_descriptor}")

    # Configuration
    num_qubits_list = config.get("num_qubits", [3, 4, 5])
    shadow_size = config.get("shadow_size", 500)
    baseline_shots = config.get("baseline_shots", 1000)
    random_seed = config.get("random_seed", 42)

    results = []

    for num_qubits in num_qubits_list:
        print(f"\n{'=' * 60}")
        print(f"GHZ({num_qubits}) State")
        print(f"{'=' * 60}")

        # Create GHZ circuit
        ghz_circuit = create_ghz_circuit(num_qubits)
        print(f"Circuit depth: {ghz_circuit.depth()}")
        print(f"Circuit:\n{ghz_circuit}")

        # Define observables
        observables = []

        # Single-qubit Z observables: ⟨Z_i⟩
        for i in range(num_qubits):
            pauli_str = "I" * i + "Z" + "I" * (num_qubits - i - 1)
            observables.append(Observable(pauli_str, coefficient=1.0))

        # Two-qubit ZZ observables: ⟨Z_0 Z_i⟩
        for i in range(1, num_qubits):
            pauli_str = "Z" + "I" * (i - 1) + "Z" + "I" * (num_qubits - i - 1)
            observables.append(Observable(pauli_str, coefficient=1.0))

        print(f"\nObservables to estimate: {len(observables)}")
        for obs in observables:
            print(f"  {obs}")

        # ============================================================
        # Classical Shadows Estimation
        # ============================================================
        print(f"\n{'*' * 40}")
        print("CLASSICAL SHADOWS ESTIMATION")
        print(f"{'*' * 40}")

        shadow_config = ShadowConfig(
            shadow_size=shadow_size,
            random_seed=random_seed,
            confidence_level=0.95,
        )

        estimator = ShadowEstimator(
            backend=backend_descriptor,
            shadow_config=shadow_config,
        )

        execution_backend = estimator.backend
        snapshot = getattr(estimator, '_backend_snapshot', None)
        if snapshot is not None:
            print(
                f"Calibration timestamp: {snapshot.calibration_timestamp.isoformat()} (hash={snapshot.properties_hash[:8] if snapshot.properties_hash else 'n/a'})"
            )
        else:
            print('Calibration snapshot will be captured during estimation.')

        start_time = time.time()
        shadow_result = estimator.estimate(
            circuit=ghz_circuit,
            observables=observables,
            save_manifest=True,
        )
        shadow_time = time.time() - start_time

        print(f"Shadow size: {shadow_size}")
        print(f"Execution time: {shadow_time:.2f}s")
        print(f"Manifest saved: {shadow_result.manifest_path}")

        # ============================================================
        # Baseline Direct Measurement
        # ============================================================
        print(f"\n{'*' * 40}")
        print("BASELINE DIRECT MEASUREMENT")
        print(f"{'*' * 40}")

        baseline_results = {}
        for obs in observables:
            baseline_results[str(obs)] = direct_measurement_baseline(
                ghz_circuit, obs, baseline_shots, execution_backend
            )

        # ============================================================
        # Comparison
        # ============================================================
        print(f"\n{'*' * 40}")
        print("COMPARISON")
        print(f"{'*' * 40}")

        print(f"\n{'Observable':<20} {'Shadows':<15} {'Baseline':<15} {'CI Width':<15}")
        print("-" * 65)

        ci_coverage_count = 0
        total_observables = len(observables)

        for obs in observables:
            obs_str = str(obs)
            shadow_val = shadow_result.observables[obs_str]["expectation_value"]
            shadow_ci = shadow_result.observables[obs_str]["ci_95"]
            shadow_width = shadow_result.observables[obs_str]["ci_width"]
            baseline_val = baseline_results[obs_str]["expectation"]

            # Check if baseline is within CI (proxy for coverage since we don't have ground truth)
            in_ci = shadow_ci[0] <= baseline_val <= shadow_ci[1]
            ci_coverage_count += int(in_ci)

            print(
                f"{obs_str:<20} {shadow_val:>7.4f}      {baseline_val:>7.4f}      "
                f"{shadow_width:>7.4f}  {'✓' if in_ci else '✗'}"
            )

        # Compute metrics
        ci_coverage = ci_coverage_count / total_observables
        avg_baseline_variance = np.mean(
            [r["variance"] for r in baseline_results.values()]
        )
        avg_shadow_variance = np.mean(
            [r["variance"] for r in shadow_result.observables.values()]
        )

        # SSR approximation (variance-based)
        ssr = compute_ssr(
            baseline_shots,
            shadow_size,
            baseline_precision=np.sqrt(avg_baseline_variance),
            quartumse_precision=np.sqrt(avg_shadow_variance),
        )

        print(f"\n{'=' * 60}")
        print(f"METRICS for GHZ({num_qubits})")
        print(f"{'=' * 60}")
        print(f"CI Coverage:         {ci_coverage:.2%} (target: ≥90%)")
        print(f"SSR (estimated):     {ssr:.2f}× (target: ≥1.2×)")
        print(f"Shadow size:         {shadow_size}")
        print(f"Baseline shots:      {baseline_shots}")

        results.append(
            {
                "num_qubits": num_qubits,
                "ci_coverage": ci_coverage,
                "ssr": ssr,
                "shadow_size": shadow_size,
                "baseline_shots": baseline_shots,
                "manifest": shadow_result.manifest_path,
            }
        )

    # ============================================================
    # Summary
    # ============================================================
    print(f"\n{'=' * 80}")
    print("EXPERIMENT SUMMARY")
    print(f"{'=' * 80}")

    print(f"\n{'Qubits':<10} {'CI Coverage':<15} {'SSR':<10} {'Status'}")
    print("-" * 50)

    all_passed = True
    for r in results:
        ci_pass = r["ci_coverage"] >= 0.9
        ssr_pass = r["ssr"] >= 1.2
        status = "✓ PASS" if (ci_pass and ssr_pass) else "✗ FAIL"
        all_passed = all_passed and ci_pass and ssr_pass

        print(
            f"{r['num_qubits']:<10} {r['ci_coverage']:<15.2%} {r['ssr']:<10.2f} {status}"
        )

    print(f"\n{'=' * 80}")
    if all_passed:
        print("✓ S-T01 EXPERIMENT PASSED - Phase 1 exit criteria met!")
    else:
        print("✗ S-T01 EXPERIMENT FAILED - Review results and tune parameters")
    print(f"{'=' * 80}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the S-T01 GHZ baseline experiment.")
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to YAML configuration file (backend, shot counts, etc.)",
    )
    parser.add_argument(
        "--backend",
        type=str,
        default=None,
        help="Override backend descriptor (e.g., ibm:ibmq_qasm_simulator)",
    )
    args = parser.parse_args()
    run_experiment(config_path=args.config, backend_override=args.backend)
