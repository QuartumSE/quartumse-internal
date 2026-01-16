#!/usr/bin/env python3
"""
Step 2: Run Optimized H2 Experiment on IBM Hardware
Uses VQE-optimized parameters and real H2 Hamiltonian.

Prerequisites:
    1. Run optimize_h2_vqe.py first
    2. Ensure QISKIT_IBM_TOKEN is set in .env

Usage:
    python run_h2_optimized.py
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


def load_optimized_config():
    """Load optimized parameters from VQE run."""
    try:
        import h2_optimized_config as config
        return config.OPTIMAL_PARAMS, config.H2_HAMILTONIAN, config.EXACT_ENERGY
    except ImportError:
        print("ERROR: Run optimize_h2_vqe.py first to generate optimized config")
        sys.exit(1)


def build_optimized_ansatz(params):
    """Build H2 ansatz with optimized parameters."""
    qc = QuantumCircuit(4)

    # Initial state preparation
    qc.h(0)
    qc.cx(0, 1)

    # Optimized rotation layers
    qc.ry(params[0], 0)
    qc.rz(params[1], 1)
    qc.cx(2, 3)
    qc.ry(params[2], 2)
    qc.rz(params[3], 3)
    qc.cx(1, 2)
    qc.ry(params[4], 1)
    qc.rz(params[5], 2)

    return qc


def main():
    backend_name = "ibm_fez"  # or "ibm_torino", "ibm_brisbane", etc.

    print("=" * 80)
    print("QuartumSE: OPTIMIZED H2 Experiment on IBM Hardware")
    print("=" * 80)

    # Load optimized configuration
    print("\nLoading VQE-optimized configuration...")
    optimal_params, h2_hamiltonian, exact_energy = load_optimized_config()

    print(f"Optimal parameters: {optimal_params}")
    print(f"Real H2 Hamiltonian: {len(h2_hamiltonian)} Pauli terms")
    print(f"Expected energy: {exact_energy:.6f} Hartree")

    # Build optimized circuit
    circuit = build_optimized_ansatz(optimal_params)
    print(f"\nCircuit: H2 ansatz (4 qubits, VQE-optimized)")
    print(f"Depth: {circuit.depth()}")
    print(f"Gate count: {circuit.count_ops()}")

    # Convert to observables
    observables = [Observable(pauli, coeff) for pauli, coeff in h2_hamiltonian]
    print(f"\nHamiltonian terms: {len(observables)} Pauli observables")
    print("Sample terms (first 5):")
    for obs in observables[:5]:
        print(f"  {obs}")

    # Configuration
    shadow_size = 500  # Increased for better accuracy with real Hamiltonian
    mem_shots = 256     # More calibration shots for better mitigation

    print(f"\nBackend: ibm:{backend_name}")
    print(f"Shadow version: v1 (noise-aware + MEM)")
    print(f"Shadow size: {shadow_size} (increased for real Hamiltonian)")
    print(f"MEM calibration shots: {mem_shots}")

    # Create estimator
    print("\n" + "=" * 80)
    print("PHASE 1: MEM Calibration")
    print("=" * 80)
    print("Calibrating measurement error mitigation...")

    estimator = ShadowEstimator(
        backend=f"ibm:{backend_name}",
        shadow_config=ShadowConfig(
            version=ShadowVersion.V1_NOISE_AWARE,
            shadow_size=shadow_size,
            random_seed=42,  # Different seed from placeholder run
            apply_inverse_channel=True,
        ),
        mitigation_config=MitigationConfig(
            techniques=[],
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
    print(f"\nHamiltonian term estimates (first 10):")
    print(f"{'Observable':<12} {'Expectation':<12} {'CI (95%)':<30}")
    print("-" * 60)

    for i, (obs_str, obs_data) in enumerate(result.observables.items()):
        exp_val = obs_data['expectation_value']
        ci = obs_data.get('ci_95', (None, None))
        total_energy += exp_val

        if i < 10:  # Show first 10
            print(f"{obs_str:<12} {exp_val:>10.6f}  [{ci[0]:>7.4f}, {ci[1]:>7.4f}]")

    print(f"\n{'=' * 60}")
    print(f"Measured H2 Energy:  {total_energy:.6f} Hartree")
    print(f"Expected (exact):    {exact_energy:.6f} Hartree")
    print(f"Error:               {abs(total_energy - exact_energy):.6f} Hartree")
    print(f"{'=' * 60}")

    # Energy accuracy assessment
    error_hartree = abs(total_energy - exact_energy)
    error_kcal = error_hartree * 627.5  # Convert to kcal/mol

    print(f"\nError: {error_hartree:.6f} Ha = {error_kcal:.2f} kcal/mol")

    if error_kcal < 1.0:
        print("✅ EXCELLENT - Within chemical accuracy (1 kcal/mol)!")
    elif error_kcal < 5.0:
        print("✅ GOOD - Reasonable quantum chemistry accuracy")
    else:
        print("⚠️  Higher error - hardware noise significant")

    print("\n" + "=" * 80)
    print("[OK] OPTIMIZED H2 Experiment COMPLETED")
    print("   Real Hamiltonian + VQE-optimized ansatz!")
    print("=" * 80)

    # Comparison
    print("\nWhat Changed from Placeholder Run:")
    print("  1. Real H2 Hamiltonian coefficients (from quantum chemistry)")
    print("  2. VQE-optimized ansatz parameters (ground state tuned)")
    print("  3. Increased shadow size (500 vs 300) for better accuracy")
    print("  4. More MEM calibration shots (256 vs 128)")

    print("\nNext Steps:")
    print("  1. Compare to baseline grouped Pauli measurement")
    print("  2. Compute rigorous SSR with error analysis")
    print("  3. Run multiple trials for statistical significance")
    print("  4. Analyze observable-by-observable performance")

    return 0


if __name__ == "__main__":
    exit(main())
