"""Shot-based sampling backends for protocol execution.

This module provides samplers that execute measurement circuits and
return bitstring outcomes. Supports both ideal and noisy simulation.

For benchmarking, protocols use samplers to execute their measurement plans.
Ground truth is computed separately via StatevectorBackend.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator


@dataclass
class SamplingResult:
    """Result from sampling a circuit.

    Attributes:
        counts_data: Internal counts dictionary (bitstring -> count).
        n_shots: Number of shots sampled.
        metadata: Additional metadata (backend, timing).
    """

    counts_data: dict[str, int]
    n_shots: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def counts(self) -> dict[str, int]:
        """Return counts dictionary."""
        return self.counts_data.copy()

    @property
    def bitstrings(self) -> list[str]:
        """Lazily generate list of bitstrings from counts."""
        result = []
        for bitstring, count in self.counts_data.items():
            result.extend([bitstring] * count)
        return result


class Sampler(ABC):
    """Abstract base class for circuit samplers."""

    @abstractmethod
    def sample(
        self,
        circuit: QuantumCircuit,
        n_shots: int,
        seed: int | None = None,
    ) -> SamplingResult:
        """Sample from a circuit.

        Args:
            circuit: Circuit to sample (must include measurements).
            n_shots: Number of shots to sample.
            seed: Random seed for reproducibility.

        Returns:
            SamplingResult with bitstring outcomes.
        """
        ...


class IdealSampler(Sampler):
    """Ideal (noiseless) shot-based sampler.

    Uses Qiskit Aer simulator for exact probability sampling.
    """

    def __init__(self) -> None:
        """Initialize ideal sampler."""
        self._backend = AerSimulator(method="statevector")

    def sample(
        self,
        circuit: QuantumCircuit,
        n_shots: int,
        seed: int | None = None,
    ) -> SamplingResult:
        """Sample from circuit using ideal simulation.

        Args:
            circuit: Circuit with measurements.
            n_shots: Number of shots.
            seed: Random seed.

        Returns:
            SamplingResult with ideal sampling outcomes.
        """
        # Ensure circuit has measurements
        if circuit.num_clbits == 0:
            # Add measure_all if no measurements
            circuit = circuit.copy()
            circuit.measure_all()

        # Run simulation
        job = self._backend.run(circuit, shots=n_shots, seed_simulator=seed)
        result = job.result()
        counts = result.get_counts()

        return SamplingResult(
            counts_data=counts,
            n_shots=n_shots,
            metadata={"backend": "aer_statevector", "seed": seed},
        )


class NoisySampler(Sampler):
    """Noisy shot-based sampler with configurable noise model.

    Supports canonical noise profiles per Measurements Bible §9.4.
    """

    def __init__(
        self,
        noise_profile_id: str = "ideal",
        readout_error: float = 0.0,
        depol_1q: float = 0.0,
        depol_2q: float = 0.0,
    ) -> None:
        """Initialize noisy sampler.

        Args:
            noise_profile_id: Identifier for the noise profile.
            readout_error: Per-qubit readout error probability.
            depol_1q: Single-qubit depolarizing error rate.
            depol_2q: Two-qubit depolarizing error rate.
        """
        self.noise_profile_id = noise_profile_id
        self.readout_error = readout_error
        self.depol_1q = depol_1q
        self.depol_2q = depol_2q

        self._backend = AerSimulator()
        self._noise_model = self._build_noise_model()

    def _build_noise_model(self) -> Any:
        """Build Qiskit noise model from parameters."""
        if self.readout_error == 0 and self.depol_1q == 0 and self.depol_2q == 0:
            return None

        from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error

        noise_model = NoiseModel()

        # Add depolarizing errors
        if self.depol_1q > 0:
            error_1q = depolarizing_error(self.depol_1q, 1)
            noise_model.add_all_qubit_quantum_error(error_1q, ["h", "x", "y", "z", "s", "sdg"])

        if self.depol_2q > 0:
            error_2q = depolarizing_error(self.depol_2q, 2)
            noise_model.add_all_qubit_quantum_error(error_2q, ["cx", "cz"])

        # Add readout error
        if self.readout_error > 0:
            p = self.readout_error
            # Symmetric readout error: P(1|0) = P(0|1) = p
            readout_err = ReadoutError([[1 - p, p], [p, 1 - p]])
            noise_model.add_all_qubit_readout_error(readout_err)

        return noise_model

    def sample(
        self,
        circuit: QuantumCircuit,
        n_shots: int,
        seed: int | None = None,
    ) -> SamplingResult:
        """Sample from circuit with noise.

        Args:
            circuit: Circuit with measurements.
            n_shots: Number of shots.
            seed: Random seed.

        Returns:
            SamplingResult with noisy sampling outcomes.
        """
        # Ensure circuit has measurements
        if circuit.num_clbits == 0:
            circuit = circuit.copy()
            circuit.measure_all()

        # Run simulation with noise
        job = self._backend.run(
            circuit,
            shots=n_shots,
            seed_simulator=seed,
            noise_model=self._noise_model,
        )
        result = job.result()
        counts = result.get_counts()

        return SamplingResult(
            counts_data=counts,
            n_shots=n_shots,
            metadata={
                "backend": "aer_noisy",
                "noise_profile_id": self.noise_profile_id,
                "readout_error": self.readout_error,
                "depol_1q": self.depol_1q,
                "depol_2q": self.depol_2q,
                "seed": seed,
            },
        )


class StatevectorSampler(Sampler):
    """Direct statevector sampling without full Aer backend.

    Faster for ideal simulations of small circuits.
    """

    def sample(
        self,
        circuit: QuantumCircuit,
        n_shots: int,
        seed: int | None = None,
    ) -> SamplingResult:
        """Sample from circuit using statevector probabilities.

        Args:
            circuit: Circuit (measurements ignored, uses final state).
            n_shots: Number of shots.
            seed: Random seed.

        Returns:
            SamplingResult with sampled bitstrings.
        """
        # Remove measurements to get pure statevector
        circuit_no_meas = circuit.remove_final_measurements(inplace=False)

        # Get statevector
        sv = Statevector.from_instruction(circuit_no_meas)
        probs = sv.probabilities()

        # Sample from probabilities
        rng = np.random.default_rng(seed)
        n_qubits = circuit.num_qubits
        outcomes = rng.choice(len(probs), size=n_shots, p=probs)

        # Use numpy to count outcomes directly (vectorized)
        unique, counts_arr = np.unique(outcomes, return_counts=True)
        counts = {
            format(outcome, f"0{n_qubits}b"): int(count)
            for outcome, count in zip(unique, counts_arr, strict=False)
        }

        return SamplingResult(
            counts_data=counts,
            n_shots=n_shots,
            metadata={"backend": "statevector_sampling", "seed": seed},
        )


def sample_circuit(
    circuit: QuantumCircuit,
    n_shots: int,
    seed: int | None = None,
    noise_profile: str = "ideal",
    **noise_params: Any,
) -> SamplingResult:
    """Convenience function to sample from a circuit.

    Args:
        circuit: Circuit to sample.
        n_shots: Number of shots.
        seed: Random seed.
        noise_profile: "ideal" or "noisy".
        **noise_params: Parameters for noisy sampling.

    Returns:
        SamplingResult with bitstring outcomes.
    """
    if noise_profile == "ideal":
        sampler = IdealSampler()
    else:
        sampler = NoisySampler(noise_profile_id=noise_profile, **noise_params)

    return sampler.sample(circuit, n_shots, seed)
