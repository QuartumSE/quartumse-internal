"""
M-T01: GHZ Phase Sensing

Experiment Overview:
- Prepare GHZ(3-4) state
- Encode small Z-phase rotation
- Estimate phase via optimal readout
- Target: CI coverage ≥ 0.8 on simulator

Status: STARTER SCAFFOLD
"""

import sys
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from quartumse import ShadowEstimator
from quartumse.shadows import ShadowConfig
from quartumse.shadows.core import Observable


def ghz_phase_sensor(num_qubits: int, phase: float) -> QuantumCircuit:
    """
    GHZ state with encoded phase.

    |GHZ⟩ = (|0⟩^n + e^{iφ}|1⟩^n) / √2

    Args:
        num_qubits: Number of qubits
        phase: Phase to encode

    Returns:
        Circuit
    """
    qc = QuantumCircuit(num_qubits)

    # Create GHZ
    qc.h(0)
    for i in range(1, num_qubits):
        qc.cx(0, i)

    # Encode phase on all qubits
    for i in range(num_qubits):
        qc.rz(phase, i)

    return qc


def run_experiment():
    """Run M-T01 starter."""
    print("=" * 80)
    print("M-T01: GHZ Phase Sensing (STARTER)")
    print("=" * 80)

    backend = AerSimulator()
    num_qubits = 3
    true_phase = 0.1  # Small phase to estimate
    shadow_size = 1000

    print(f"\nConfiguration:")
    print(f"  Qubits: {num_qubits}")
    print(f"  True phase: {true_phase:.4f} rad")

    # Create circuit
    circuit = ghz_phase_sensor(num_qubits, true_phase)
    print(f"\nCircuit:\n{circuit}")

    # Observable for phase estimation (Z^⊗n)
    obs = Observable("Z" * num_qubits, coefficient=1.0)

    # Estimate with shadows
    shadow_config = ShadowConfig(shadow_size=shadow_size, random_seed=42)
    estimator = ShadowEstimator(backend=backend, shadow_config=shadow_config)

    result = estimator.estimate(circuit=circuit, observables=[obs], save_manifest=True)

    # Extract estimate
    zn_expectation = result.observables[str(obs)]["expectation_value"]
    ci = result.observables[str(obs)]["ci_95"]

    # Phase estimate (assuming small phase)
    # ⟨Z^⊗n⟩ ≈ cos(n * φ) for GHZ
    phase_estimate = np.arccos(zn_expectation) / num_qubits

    print(f"\n{'=' * 60}")
    print(f"Results:")
    print(f"  ⟨Z^⊗{num_qubits}⟩: {zn_expectation:.4f} ± {(ci[1]-ci[0])/2:.4f}")
    print(f"  True phase: {true_phase:.4f} rad")
    print(f"  Estimated phase: {phase_estimate:.4f} rad")
    print(f"  Error: {abs(phase_estimate - true_phase):.4f} rad")
    print(f"{'=' * 60}")

    print("\n[TODO] Implement variational metrology (optimize state + measurement)")
    print("[TODO] Explore ZNE for readout bias mitigation")
    print("[TODO] Test on larger GHZ states")

    return result


if __name__ == "__main__":
    run_experiment()
