"""
C-T01: Shadow-VQE for H₂ @ STO-3G

Experiment Overview:
- Prepare H₂ molecule at equilibrium geometry (STO-3G basis)
- Run VQE with hardware-efficient ansatz (depth ≤ 2)
- Use classical shadows for Hamiltonian readout
- Target: Energy error ≤ 50 mHa (simulator), ≤ 80 mHa (IBM hardware)

Status: STARTER SCAFFOLD - Needs full implementation
"""

import sys
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from quartumse import ShadowEstimator
from quartumse.shadows import ShadowConfig
from quartumse.shadows.core import Observable


def create_h2_hamiltonian():
    """
    Create H₂ Hamiltonian in qubit representation.

    Returns:
        List of (coefficient, pauli_string) tuples
    """
    # TODO: Use qiskit-nature to generate H₂ Hamiltonian
    # Placeholder for H₂ @ STO-3G @ 0.735 Å
    # Real coefficients will come from qiskit_nature.second_q.mappers

    print("[WARNING] Using placeholder Hamiltonian. Integrate qiskit-nature for real H₂.")

    # Simplified 2-qubit Hamiltonian (example structure)
    hamiltonian = [
        (-1.0523, "II"),
        (0.3979, "ZI"),
        (-0.3979, "IZ"),
        (-0.0112, "ZZ"),
        (0.1809, "XX"),
    ]

    return hamiltonian


def hardware_efficient_ansatz(num_qubits: int, depth: int, params: np.ndarray) -> QuantumCircuit:
    """
    Hardware-efficient ansatz for VQE.

    Args:
        num_qubits: Number of qubits
        depth: Ansatz depth
        params: Variational parameters

    Returns:
        Parameterized circuit
    """
    qc = QuantumCircuit(num_qubits)

    param_idx = 0
    for d in range(depth):
        # Rotation layer
        for q in range(num_qubits):
            qc.ry(params[param_idx], q)
            param_idx += 1

        # Entangling layer
        for q in range(num_qubits - 1):
            qc.cx(q, q + 1)

    return qc


def run_experiment():
    """Run C-T01 starter experiment."""
    print("=" * 80)
    print("C-T01: Shadow-VQE for H₂ @ STO-3G (STARTER)")
    print("=" * 80)

    # Configuration
    backend = AerSimulator()
    num_qubits = 2  # H₂ in minimal basis requires 2 qubits after reduction
    ansatz_depth = 2
    shadow_size = 1000

    # Get Hamiltonian
    hamiltonian = create_h2_hamiltonian()
    observables = [Observable(pauli, coeff) for coeff, pauli in hamiltonian]

    print(f"\nHamiltonian terms: {len(observables)}")
    for obs in observables:
        print(f"  {obs}")

    # TODO: Implement VQE optimization loop
    # For now, just test shadow estimation on a random ansatz

    # Random parameters
    num_params = num_qubits * ansatz_depth
    params = np.random.uniform(-np.pi, np.pi, num_params)

    # Create ansatz circuit
    circuit = hardware_efficient_ansatz(num_qubits, ansatz_depth, params)
    print(f"\nAnsatz circuit:\n{circuit}")

    # Estimate energy with shadows
    shadow_config = ShadowConfig(shadow_size=shadow_size, random_seed=42)
    estimator = ShadowEstimator(backend=backend, shadow_config=shadow_config)

    result = estimator.estimate(circuit=circuit, observables=observables, save_manifest=True)

    # Compute total energy
    energy = sum(
        result.observables[str(obs)]["expectation_value"] for obs in observables
    )

    print(f"\n{'=' * 60}")
    print(f"Estimated Energy: {energy:.6f} Ha")
    print(f"Shadow size: {shadow_size}")
    print(f"Manifest: {result.manifest_path}")
    print(f"{'=' * 60}")

    print("\n[TODO] Implement full VQE optimization loop")
    print("[TODO] Compare to exact energy and compute error")
    print("[TODO] Compare shadow readout vs grouped Pauli measurement")

    return result


if __name__ == "__main__":
    run_experiment()
