"""Direct Optimized baseline protocol (Measurements Bible §4.1C).

This protocol extends DirectGrouped with optimal shot allocation across groups.
Rather than uniform allocation, it allocates shots proportionally to group
"cost" based on the number of observables in each group.

This represents the best achievable performance for direct measurement
approaches without using advanced techniques like classical shadows.

Shot allocation: Proportional to sqrt(group_size) * variance_estimate.
Measurement basis: Shared basis for each commuting group.
Expected scaling: O(G) measurement settings with optimal allocation.
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
class DirectOptimizedState(ProtocolState):
    """State for DirectOptimized protocol.

    Additional attributes:
        groups: List of CommutingGroup objects.
        shots_per_group: Optimally allocated shots per group.
        group_bitstrings: Collected bitstrings for each group.
        allocation_weights: Allocation weights for each group.
    """

    groups: list[CommutingGroup] = field(default_factory=list)
    shots_per_group: dict[str, int] = field(default_factory=dict)
    group_bitstrings: dict[str, list[str]] = field(default_factory=dict)
    allocation_weights: dict[str, float] = field(default_factory=dict)


@register_protocol
class DirectOptimizedProtocol(StaticProtocol):
    """Direct measurement with optimal shot allocation (§4.1C).

    This protocol:
    1. Groups observables into qubit-wise commuting families
    2. Allocates shots optimally based on group importance/size
    3. Uses a simple heuristic: more shots to larger groups

    The optimal allocation aims to minimize the worst-case SE across
    all observables, subject to the total shot budget constraint.

    Attributes:
        protocol_id: "direct_optimized"
        protocol_version: "1.0.0"
        allocation_strategy: Strategy for shot allocation
    """

    protocol_id: str = "direct_optimized"
    protocol_version: str = "1.0.0"
    allocation_strategy: str = "proportional"  # or "equal_se", "max_min"

    def __init__(self, allocation_strategy: str = "proportional") -> None:
        """Initialize protocol.

        Args:
            allocation_strategy: Strategy for allocating shots to groups.
                - "proportional": Proportional to sqrt(group_size)
                - "equal_se": Aim for equal SE across observables
                - "max_min": Maximize minimum shots per observable
        """
        self.allocation_strategy = allocation_strategy

    def initialize(
        self,
        observable_set: ObservableSet,
        total_budget: int,
        seed: int,
    ) -> DirectOptimizedState:
        """Initialize protocol state with optimal allocation.

        Args:
            observable_set: Set of observables to estimate.
            total_budget: Total number of shots available.
            seed: Random seed for reproducibility.

        Returns:
            Initialized DirectOptimizedState.
        """
        # Partition into commuting groups
        groups, stats = partition_observable_set(observable_set, method="greedy")

        # Compute optimal allocation
        shots_per_group, allocation_weights = self._compute_allocation(
            groups, total_budget
        )

        # Initialize storage
        group_bitstrings = {g.group_id: [] for g in groups}

        return DirectOptimizedState(
            observable_set=observable_set,
            total_budget=total_budget,
            remaining_budget=total_budget,
            seed=seed,
            n_rounds=0,
            groups=groups,
            shots_per_group=shots_per_group,
            group_bitstrings=group_bitstrings,
            allocation_weights=allocation_weights,
            metadata={
                "protocol_id": self.protocol_id,
                "n_groups": len(groups),
                "allocation_strategy": self.allocation_strategy,
                "grouping_stats": stats,
            },
        )

    def _compute_allocation(
        self,
        groups: list[CommutingGroup],
        total_budget: int,
    ) -> tuple[dict[str, int], dict[str, float]]:
        """Compute optimal shot allocation across groups.

        Args:
            groups: List of commuting groups.
            total_budget: Total shots available.

        Returns:
            Tuple of (shots_per_group dict, allocation_weights dict).
        """
        if not groups:
            return {}, {}

        weights = {}

        if self.allocation_strategy == "proportional":
            # Allocate proportionally to sqrt(group_size)
            # Rationale: larger groups benefit more from shared measurements
            for group in groups:
                weights[group.group_id] = np.sqrt(group.size)

        elif self.allocation_strategy == "equal_se":
            # Allocate to achieve approximately equal SE
            # SE ~ 1/sqrt(N), so N ~ 1/SE^2
            # For equal SE across groups with different sizes:
            # weight ~ sqrt(group_size) (same as proportional)
            for group in groups:
                weights[group.group_id] = np.sqrt(group.size)

        elif self.allocation_strategy == "max_min":
            # Maximize the minimum shots per observable
            # Each observable gets N_g / |G_g| effective shots
            # To equalize: N_g / |G_g| = constant
            # So N_g ~ |G_g| (group size)
            for group in groups:
                weights[group.group_id] = float(group.size)

        else:
            # Default to uniform
            for group in groups:
                weights[group.group_id] = 1.0

        # Normalize weights
        total_weight = sum(weights.values())
        for gid in weights:
            weights[gid] /= total_weight

        # Allocate shots
        shots_per_group = {}
        allocated = 0

        for group in groups[:-1]:  # All but last
            shots = int(weights[group.group_id] * total_budget)
            shots_per_group[group.group_id] = shots
            allocated += shots

        # Last group gets remainder to avoid rounding issues
        if groups:
            shots_per_group[groups[-1].group_id] = total_budget - allocated

        return shots_per_group, weights

    def plan(
        self,
        state: ProtocolState,
    ) -> MeasurementPlan:
        """Generate measurement plan with optimal allocation.

        Args:
            state: Current protocol state.

        Returns:
            MeasurementPlan with G settings and optimal shot distribution.
        """
        opt_state = state
        if not isinstance(opt_state, DirectOptimizedState):
            raise TypeError("Expected DirectOptimizedState")

        settings = []
        shots_per_setting = []
        observable_setting_map: dict[str, list[int]] = {}

        for i, group in enumerate(opt_state.groups):
            setting = MeasurementSetting(
                setting_id=group.group_id,
                measurement_basis=group.measurement_basis,
                target_qubits=list(range(opt_state.observable_set.n_qubits)),
                metadata={
                    "group_size": group.size,
                    "allocation_weight": opt_state.allocation_weights[group.group_id],
                    "observable_ids": [obs.observable_id for obs in group.observables],
                },
            )
            settings.append(setting)
            shots_per_setting.append(opt_state.shots_per_group[group.group_id])

            # Map each observable in this group to this setting
            for obs in group.observables:
                observable_setting_map[obs.observable_id] = [i]

        return MeasurementPlan(
            settings=settings,
            shots_per_setting=shots_per_setting,
            observable_setting_map=observable_setting_map,
            metadata={
                "n_groups": len(opt_state.groups),
                "allocation_strategy": self.allocation_strategy,
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
        opt_state = state
        if not isinstance(opt_state, DirectOptimizedState):
            raise TypeError("Expected DirectOptimizedState")

        # Store bitstrings for each group
        for setting_id, bitstrings in data_chunk.bitstrings.items():
            opt_state.group_bitstrings[setting_id].extend(bitstrings)

        # Update budget tracking
        total_new_shots = sum(len(bs) for bs in data_chunk.bitstrings.values())
        opt_state.remaining_budget -= total_new_shots
        opt_state.round_number += 1

        return opt_state

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
        opt_state = state
        if not isinstance(opt_state, DirectOptimizedState):
            raise TypeError("Expected DirectOptimizedState")

        estimates = []

        # Build mapping from observable_id to group
        obs_to_group = {}
        for group in opt_state.groups:
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
                bitstrings = opt_state.group_bitstrings.get(group.group_id, [])

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
                        metadata={
                            "group_id": group.group_id,
                            "allocation_weight": opt_state.allocation_weights[
                                group.group_id
                            ],
                        },
                    )

            estimates.append(estimate)

        return Estimates(
            estimates=estimates,
            protocol_id=self.protocol_id,
            protocol_version=self.protocol_version,
            total_shots=state.total_budget - state.remaining_budget,
            metadata={
                "n_groups": len(opt_state.groups),
                "allocation_strategy": self.allocation_strategy,
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
