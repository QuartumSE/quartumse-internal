"""Quantum hardware timing model for estimating real-device execution time.

Provides conservative wall-clock time estimates for quantum circuits
based on hardware timing profiles (gate times, measurement, reset).
Separate from CostModel in cost_normalized.py which computes abstract
cost penalties for protocol comparison.
"""

from __future__ import annotations

from dataclasses import dataclass

from qiskit import QuantumCircuit


@dataclass
class HardwareTimingProfile:
    """Timing characteristics of a quantum hardware backend.

    Attributes:
        profile_id: Unique identifier for this profile.
        gate_1q_ns: Single-qubit gate time in nanoseconds.
        gate_2q_ns: Two-qubit gate time in nanoseconds.
        measurement_ns: Measurement time in nanoseconds.
        reset_ns: Qubit reset time in nanoseconds.
    """

    profile_id: str
    gate_1q_ns: float = 60.0
    gate_2q_ns: float = 300.0
    measurement_ns: float = 1500.0
    reset_ns: float = 1000.0


# Pre-defined profiles
IBM_HERON = HardwareTimingProfile(profile_id="ibm_heron_r2")


@dataclass
class CircuitTimingInfo:
    """Extracted timing-relevant properties from a quantum circuit.

    Attributes:
        depth: Circuit depth (number of layers).
        n_qubits: Number of qubits.
        gate_count_1q: Number of single-qubit gates.
        gate_count_2q: Number of two-qubit gates.
    """

    depth: int
    n_qubits: int
    gate_count_1q: int
    gate_count_2q: int


def extract_circuit_timing_info(circuit: QuantumCircuit) -> CircuitTimingInfo:
    """Extract timing-relevant info from a Qiskit QuantumCircuit.

    Args:
        circuit: The quantum circuit to analyze.

    Returns:
        CircuitTimingInfo with gate counts and depth.
    """
    gate_count_1q = 0
    gate_count_2q = 0

    for instruction in circuit.data:
        n_qubits_in_gate = len(instruction.qubits)
        if n_qubits_in_gate == 1:
            gate_count_1q += 1
        elif n_qubits_in_gate >= 2:
            gate_count_2q += 1

    return CircuitTimingInfo(
        depth=circuit.depth(),
        n_qubits=circuit.num_qubits,
        gate_count_1q=gate_count_1q,
        gate_count_2q=gate_count_2q,
    )


def estimate_quantum_hw_time(
    circuit_info: CircuitTimingInfo,
    n_shots: int,
    n_settings: int = 1,
    hw_profile: HardwareTimingProfile = IBM_HERON,
) -> float:
    """Estimate wall-clock time on quantum hardware.

    Conservative model: every layer uses the 2Q gate time (longest gate).
    Per-shot time = depth * gate_2q_ns + measurement_ns + reset_ns.
    Total = n_shots * n_settings * per_shot_time (in seconds).

    Args:
        circuit_info: Extracted circuit timing info.
        n_shots: Number of shots per setting.
        n_settings: Number of measurement settings.
        hw_profile: Hardware timing profile to use.

    Returns:
        Estimated total execution time in seconds.
    """
    per_shot_ns = (
        circuit_info.depth * hw_profile.gate_2q_ns
        + hw_profile.measurement_ns
        + hw_profile.reset_ns
    )
    total_ns = per_shot_ns * n_shots * n_settings
    return total_ns * 1e-9
