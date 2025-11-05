#!/usr/bin/env python3
"""
Quick H₂ chemistry validation experiment (C-T01 / S-CHEM)
Optimized for fast execution on IBM Quantum hardware.

This is the critical chemistry workstream starter for Phase 1 completion.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from qiskit import QuantumCircuit

# Load environment
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quartumse import ShadowEstimator
from quartumse.shadows import ShadowConfig
from quartumse.shadows.config import ShadowVersion
from quartumse.shadows.core import Observable
from quartumse.reporting.manifest import MitigationConfig


def h2_ansatz():
    """
    Simple 4-qubit H₂ ansatz circuit.
    Note: Uses placeholder geometry; update with actual molecular parameters for production.
    """
    qc = QuantumCircuit(4)
    # Initial state preparation
    qc.h(0)
    qc.cx(0, 1)

    # Variational layers (example parameters)
    qc.ry(0.5, 0)
    qc.rz(0.3, 1)
    qc.cx(2, 3)
    qc.ry(0.4, 2)
    qc.rz(0.2, 3)
    qc.cx(1, 2)
    qc.ry(0.2, 1)
    qc.rz(0.1, 2)

    return qc


def h2_hamiltonian_observables():
    """
    H₂ Hamiltonian Pauli terms.
    Note: Placeholder coefficients for smoke test; update with actual qubit-mapped Hamiltonian.

    For real H₂@STO-3G at equilibrium (0.735 Å), typical Hamiltonian includes:
    - Identity term (nuclear repulsion)
    - Single-qubit Z terms
    - Two-qubit ZZ terms
    - Excitation terms (XX, YY combinations)
    """
    terms = [
        ("IIII", -1.05),   # Nuclear repulsion + offset
        ("ZIII", 0.39),
        ("IZII", -0.39),
        ("ZZII", -0.01),
        ("IIZI", 0.39),
        ("IIIZ", -0.39),
        ("IIZZ", -0.01),
        ("ZIZI", 0.03),
        ("IZIZ", 0.03),
        ("XXXX", 0.06),
        ("YYXX", -0.02),
        ("XXYY", -0.02),
    ]
    return [Observable(pauli, coeff) for (pauli, coeff) in terms]


def main():
    backend_name = "ibm_fez"  # Lowest queue as of Nov 3, 2025

    print("=" * 80)
    print("QuartumSE C-T01: H₂ Chemistry Workstream Starter")
    print("Phase 1 Critical Experiment")
    print("=" * 80)

    # Create circuit
    circuit = h2_ansatz()
    print(f"\nCircuit: H₂ ansatz (4 qubits)")
    print(f"Depth: {circuit.depth()}")
    print(f"Gate count: {circuit.count_ops()}")

    # Define observables
    observables = h2_hamiltonian_observables()
    print(f"\nHamiltonian terms: {len(observables)} Pauli observables")
    print("Sample terms:")
    for obs in observables[:5]:
        print(f"  {obs}")

    # Configuration
    shadow_size = 300  # Reduced from 4000 for quick validation
    mem_shots = 128

    print(f"\nBackend: ibm:{backend_name}")
    print(f"Shadow version: v1 (noise-aware + MEM)")
    print(f"Shadow size: {shadow_size}")
    print(f"MEM calibration shots: {mem_shots}")

    # Create estimator with v1 (noise-aware + MEM)
    print("\n" + "=" * 80)
    print("PHASE 1: MEM Calibration")
    print("=" * 80)
    print("Calibrating measurement error mitigation...")

    estimator = ShadowEstimator(
        backend=f"ibm:{backend_name}",
        shadow_config=ShadowConfig(
            version=ShadowVersion.V1_NOISE_AWARE,
            shadow_size=shadow_size,
            random_seed=77,
            apply_inverse_channel=True,
        ),
        mitigation_config=MitigationConfig(
            techniques=[],  # Will be auto-added during calibration
            parameters={"mem_shots": mem_shots}
        ),
        data_dir="data"
    )

    # Run estimation
    print("\n" + "=" * 80)
    print("PHASE 2: Shadow Measurement & Estimation")
    print("=" * 80)
    print("Submitting shadow measurement circuits to IBM Quantum...")
    print(f"Estimated execution time: 5-15 minutes (depending on queue)")

    result = estimator.estimate(
        circuit=circuit,
        observables=observables,
        save_manifest=True,
    )

    # Compute total energy
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Execution time: {result.execution_time:.2f}s")
    print(f"Shots used: {result.shots_used}")
    print(f"Manifest: {result.manifest_path}")
    print(f"Shot data: {result.shot_data_path}")

    # Calculate energy from observable expectations
    total_energy = 0.0
    print(f"\nHamiltonian term estimates:")
    print(f"{'Observable':<12} {'Expectation':<12} {'CI (95%)':<30}")
    print("-" * 60)

    for obs_str, obs_data in result.observables.items():
        exp_val = obs_data['expectation_value']
        ci = obs_data.get('ci_95', (None, None))
        total_energy += exp_val
        print(f"{obs_str:<12} {exp_val:>10.6f}  [{ci[0]:>7.4f}, {ci[1]:>7.4f}]")

    print(f"\n{'=' * 60}")
    print(f"Total H₂ Energy: {total_energy:.6f} Hartree")
    print(f"{'=' * 60}")

    print("\n⚠️  Note: Using placeholder Hamiltonian coefficients for smoke test.")
    print("   For production, update h2_hamiltonian_observables() with actual")
    print("   qubit-mapped coefficients from qiskit-nature.")

    print("\n" + "=" * 80)
    print("✅ C-T01 Chemistry Workstream Starter COMPLETED")
    print("   Phase 1 chemistry data drop generated!")
    print("=" * 80)

    # Next steps
    print("\nNext Steps:")
    print("  1. Compare energy to direct measurement baseline")
    print("  2. Compute SSR for Hamiltonian estimation")
    print("  3. Update with real H₂@STO-3G coefficients for validation")
    print("  4. Run comparative experiment with grouped Pauli measurements")

    return 0


if __name__ == "__main__":
    exit(main())
