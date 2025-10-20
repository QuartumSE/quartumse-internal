"""
B-T01: Randomized Benchmarking with Provenance

Experiment Overview:
- 1-3 qubit Randomized Benchmarking (RB)
- Cross-Eye Benchmarking (XEB) on shallow random circuits
- Log results into provenance manifest
- Compare to IBM backend calibration metadata

Status: STARTER SCAFFOLD
"""

import sys
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import random_circuit
from qiskit_aer import AerSimulator

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


def randomized_benchmarking_sequence(num_qubits: int, sequence_length: int, seed: int) -> QuantumCircuit:
    """
    Generate RB sequence.

    Args:
        num_qubits: Number of qubits
        sequence_length: Number of Cliffords in sequence
        seed: Random seed

    Returns:
        RB circuit
    """
    # TODO: Implement proper Clifford RB
    # For now, use random circuit as placeholder
    rng = np.random.default_rng(seed)
    qc = QuantumCircuit(num_qubits)

    # Placeholder: random gates
    gates = ['h', 'x', 'y', 'z', 's', 'sdg']
    for _ in range(sequence_length):
        gate = rng.choice(gates)
        qubit = rng.integers(0, num_qubits)
        getattr(qc, gate)(qubit)

    return qc


def run_experiment():
    """Run B-T01 starter."""
    print("=" * 80)
    print("B-T01: Randomized Benchmarking (STARTER)")
    print("=" * 80)

    backend = AerSimulator()
    num_qubits = 2
    sequence_lengths = [1, 5, 10, 20, 50]
    num_trials = 10

    print(f"\nRB Configuration:")
    print(f"  Qubits: {num_qubits}")
    print(f"  Sequence lengths: {sequence_lengths}")
    print(f"  Trials per length: {num_trials}")

    survival_probs = []

    for seq_len in sequence_lengths:
        survives = 0
        for trial in range(num_trials):
            # Generate RB sequence
            qc = randomized_benchmarking_sequence(num_qubits, seq_len, seed=trial)
            qc.measure_all()

            # Run
            job = backend.run(qc, shots=1000)
            counts = job.result().get_counts()

            # Check survival probability (|00⟩ state)
            target_state = "0" * num_qubits
            survives += counts.get(target_state, 0)

        survival_prob = survives / (num_trials * 1000)
        survival_probs.append(survival_prob)
        print(f"  Length {seq_len:3d}: Survival = {survival_prob:.4f}")

    # Fit decay
    # P(survive) ≈ A * p^m + B, where p = (d-1)/d + eps * gate_error
    # TODO: Fit exponential decay to extract gate error

    print("\n[TODO] Fit RB decay curve to extract gate error rate")
    print("[TODO] Compare to backend calibration data")
    print("[TODO] Implement XEB benchmarking")
    print("[TODO] Store results in provenance manifest")

    return survival_probs


if __name__ == "__main__":
    run_experiment()
