"""
O-T01: Shot-Frugal QAOA for MAX-CUT-5

Experiment Overview:
- Solve MAX-CUT on 5-node ring graph
- QAOA with p ∈ {1, 2}
- Use classical shadows for cost function estimation
- Target: Compare variance with/without shadows

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


def create_ring_graph(n: int):
    """Create ring graph edges."""
    return [(i, (i + 1) % n) for i in range(n)]


def maxcut_cost_hamiltonian(edges: list):
    """
    Create MAX-CUT cost Hamiltonian.

    H = Σ_(i,j)∈E (1 - Z_i Z_j) / 2
    """
    observables = []
    for i, j in edges:
        # Pauli string for edge (i, j)
        num_qubits = max(max(edges, key=lambda e: max(e))) + 1
        pauli = ["I"] * num_qubits
        pauli[i] = "Z"
        pauli[j] = "Z"
        observables.append(Observable("".join(pauli), coefficient=-0.5))  # -Z_i Z_j / 2

    return observables


def qaoa_circuit(num_qubits: int, edges: list, params: np.ndarray, p: int) -> QuantumCircuit:
    """
    QAOA circuit for MAX-CUT.

    Args:
        num_qubits: Number of nodes
        edges: Graph edges
        params: Variational parameters [gamma_1, beta_1, ..., gamma_p, beta_p]
        p: QAOA depth

    Returns:
        QAOA circuit
    """
    qc = QuantumCircuit(num_qubits)

    # Initial state: |+⟩^n
    qc.h(range(num_qubits))

    # QAOA layers
    for layer in range(p):
        gamma = params[2 * layer]
        beta = params[2 * layer + 1]

        # Cost Hamiltonian: exp(-i γ H_C)
        for i, j in edges:
            qc.rzz(2 * gamma, i, j)

        # Mixer: exp(-i β H_M)
        for q in range(num_qubits):
            qc.rx(2 * beta, q)

    return qc


def run_experiment():
    """Run O-T01 starter."""
    print("=" * 80)
    print("O-T01: Shot-Frugal QAOA for MAX-CUT-5 (STARTER)")
    print("=" * 80)

    # Configuration
    backend = AerSimulator()
    n = 5
    p = 1
    shadow_size = 500

    # Create graph
    edges = create_ring_graph(n)
    print(f"\nGraph: Ring with {n} nodes")
    print(f"Edges: {edges}")

    # Cost Hamiltonian
    observables = maxcut_cost_hamiltonian(edges)
    print(f"\nCost observables: {len(observables)}")

    # Random QAOA parameters
    params = np.random.uniform(0, 2 * np.pi, 2 * p)
    print(f"QAOA parameters: {params}")

    # Create circuit
    circuit = qaoa_circuit(n, edges, params, p)
    print(f"\nCircuit depth: {circuit.depth()}")

    # Estimate cost with shadows
    shadow_config = ShadowConfig(shadow_size=shadow_size, random_seed=42)
    estimator = ShadowEstimator(backend=backend, shadow_config=shadow_config)

    result = estimator.estimate(circuit=circuit, observables=observables, save_manifest=True)

    # Compute cost
    cost = sum(result.observables[str(obs)]["expectation_value"] for obs in observables)
    cost += len(edges) / 2  # Constant offset

    print(f"\n{'=' * 60}")
    print(f"Estimated MAX-CUT cost: {cost:.4f}")
    print(f"Shadow size: {shadow_size}")
    print(f"Manifest: {result.manifest_path}")
    print(f"{'=' * 60}")

    print("\n[TODO] Implement QAOA optimization loop")
    print("[TODO] Compare shadow variance vs direct measurement")
    print("[TODO] Track optimizer convergence and shot usage")

    return result


if __name__ == "__main__":
    run_experiment()
