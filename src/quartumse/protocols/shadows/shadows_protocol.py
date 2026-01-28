"""Classical Shadows Protocol wrappers (Measurements Bible §4.2D-E).

This module wraps the classical shadows implementations as Protocol ABC
implementations, enabling unified benchmarking against direct measurement
baselines using the same task evaluation infrastructure.

Supported variants:
- ShadowsV0Protocol: Random local Clifford shadows (§4.2D)
- ShadowsV1Protocol: Noise-aware shadows with MEM (extension)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from ...observables import ObservableSet
from ...shadows import NoiseAwareRandomLocalCliffordShadows, RandomLocalCliffordShadows
from ...shadows.config import ShadowConfig
from ...shadows.core import Observable as ShadowObservable
from ..base import StaticProtocol
from ..registry import register_protocol
from ..state import (
    CIMethod,
    CIResult,
    Estimates,
    MeasurementPlan,
    MeasurementSetting,
    ObservableEstimate,
    ProtocolState,
    RawDatasetChunk,
)


@dataclass
class ShadowsProtocolState(ProtocolState):
    """State for classical shadows protocol.

    Additional attributes:
        shadow_config: Configuration for shadows implementation.
        measurement_bases: Per-shot basis choices (n_shots x n_qubits).
        measurement_outcomes: Per-shot outcomes (n_shots x n_qubits).
        shadows_impl: The underlying shadows implementation instance.
    """

    shadow_config: ShadowConfig | None = None
    measurement_bases: np.ndarray | None = None
    measurement_outcomes: np.ndarray | None = None
    shadows_impl: Any = None  # ClassicalShadows instance


class ClassicalShadowsProtocol(StaticProtocol):
    """Base class for classical shadows as a Protocol.

    This wraps the ClassicalShadows implementations to conform to
    the Protocol ABC, enabling use with the benchmarking tasks.

    Subclasses specify which shadows variant to use (v0, v1, etc.).
    """

    protocol_id: str = "classical_shadows"
    protocol_version: str = "1.0.0"

    def __init__(
        self,
        shadow_config: ShadowConfig | None = None,
        median_of_means: bool = False,
        num_groups: int = 10,
    ) -> None:
        """Initialize shadows protocol.

        Args:
            shadow_config: Configuration for shadows (uses defaults if None).
            median_of_means: Whether to use median-of-means estimator.
            num_groups: Number of groups for median-of-means.
        """
        super().__init__()
        self.median_of_means = median_of_means
        self.num_groups = num_groups
        self._base_config = shadow_config

    def _create_shadows_impl(
        self,
        n_shots: int,
        seed: int,
    ) -> RandomLocalCliffordShadows:
        """Create the underlying shadows implementation.

        Subclasses override to return v0, v1, etc.
        """
        config = ShadowConfig(
            num_shadows=n_shots,
            random_seed=seed,
            median_of_means=self.median_of_means,
            num_groups=self.num_groups,
            confidence_level=self.config.confidence_level,
        )
        return RandomLocalCliffordShadows(config)

    def initialize(
        self,
        observable_set: ObservableSet,
        total_budget: int,
        seed: int,
    ) -> ShadowsProtocolState:
        """Initialize protocol state.

        Args:
            observable_set: Set of observables to estimate.
            total_budget: Total number of shots (= shadow size).
            seed: Random seed for reproducibility.

        Returns:
            Initialized ShadowsProtocolState.
        """
        # Create shadows implementation
        shadows_impl = self._create_shadows_impl(total_budget, seed)

        return ShadowsProtocolState(
            observable_set=observable_set,
            total_budget=total_budget,
            remaining_budget=total_budget,
            seed=seed,
            n_rounds=0,
            shadows_impl=shadows_impl,
            metadata={"protocol_id": self.protocol_id},
        )

    def plan(self, state: ProtocolState) -> MeasurementPlan:
        """Generate measurement plan for shadows.

        For shadows, we create a single "setting" that represents
        the random basis measurement protocol. The actual basis
        choices are generated during acquisition.

        Args:
            state: Current protocol state.

        Returns:
            MeasurementPlan with shadow measurement specification.
        """
        shadows_state = state
        if not isinstance(shadows_state, ShadowsProtocolState):
            raise TypeError("Expected ShadowsProtocolState")

        n_qubits = shadows_state.observable_set.n_qubits
        n_shots = shadows_state.total_budget

        # Create a single setting representing the shadows protocol
        # (basis choices are random per-shot)
        setting = MeasurementSetting(
            setting_id="shadows_random_local_clifford",
            measurement_basis="random",  # Indicates random basis selection
            target_qubits=list(range(n_qubits)),
            metadata={
                "protocol": "classical_shadows",
                "ensemble": "random_local_clifford",
            },
        )

        # Map all observables to this single setting
        observable_setting_map = {
            obs.observable_id: [0] for obs in shadows_state.observable_set.observables
        }

        return MeasurementPlan(
            settings=[setting],
            shots_per_setting=[n_shots],
            observable_setting_map=observable_setting_map,
            metadata={
                "shadow_size": n_shots,
                "n_qubits": n_qubits,
                "protocol_id": self.protocol_id,
            },
        )

    def acquire(
        self,
        circuit: QuantumCircuit,
        plan: MeasurementPlan,
        backend: AerSimulator | Any,
        seed: int,
    ) -> RawDatasetChunk:
        """Execute shadow measurements.

        Generates random basis circuits, executes them, and returns
        the measurement outcomes along with basis choices.

        Args:
            circuit: State preparation circuit.
            plan: Measurement plan.
            backend: Quantum backend for execution.
            seed: Random seed.

        Returns:
            RawDatasetChunk with shadow measurement data.
        """
        n_shots = plan.total_shots
        n_qubits = circuit.num_qubits

        # Generate random basis choices
        rng = np.random.default_rng(seed)
        measurement_bases = rng.integers(0, 3, size=(n_shots, n_qubits))

        # Simulate measurements
        # In ideal case, sample from statevector probabilities
        measurement_outcomes = self._simulate_shadow_measurements(circuit, measurement_bases, rng)

        # Store as bitstrings for compatibility with Protocol interface
        bitstrings = {}
        setting_bitstrings = []
        for i in range(n_shots):
            # Convert outcome array to bitstring
            bs = "".join(str(measurement_outcomes[i, q]) for q in range(n_qubits))
            setting_bitstrings.append(bs)

        bitstrings["shadows_random_local_clifford"] = setting_bitstrings

        return RawDatasetChunk(
            bitstrings=bitstrings,
            settings_executed=["shadows_random_local_clifford"],
            n_qubits=n_qubits,
            metadata={
                "measurement_bases": measurement_bases,
                "n_shots": n_shots,
            },
        )

    def _simulate_shadow_measurements(
        self,
        circuit: QuantumCircuit,
        measurement_bases: np.ndarray,
        rng: np.random.Generator,
    ) -> np.ndarray:
        """Simulate shadow measurements with random bases.

        For ideal simulation, we sample from the rotated statevector
        probabilities. Each shot uses a different random basis.

        Args:
            circuit: State preparation circuit.
            measurement_bases: Shape (n_shots, n_qubits), values in {0,1,2}.
            rng: Random number generator.

        Returns:
            Measurement outcomes array, shape (n_shots, n_qubits).
        """
        from qiskit.quantum_info import Statevector

        n_shots, n_qubits = measurement_bases.shape

        # Get statevector
        Statevector.from_instruction(circuit)

        outcomes = np.zeros((n_shots, n_qubits), dtype=int)

        for shot_idx in range(n_shots):
            # For each shot, apply basis rotations and measure
            # This is done by computing conditional probabilities
            bases = measurement_bases[shot_idx]

            # Create rotated circuit
            rotated_circuit = circuit.copy()
            for q in range(n_qubits):
                basis = bases[q]
                if basis == 1:  # X basis: apply H before measurement
                    rotated_circuit.h(q)
                elif basis == 2:  # Y basis: apply S^dag H before measurement
                    rotated_circuit.sdg(q)
                    rotated_circuit.h(q)
                # basis == 0: Z basis, no rotation needed

            # Get statevector after rotations
            rotated_sv = Statevector.from_instruction(rotated_circuit)
            probs = rotated_sv.probabilities()

            # Sample outcome
            outcome_int = rng.choice(len(probs), p=probs)

            # Convert to per-qubit outcomes
            for q in range(n_qubits):
                outcomes[shot_idx, q] = (outcome_int >> q) & 1

        return outcomes

    def update(
        self,
        state: ProtocolState,
        data_chunk: RawDatasetChunk,
    ) -> ProtocolState:
        """Update state with measurement data.

        Stores the measurement outcomes and bases for later estimation.

        Args:
            state: Current protocol state.
            data_chunk: New measurement data.

        Returns:
            Updated protocol state.
        """
        shadows_state = state
        if not isinstance(shadows_state, ShadowsProtocolState):
            raise TypeError("Expected ShadowsProtocolState")

        # Extract measurement data
        n_qubits = data_chunk.n_qubits
        bitstrings = data_chunk.bitstrings.get("shadows_random_local_clifford", [])
        n_shots = len(bitstrings)

        # Convert bitstrings back to array
        outcomes = np.zeros((n_shots, n_qubits), dtype=int)
        for i, bs in enumerate(bitstrings):
            for q, c in enumerate(bs):
                outcomes[i, q] = int(c)

        # Get bases from metadata
        bases = data_chunk.metadata.get("measurement_bases")
        if bases is None:
            raise ValueError("Missing measurement_bases in chunk metadata")

        # Store in state
        shadows_state.measurement_outcomes = outcomes
        shadows_state.measurement_bases = bases

        # Also store in the shadows implementation
        if shadows_state.shadows_impl is not None:
            shadows_state.shadows_impl.reconstruct_classical_shadow(outcomes, bases)

        # Update budget tracking
        shadows_state.remaining_budget -= n_shots
        shadows_state.n_rounds += 1

        return shadows_state

    def finalize(
        self,
        state: ProtocolState,
        observable_set: ObservableSet,
    ) -> Estimates:
        """Compute final estimates from shadow data.

        Uses the shadows implementation to estimate each observable.

        Args:
            state: Final protocol state with shadow data.
            observable_set: Set of observables to estimate.

        Returns:
            Estimates for all observables.
        """
        shadows_state = state
        if not isinstance(shadows_state, ShadowsProtocolState):
            raise TypeError("Expected ShadowsProtocolState")

        shadows_impl = shadows_state.shadows_impl
        if shadows_impl is None:
            raise ValueError("Shadows implementation not initialized")

        estimates = []
        n_shots = shadows_state.total_budget - shadows_state.remaining_budget

        for obs in observable_set.observables:
            # Create shadow observable
            shadow_obs = ShadowObservable(
                pauli_string=obs.pauli_string,
                coefficient=obs.coefficient,
            )

            # Get estimate from shadows implementation
            shadow_estimate = shadows_impl.estimate_observable(shadow_obs)

            # Compute SE from variance
            variance = shadow_estimate.variance
            se = np.sqrt(variance / n_shots) if variance > 0 and n_shots > 0 else 0.0

            # Create CI if available
            ci_result = None
            if shadow_estimate.confidence_interval:
                ci_low, ci_high = shadow_estimate.confidence_interval
                ci_result = CIResult(
                    ci_low_raw=ci_low,
                    ci_high_raw=ci_high,
                    ci_low=max(ci_low, -1.0),
                    ci_high=min(ci_high, 1.0),
                    confidence_level=self.config.confidence_level,
                    method=CIMethod.NORMAL,
                    clamped=ci_low < -1.0 or ci_high > 1.0,
                )

            estimate = ObservableEstimate(
                observable_id=obs.observable_id,
                estimate=shadow_estimate.expectation_value,
                se=se,
                n_shots=n_shots,
                n_settings=1,  # Shadows use single "setting" conceptually
                ci=ci_result,
                variance=variance,
                metadata={
                    "method": "classical_shadows",
                    "shadow_size": shadow_estimate.shadow_size,
                },
            )
            estimates.append(estimate)

        return Estimates(
            estimates=estimates,
            total_shots=n_shots,
            n_settings=1,
            protocol_id=self.protocol_id,
            protocol_version=self.protocol_version,
            metadata={
                "shadow_size": n_shots,
                "median_of_means": self.median_of_means,
            },
        )


@register_protocol
class ShadowsV0Protocol(ClassicalShadowsProtocol):
    """Classical Shadows v0: Random Local Clifford (§4.2D).

    This implements the standard classical shadows protocol from
    Huang, Kueng, Preskill (2020).

    Properties:
    - Random single-qubit Clifford rotations (X, Y, Z bases)
    - Inverse channel reconstruction: rho_hat = 3|b><b| - I
    - Variance bound: 4^k / M for weight-k Pauli observables
    """

    protocol_id: str = "classical_shadows_v0"
    protocol_version: str = "1.0.0"

    def _create_shadows_impl(
        self,
        n_shots: int,
        seed: int,
    ) -> RandomLocalCliffordShadows:
        """Create v0 (random local Clifford) shadows implementation."""
        config = ShadowConfig(
            num_shadows=n_shots,
            random_seed=seed,
            median_of_means=self.median_of_means,
            num_groups=self.num_groups,
            confidence_level=self.config.confidence_level,
        )
        return RandomLocalCliffordShadows(config)


@register_protocol
class ShadowsV1Protocol(ClassicalShadowsProtocol):
    """Classical Shadows v1: Noise-Aware with MEM.

    This extends v0 with measurement error mitigation (MEM) to
    correct for readout errors using calibration data.
    """

    protocol_id: str = "classical_shadows_v1"
    protocol_version: str = "1.0.0"

    def __init__(
        self,
        shadow_config: ShadowConfig | None = None,
        median_of_means: bool = False,
        num_groups: int = 10,
        confusion_matrices: np.ndarray | None = None,
    ) -> None:
        """Initialize noise-aware shadows protocol.

        Args:
            shadow_config: Configuration for shadows.
            median_of_means: Whether to use median-of-means estimator.
            num_groups: Number of groups for median-of-means.
            confusion_matrices: Per-qubit confusion matrices for MEM.
        """
        super().__init__(shadow_config, median_of_means, num_groups)
        self.confusion_matrices = confusion_matrices

    def _create_shadows_impl(
        self,
        n_shots: int,
        seed: int,
    ) -> NoiseAwareRandomLocalCliffordShadows:
        """Create v1 (noise-aware) shadows implementation."""
        config = ShadowConfig(
            num_shadows=n_shots,
            random_seed=seed,
            median_of_means=self.median_of_means,
            num_groups=self.num_groups,
            confidence_level=self.config.confidence_level,
        )
        impl = NoiseAwareRandomLocalCliffordShadows(config)

        # Set confusion matrices if provided
        if self.confusion_matrices is not None:
            impl.set_confusion_matrices(self.confusion_matrices)

        return impl
