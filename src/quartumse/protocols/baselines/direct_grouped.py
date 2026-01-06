"""Direct Grouped baseline protocol (Measurements Bible §4.1B).

This protocol groups commuting observables that share a measurement basis
and measures them simultaneously. It allocates shots uniformly across groups.

This is the REQUIRED baseline for defensible benchmarks per §4.1B:
"Any protocol claiming advantage must be compared against this baseline."

Shot allocation: N/G shots per group (uniform), where G = number of groups.
Measurement basis: Shared basis for each commuting group.
Expected scaling: O(G) measurement settings, where G ≤ M.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ...observables import (
    CommutingGroup,
    Observable,
    ObservableSet,
    partition_observable_set,
)
from ..base import StaticProtocol
from ..registry import register_protocol
from ..state import (
    CIResult,
    Estimates,
    MeasurementPlan,
    MeasurementSetting,
    ObservableEstimate,
    ProtocolState,
    RawDatasetChunk,
)


@dataclass
class DirectGroupedState(ProtocolState):
    """State for DirectGrouped protocol.

    Additional attributes:
        groups: List of CommutingGroup objects.
        shots_per_group: Number of shots allocated per group.
        group_bitstrings: Collected bitstrings for each group.
        grouping_method: Method used for grouping.
    """

    groups: list[CommutingGroup] = field(default_factory=list)
    shots_per_group: int = 0
    group_bitstrings: dict[str, list[str]] = field(default_factory=dict)
    grouping_method: str = "greedy"


@register_protocol
class DirectGroupedProtocol(StaticProtocol):
    """Direct measurement with commuting grouping (§4.1B).

    Observables are partitioned into qubit-wise commuting groups.
    Each group is measured in a shared basis.

    This is the REQUIRED baseline for defensible benchmarks.

    Attributes:
        protocol_id: "direct_grouped"
        protocol_version: "1.0.0"
        grouping_method: Method for partitioning ("greedy" or "sorted_insertion")
    """

    protocol_id: str = "direct_grouped"
    protocol_version: str = "1.0.0"
    grouping_method: str = "greedy"

    def __init__(self, grouping_method: str = "greedy") -> None:
        """Initialize protocol.

        Args:
            grouping_method: "greedy" or "sorted_insertion"
        """
        self.grouping_method = grouping_method

    def initialize(
        self,
        observable_set: ObservableSet,
        total_budget: int,
        seed: int,
    ) -> DirectGroupedState:
        """Initialize protocol state with commuting groups.

        Args:
            observable_set: Set of observables to estimate.
            total_budget: Total number of shots available.
            seed: Random seed for reproducibility.

        Returns:
            Initialized DirectGroupedState.
        """
        # Partition into commuting groups
        groups, stats = partition_observable_set(
            observable_set, method=self.grouping_method
        )

        G = len(groups)
        shots_per_group = total_budget // G if G > 0 else 0

        # Initialize storage for each group
        group_bitstrings = {g.group_id: [] for g in groups}

        return DirectGroupedState(
            observable_set=observable_set,
            total_budget=total_budget,
            remaining_budget=total_budget,
            seed=seed,
            round_number=0,
            groups=groups,
            shots_per_group=shots_per_group,
            group_bitstrings=group_bitstrings,
            grouping_method=self.grouping_method,
            metadata={
                "protocol_id": self.protocol_id,
                "n_groups": G,
                "grouping_stats": stats,
            },
        )

    def plan(
        self,
        state: ProtocolState,
    ) -> MeasurementPlan:
        """Generate measurement plan with one setting per group.

        Args:
            state: Current protocol state.

        Returns:
            MeasurementPlan with G settings, one per commuting group.
        """
        grouped_state = state
        if not isinstance(grouped_state, DirectGroupedState):
            raise TypeError("Expected DirectGroupedState")

        settings = []
        shots_per_setting = []
        observable_setting_map: dict[str, list[int]] = {}

        for i, group in enumerate(grouped_state.groups):
            setting = MeasurementSetting(
                setting_id=group.group_id,
                measurement_basis=group.measurement_basis,
                target_qubits=list(range(grouped_state.observable_set.n_qubits)),
                metadata={
                    "group_size": group.size,
                    "observable_ids": [obs.observable_id for obs in group.observables],
                },
            )
            settings.append(setting)
            shots_per_setting.append(grouped_state.shots_per_group)

            # Map each observable in this group to this setting
            for obs in group.observables:
                observable_setting_map[obs.observable_id] = [i]

        return MeasurementPlan(
            settings=settings,
            shots_per_setting=shots_per_setting,
            observable_setting_map=observable_setting_map,
            metadata={
                "n_groups": len(grouped_state.groups),
                "grouping_method": grouped_state.grouping_method,
            },
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
        grouped_state = state
        if not isinstance(grouped_state, DirectGroupedState):
            raise TypeError("Expected DirectGroupedState")

        # Store bitstrings for each group
        for setting_id, bitstrings in data_chunk.bitstrings.items():
            grouped_state.group_bitstrings[setting_id].extend(bitstrings)

        # Update budget tracking
        total_new_shots = sum(len(bs) for bs in data_chunk.bitstrings.values())
        grouped_state.remaining_budget -= total_new_shots
        grouped_state.round_number += 1

        return grouped_state

    def finalize(
        self,
        state: ProtocolState,
        observable_set: ObservableSet,
    ) -> Estimates:
        """Compute final estimates from collected data.

        For grouped measurements, each observable's estimate is computed
        from the same bitstrings as other observables in its group.

        Args:
            state: Final protocol state.
            observable_set: Set of observables (for reference).

        Returns:
            Estimates for all observables.
        """
        grouped_state = state
        if not isinstance(grouped_state, DirectGroupedState):
            raise TypeError("Expected DirectGroupedState")

        estimates = []

        # Build mapping from observable_id to group
        obs_to_group = {}
        for group in grouped_state.groups:
            for obs in group.observables:
                obs_to_group[obs.observable_id] = group

        for obs in observable_set.observables:
            group = obs_to_group.get(obs.observable_id)

            if group is None:
                estimate = ObservableEstimate(
                    observable_id=obs.observable_id,
                    estimate=0.0,
                    se=float("inf"),
                    n_shots=0,
                    n_settings=0,
                )
            else:
                bitstrings = grouped_state.group_bitstrings.get(group.group_id, [])

                if not bitstrings:
                    estimate = ObservableEstimate(
                        observable_id=obs.observable_id,
                        estimate=0.0,
                        se=float("inf"),
                        n_shots=0,
                        n_settings=1,
                    )
                else:
                    # Compute expectation value from shared bitstrings
                    expectation, se = self._estimate_from_bitstrings(
                        bitstrings,
                        obs.pauli_string,
                        group.measurement_basis,
                        obs.coefficient,
                    )

                    estimate = ObservableEstimate(
                        observable_id=obs.observable_id,
                        estimate=expectation,
                        se=se,
                        n_shots=len(bitstrings),
                        n_settings=1,
                        metadata={"group_id": group.group_id},
                    )

            estimates.append(estimate)

        return Estimates(
            estimates=estimates,
            protocol_id=self.protocol_id,
            protocol_version=self.protocol_version,
            total_shots=state.total_budget - state.remaining_budget,
            metadata={
                "n_groups": len(grouped_state.groups),
                "grouping_method": grouped_state.grouping_method,
            },
        )

    def _estimate_from_bitstrings(
        self,
        bitstrings: list[str],
        pauli_string: str,
        measurement_basis: str,
        coefficient: float,
    ) -> tuple[float, float]:
        """Estimate expectation value from grouped measurement bitstrings.

        When measuring in a shared basis, we need to consider which qubits
        are relevant for each observable. The eigenvalue for observable P
        is determined by the parity of outcomes on P's support.

        Args:
            bitstrings: List of measurement outcome bitstrings.
            pauli_string: The Pauli observable being estimated.
            measurement_basis: The shared measurement basis.
            coefficient: Observable coefficient.

        Returns:
            Tuple of (expectation value, standard error).
        """
        if not bitstrings:
            return 0.0, float("inf")

        # Get positions where the observable has non-identity operators
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
