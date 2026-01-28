"""Direct Naive baseline protocol (Measurements Bible §4.1A).

This protocol measures each observable independently in its native basis,
allocating N/M shots uniformly across M observables. It serves as the
simplest baseline that any reasonable protocol should outperform.

Shot allocation: N/M shots per observable (uniform).
Measurement basis: Native Pauli basis for each observable.
Expected scaling: O(M) measurement settings.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ...observables import ObservableSet
from ..base import StaticProtocol
from ..registry import register_protocol
from ..state import (
    Estimates,
    MeasurementPlan,
    MeasurementSetting,
    ObservableEstimate,
    ProtocolState,
    RawDatasetChunk,
)


@dataclass
class DirectNaiveState(ProtocolState):
    """State for DirectNaive protocol.

    Additional attributes:
        shots_per_observable: Number of shots allocated per observable.
        observable_bitstrings: Collected bitstrings for each observable.
    """

    shots_per_observable: int = 0
    observable_bitstrings: dict[str, list[str]] = field(default_factory=dict)


@register_protocol
class DirectNaiveProtocol(StaticProtocol):
    """Direct measurement without grouping (§4.1A).

    Each observable is measured independently in its native basis.
    This is the simplest possible approach and serves as a baseline.

    Attributes:
        protocol_id: "direct_naive"
        protocol_version: "1.0.0"
    """

    protocol_id: str = "direct_naive"
    protocol_version: str = "1.0.0"

    def initialize(
        self,
        observable_set: ObservableSet,
        total_budget: int,
        seed: int,
    ) -> DirectNaiveState:
        """Initialize protocol state.

        Args:
            observable_set: Set of observables to estimate.
            total_budget: Total number of shots available.
            seed: Random seed for reproducibility.

        Returns:
            Initialized DirectNaiveState.
        """
        M = len(observable_set)
        # Ensure at least 1 shot per observable (if budget allows)
        shots_per_observable = max(1, total_budget // M) if M > 0 else 0

        # Initialize storage for each observable
        observable_bitstrings = {obs.observable_id: [] for obs in observable_set.observables}

        return DirectNaiveState(
            observable_set=observable_set,
            total_budget=total_budget,
            remaining_budget=total_budget,
            seed=seed,
            n_rounds=0,
            shots_per_observable=shots_per_observable,
            observable_bitstrings=observable_bitstrings,
            metadata={"protocol_id": self.protocol_id},
        )

    def plan(
        self,
        state: ProtocolState,
    ) -> MeasurementPlan:
        """Generate measurement plan for all observables.

        Each observable gets its own measurement setting in its native basis.

        Args:
            state: Current protocol state.

        Returns:
            MeasurementPlan with M settings, one per observable.
        """
        direct_state = state
        if not isinstance(direct_state, DirectNaiveState):
            raise TypeError("Expected DirectNaiveState")

        settings = []
        shots_per_setting = []
        observable_setting_map: dict[str, list[int]] = {}

        for i, obs in enumerate(state.observable_set.observables):
            # Native measurement basis is the Pauli string with I -> Z
            basis = obs.pauli_string.replace("I", "Z")

            setting = MeasurementSetting(
                setting_id=f"setting_{i}",
                measurement_basis=basis,
                target_qubits=list(range(obs.n_qubits)),
                metadata={"observable_id": obs.observable_id},
            )
            settings.append(setting)
            shots_per_setting.append(direct_state.shots_per_observable)
            observable_setting_map[obs.observable_id] = [i]

        return MeasurementPlan(
            settings=settings,
            shots_per_setting=shots_per_setting,
            observable_setting_map=observable_setting_map,
            metadata={"n_observables": len(state.observable_set)},
        )

    def update(
        self,
        state: ProtocolState,
        data_chunk: RawDatasetChunk,
    ) -> ProtocolState:
        """Update state with new measurement data.

        Args:
            state: Current protocol state.
            data_chunk: New measurement data.

        Returns:
            Updated protocol state.
        """
        direct_state = state
        if not isinstance(direct_state, DirectNaiveState):
            raise TypeError("Expected DirectNaiveState")

        # Store bitstrings for each setting
        for setting_id, bitstrings in data_chunk.bitstrings.items():
            # Find which observable this setting corresponds to
            setting_idx = int(setting_id.split("_")[1])
            obs = direct_state.observable_set.observables[setting_idx]
            direct_state.observable_bitstrings[obs.observable_id].extend(bitstrings)

        # Update budget tracking
        total_new_shots = sum(len(bs) for bs in data_chunk.bitstrings.values())
        direct_state.remaining_budget -= total_new_shots
        direct_state.round_number += 1

        return direct_state

    def finalize(
        self,
        state: ProtocolState,
        observable_set: ObservableSet,
    ) -> Estimates:
        """Compute final estimates from collected data.

        Args:
            state: Final protocol state.
            observable_set: Set of observables (for reference).

        Returns:
            Estimates for all observables.
        """
        direct_state = state
        if not isinstance(direct_state, DirectNaiveState):
            raise TypeError("Expected DirectNaiveState")

        estimates = []

        for obs in observable_set.observables:
            bitstrings = direct_state.observable_bitstrings.get(obs.observable_id, [])

            if not bitstrings:
                # No data collected
                estimate = ObservableEstimate(
                    observable_id=obs.observable_id,
                    estimate=0.0,
                    se=float("inf"),
                    n_shots=0,
                    n_settings=0,
                )
            else:
                # Compute expectation value from bitstrings
                expectation, se = self._estimate_from_bitstrings(
                    bitstrings, obs.pauli_string, obs.coefficient
                )

                estimate = ObservableEstimate(
                    observable_id=obs.observable_id,
                    estimate=expectation,
                    se=se,
                    n_shots=len(bitstrings),
                    n_settings=1,
                )

            estimates.append(estimate)

        return Estimates(
            estimates=estimates,
            protocol_id=self.protocol_id,
            protocol_version=self.protocol_version,
            total_shots=state.total_budget - state.remaining_budget,
            metadata={"n_observables": len(observable_set)},
        )

    def _estimate_from_bitstrings(
        self,
        bitstrings: list[str],
        pauli_string: str,
        coefficient: float,
    ) -> tuple[float, float]:
        """Estimate expectation value from measurement bitstrings.

        For a Pauli string P = P_1 ⊗ P_2 ⊗ ... ⊗ P_n, the expectation
        value is estimated as the mean of (-1)^(parity) where parity
        counts the number of 1s on qubits where P_i ≠ I.

        Args:
            bitstrings: List of measurement outcome bitstrings.
            pauli_string: The Pauli operator being measured.
            coefficient: Observable coefficient.

        Returns:
            Tuple of (expectation value, standard error).
        """
        if not bitstrings:
            return 0.0, float("inf")

        # Get positions where we have non-identity Paulis
        support = [i for i, p in enumerate(pauli_string) if p != "I"]

        # Compute eigenvalues for each bitstring
        eigenvalues = []
        for bs in bitstrings:
            # Count parity on support qubits
            parity = sum(int(bs[i]) for i in support) % 2
            eigenvalues.append((-1) ** parity)

        # Compute mean and standard error
        eigenvalues_array = np.array(eigenvalues, dtype=float)
        mean = float(np.mean(eigenvalues_array)) * coefficient
        std = float(np.std(eigenvalues_array, ddof=1))
        se = std / np.sqrt(len(eigenvalues)) * abs(coefficient)

        return mean, se
