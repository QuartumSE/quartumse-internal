"""S-T01/S-T02 GHZ validation experiments for classical shadows."""

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np
import yaml
from qiskit import QuantumCircuit

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from quartumse import ShadowEstimator
from quartumse.reporting.manifest import MitigationConfig
from quartumse.shadows import ShadowConfig
from quartumse.shadows.config import ShadowVersion
from quartumse.shadows.core import Observable
from quartumse.utils.args import (
    DEFAULT_DATA_DIR,
    add_backend_option,
    add_data_dir_option,
    add_seed_option,
    add_shadow_size_option,
)
from quartumse.utils.metrics import compute_ssr
from quartumse.connectors import is_ibm_runtime_backend, create_runtime_sampler


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


def _resolve_data_dir(
    config: Dict[str, Any], override: Optional[Union[str, Path]]
) -> Path:
    """Resolve the data directory used for manifests and shot archives."""

    if override is not None:
        return Path(override)

    candidate = config.get("data_dir") if config else None
    if candidate:
        return Path(candidate)

    return DEFAULT_DATA_DIR


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

    sampler = None
    if is_ibm_runtime_backend(backend):
        sampler = create_runtime_sampler(backend)

    if sampler is not None:
        from qiskit import transpile
        transpiled = transpile(qc, backend)
        job = sampler.run([transpiled], shots=shots)
        result = job.result()
        counts = result[0].data.meas.get_counts()
    else:
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


def ghz_expectation_value(observable: Observable) -> float:
    """Analytical expectation value for GHZ state observables."""

    if any(p not in {"I", "Z"} for p in observable.pauli_string):
        return 0.0

    num_z = observable.pauli_string.count("Z")
    if num_z == 0:
        return observable.coefficient

    if num_z % 2 == 0:
        return observable.coefficient

    return 0.0


def run_experiment(
    config_path: Optional[Union[str, Path]] = None,
    backend_override: Optional[str] = None,
    variant: str = "st01",
    *,
    data_dir: Optional[Union[str, Path]] = None,
    random_seed_override: Optional[int] = None,
    shadow_size_override: Optional[int] = None,
) -> None:
    """Run GHZ benchmarks for classical shadows variants."""

    variant = variant.lower()
    variant_title = {
        "st01": "S-T01: Classical Shadows on GHZ States (Baseline v0)",
        "st02": "S-T02: Noise-aware GHZ Shadows with MEM (v1)",
    }.get(variant, "S-T01: Classical Shadows on GHZ States (Baseline v0)")

    print("=" * 80)
    print(variant_title)
    print("=" * 80)

    config = _load_experiment_config(config_path)
    backend_descriptor = _resolve_backend_descriptor(config, backend_override)
    print(f"Backend descriptor: {backend_descriptor}")

    # Configuration
    num_qubits_list = config.get("num_qubits", [3, 4, 5])
    shadow_size = int(shadow_size_override or config.get("shadow_size", 500))
    baseline_shots = int(config.get("baseline_shots", 1000))
    random_seed = (
        random_seed_override
        if random_seed_override is not None
        else config.get("random_seed", 42)
    )
    if random_seed is not None:
        random_seed = int(random_seed)
    mem_shots = int(config.get("mem_shots", 2048))
    resolved_data_dir = _resolve_data_dir(config, data_dir)
    resolved_data_dir.mkdir(parents=True, exist_ok=True)
    print(f"Data directory: {resolved_data_dir.resolve()}")

    use_noise_aware = variant == "st02"

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
            version=(
                ShadowVersion.V1_NOISE_AWARE if use_noise_aware else ShadowVersion.V0_BASELINE
            ),
            apply_inverse_channel=use_noise_aware,
        )

        mitigation_config = None
        if use_noise_aware:
            mitigation_config = MitigationConfig(
                techniques=["MEM"],
                parameters={"mem_shots": mem_shots},
            )

        estimator = ShadowEstimator(
            backend=backend_descriptor,
            shadow_config=shadow_config,
            mitigation_config=mitigation_config,
            data_dir=resolved_data_dir,
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

        print(
            f"\n{'Observable':<20} {'Shadows':<15} {'Expected':<15} "
            f"{'Baseline':<15} {'CI Width':<12} {'SSR':<8} {'Coverage'}"
        )
        print("-" * 95)

        ci_coverage_count = 0
        total_observables = len(observables)
        ssr_values = []

        for obs in observables:
            obs_str = str(obs)
            shadow_val = shadow_result.observables[obs_str]["expectation_value"]
            shadow_ci = shadow_result.observables[obs_str]["ci_95"]
            shadow_width = shadow_result.observables[obs_str]["ci_width"]
            baseline_val = baseline_results[obs_str]["expectation"]
            expected_val = ghz_expectation_value(obs)

            in_ci = shadow_ci[0] <= expected_val <= shadow_ci[1]
            ci_coverage_count += int(in_ci)

            baseline_error = max(abs(baseline_val - expected_val), 1e-9)
            shadow_error = max(abs(shadow_val - expected_val), 1e-9)
            obs_ssr = compute_ssr(
                baseline_shots,
                shadow_size,
                baseline_precision=baseline_error,
                quartumse_precision=shadow_error,
            )
            ssr_values.append(obs_ssr)

            print(
                f"{obs_str:<20} {shadow_val:>7.4f}      {expected_val:>7.4f}      "
                f"{baseline_val:>7.4f}      {shadow_width:>7.4f}  {obs_ssr:>6.2f}  "
                f"{'✓' if in_ci else '✗'}"
            )

        # Compute metrics
        ci_coverage = ci_coverage_count / total_observables
        ssr = float(np.mean(ssr_values)) if ssr_values else float("nan")

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
        print("✓ EXPERIMENT PASSED - Phase 1 exit criteria met!")
    else:
        print("✗ EXPERIMENT FAILED - Review results and tune parameters")
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
    add_backend_option(parser)
    add_shadow_size_option(parser)
    add_seed_option(parser)
    add_data_dir_option(parser)
    parser.add_argument(
        "--variant",
        type=str,
        default="st01",
        choices=["st01", "st02"],
        help="Experiment variant (st01=baseline, st02=noise-aware with MEM)",
    )
    args = parser.parse_args()
    run_experiment(
        config_path=args.config,
        backend_override=args.backend,
        variant=args.variant,
        data_dir=args.data_dir,
        random_seed_override=args.seed,
        shadow_size_override=args.shadow_size,
    )
