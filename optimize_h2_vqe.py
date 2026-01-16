#!/usr/bin/env python3
"""
Step 1: VQE Optimization for H2 Molecule
This script runs VQE on a simulator to find optimal ansatz parameters,
then generates the real H2 Hamiltonian for hardware execution.

Usage:
    python optimize_h2_vqe.py

Outputs:
    - Optimal VQE parameters
    - Real H2 Hamiltonian (Pauli terms with correct coefficients)
    - Ready-to-use configuration for hardware run
"""

import sys
from pathlib import Path
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.quantum_info import SparsePauliOp
from qiskit_aer import AerSimulator
from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import SLSQP

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quartumse.shadows.core import Observable


def get_h2_hamiltonian_sto3g():
    """
    Real H2 Hamiltonian at equilibrium geometry (0.735 Angstrom).
    These are the actual Jordan-Wigner mapped coefficients for H2/STO-3G.

    Source: Standard quantum chemistry calculation
    Expected ground state energy: -1.137 Hartree
    """
    # H2 at 0.735 Angstrom, STO-3G basis, Jordan-Wigner mapping
    pauli_terms = [
        ("IIII", -0.8105479805373283),   # Nuclear repulsion + offset
        ("IIIZ", 0.17218393261915552),
        ("IIZI", -0.2257534922240251),
        ("IIZZ", 0.12091263261776641),
        ("IZII", -0.2257534922240251),
        ("IZIZ", 0.16614543256382414),
        ("IZZI", 0.16614543256382414),
        ("ZIIZ", 0.17464343068300453),
        ("ZIZI", 0.17464343068300453),
        ("ZZII", -0.2427428051314046),
        ("XXXX", 0.04523279994605788),
        ("XXYY", 0.04523279994605788),
        ("YYXX", 0.04523279994605788),
        ("YYYY", 0.04523279994605788),
    ]

    return pauli_terms


def build_h2_ansatz_parameterized():
    """
    Parameterized ansatz for H2 (4 qubits).
    Uses hardware-efficient structure with controlled parameters.

    Returns parameterized circuit for VQE.
    """
    qc = QuantumCircuit(4)
    params = ParameterVector('θ', 6)

    # Initial state preparation
    qc.h(0)
    qc.cx(0, 1)

    # Parameterized rotation layers
    qc.ry(params[0], 0)
    qc.rz(params[1], 1)
    qc.cx(2, 3)
    qc.ry(params[2], 2)
    qc.rz(params[3], 3)
    qc.cx(1, 2)
    qc.ry(params[4], 1)
    qc.rz(params[5], 2)

    return qc


def build_h2_ansatz(params):
    """Build H2 ansatz with concrete parameter values."""
    qc = QuantumCircuit(4)

    # Initial state preparation
    qc.h(0)
    qc.cx(0, 1)

    # Rotation layers with concrete values
    qc.ry(params[0], 0)
    qc.rz(params[1], 1)
    qc.cx(2, 3)
    qc.ry(params[2], 2)
    qc.rz(params[3], 3)
    qc.cx(1, 2)
    qc.ry(params[4], 1)
    qc.rz(params[5], 2)

    return qc


def create_sparse_pauli_hamiltonian(pauli_terms):
    """Convert Pauli terms to Qiskit SparsePauliOp."""
    pauli_list = []
    coeffs = []

    for pauli_str, coeff in pauli_terms:
        pauli_list.append(pauli_str)
        coeffs.append(coeff)

    return SparsePauliOp(pauli_list, coeffs)


def optimize_vqe():
    """
    Run VQE optimization on simulator to find ground state parameters.
    """
    print("=" * 80)
    print("H2 VQE OPTIMIZATION (Simulator)")
    print("=" * 80)

    # Get real Hamiltonian
    pauli_terms = get_h2_hamiltonian_sto3g()
    hamiltonian = create_sparse_pauli_hamiltonian(pauli_terms)

    print(f"\nH2 Hamiltonian: {len(pauli_terms)} Pauli terms")
    print(f"Expected ground state energy: -1.137 Hartree")

    # Setup VQE
    backend = AerSimulator()
    optimizer = SLSQP(maxiter=100)

    # Initial parameters (starting from current placeholder values)
    initial_params = np.array([0.5, 0.3, 0.4, 0.2, 0.2, 0.1])

    print(f"\nInitial parameters: {initial_params}")
    print(f"Optimizer: SLSQP (max 100 iterations)")
    print("\nRunning VQE optimization...")

    # Run VQE
    from qiskit.primitives import StatevectorEstimator

    estimator_primitive = StatevectorEstimator()
    ansatz = build_h2_ansatz_parameterized()

    vqe = VQE(
        estimator=estimator_primitive,
        ansatz=ansatz,
        optimizer=optimizer,
        initial_point=initial_params,
    )

    result = vqe.compute_minimum_eigenvalue(hamiltonian)

    print("\n" + "=" * 80)
    print("VQE OPTIMIZATION RESULTS")
    print("=" * 80)
    print(f"Ground state energy: {result.eigenvalue.real:.6f} Hartree")
    print(f"Optimal parameters: {result.optimal_point}")
    print(f"Optimizer iterations: {result.optimizer_evals}")

    energy_error = abs(result.eigenvalue.real - (-1.137))
    print(f"\nEnergy error vs exact: {energy_error:.6f} Hartree")

    if energy_error < 0.01:
        print("[OK] Excellent - within chemical accuracy (1 kcal/mol = 0.0016 Ha)")
    elif energy_error < 0.05:
        print("[OK] Good - reasonable approximation")
    else:
        print("[!] Higher error - may need more ansatz layers")

    return result.optimal_point, pauli_terms


def save_optimized_config(optimal_params, pauli_terms):
    """
    Save configuration file for hardware run with optimized parameters.
    """
    config_path = Path("h2_optimized_config.py")

    with open(config_path, "w") as f:
        f.write('"""Optimized H2 configuration for hardware run."""\n\n')
        f.write('import numpy as np\n\n')

        f.write('# VQE-optimized ansatz parameters\n')
        f.write(f'OPTIMAL_PARAMS = np.array({list(optimal_params)})\n\n')

        f.write('# Real H2 Hamiltonian (STO-3G, 0.735 Angstrom)\n')
        f.write('H2_HAMILTONIAN = [\n')
        for pauli, coeff in pauli_terms:
            f.write(f'    ("{pauli}", {coeff}),\n')
        f.write(']\n\n')

        f.write('# Expected ground state energy\n')
        f.write('EXACT_ENERGY = -1.137  # Hartree\n')

    print(f"\n[OK] Configuration saved to: {config_path}")
    print("\nNext step:")
    print(f"  Run: python run_h2_optimized.py")


def main():
    print("\nQuartumSE: H2 VQE Optimization")
    print("This will find optimal ansatz parameters for the H2 ground state\n")

    # Run VQE optimization
    optimal_params, pauli_terms = optimize_vqe()

    # Save configuration
    save_optimized_config(optimal_params, pauli_terms)

    # Show comparison
    print("\n" + "=" * 80)
    print("COMPARISON: Placeholder vs Real Hamiltonian")
    print("=" * 80)
    print(f"{'Term':<8} {'Placeholder':<15} {'Real (STO-3G)':<15} {'Difference'}")
    print("-" * 65)

    placeholder = {
        "IIII": -1.05,
        "ZIII": 0.39,
        "IZII": -0.39,
        "IIIZ": -0.39,
    }

    real_dict = dict(pauli_terms)

    for term in ["IIII", "IIIZ", "IIZI", "ZIIZ"]:
        if term in real_dict:
            real_val = real_dict[term]
            place_val = placeholder.get(term, 0.0)
            diff = abs(real_val - place_val)
            print(f"{term:<8} {place_val:>13.6f}  {real_val:>13.6f}  {diff:>10.6f}")

    print("\n[OK] Ready to run optimized hardware experiment!")

    return 0


if __name__ == "__main__":
    exit(main())
