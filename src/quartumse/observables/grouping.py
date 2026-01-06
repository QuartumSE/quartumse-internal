"""Commutation analysis and grouping for observables (§4.1B).

This module provides utilities for:
1. Checking commutation between Pauli observables
2. Partitioning observables into commuting families
3. Finding shared measurement bases for commuting groups

These utilities are essential for implementing the "Direct with commuting
grouping" baseline (§4.1B) which is required for defensible benchmarks.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .core import Observable, ObservableSet


def pauli_commutes(p1: str, p2: str) -> bool:
    """Check if two Pauli strings commute.

    Two Pauli strings commute if they differ on an even number of
    qubits (excluding positions where either is identity).

    Args:
        p1: First Pauli string (e.g., "XYZII").
        p2: Second Pauli string (e.g., "ZYXII").

    Returns:
        True if the Pauli strings commute.
    """
    if len(p1) != len(p2):
        raise ValueError(f"Pauli strings must have same length: {len(p1)} vs {len(p2)}")

    anticommute_count = 0
    for c1, c2 in zip(p1, p2):
        if c1 != "I" and c2 != "I" and c1 != c2:
            anticommute_count += 1

    return anticommute_count % 2 == 0


def qubitwise_commutes(p1: str, p2: str) -> bool:
    """Check if two Pauli strings commute qubit-wise.

    Qubit-wise commutation is stronger than global commutation.
    Two strings commute qubit-wise if on each qubit, either:
    - At least one is identity, or
    - Both are the same Pauli operator

    Args:
        p1: First Pauli string.
        p2: Second Pauli string.

    Returns:
        True if the Pauli strings commute qubit-wise.
    """
    if len(p1) != len(p2):
        raise ValueError(f"Pauli strings must have same length: {len(p1)} vs {len(p2)}")

    for c1, c2 in zip(p1, p2):
        if c1 != "I" and c2 != "I" and c1 != c2:
            return False
    return True


def shared_measurement_basis(observables: list[Observable]) -> str | None:
    """Find a shared measurement basis for a list of observables.

    For observables to share a measurement basis, they must commute
    qubit-wise. The shared basis is the "union" of non-identity operators.

    Args:
        observables: List of observables to find shared basis for.

    Returns:
        Shared measurement basis string, or None if no shared basis exists.
    """
    if not observables:
        return None

    n_qubits = observables[0].n_qubits

    # Verify all observables have same qubit count
    if not all(obs.n_qubits == n_qubits for obs in observables):
        return None

    # Build shared basis by taking non-identity operators
    basis = ["I"] * n_qubits

    for obs in observables:
        for i, c in enumerate(obs.pauli_string):
            if c == "I":
                continue
            if basis[i] == "I":
                basis[i] = c
            elif basis[i] != c:
                # Conflict: different non-identity operators on same qubit
                return None

    # Default identity positions to Z (computational basis)
    basis = [c if c != "I" else "Z" for c in basis]

    return "".join(basis)


def build_commutation_graph(observables: list[Observable]) -> dict[int, set[int]]:
    """Build a graph where edges connect commuting observables.

    Args:
        observables: List of observables.

    Returns:
        Adjacency list representation: node -> set of commuting neighbors.
    """
    n = len(observables)
    graph: dict[int, set[int]] = {i: set() for i in range(n)}

    for i in range(n):
        for j in range(i + 1, n):
            if observables[i].commutes_with(observables[j]):
                graph[i].add(j)
                graph[j].add(i)

    return graph


def build_qubitwise_commutation_graph(
    observables: list[Observable],
) -> dict[int, set[int]]:
    """Build a graph where edges connect qubit-wise commuting observables.

    This is stricter than global commutation and is required for
    shared measurement basis construction.

    Args:
        observables: List of observables.

    Returns:
        Adjacency list representation: node -> set of qw-commuting neighbors.
    """
    n = len(observables)
    graph: dict[int, set[int]] = {i: set() for i in range(n)}

    for i in range(n):
        for j in range(i + 1, n):
            if qubitwise_commutes(
                observables[i].pauli_string,
                observables[j].pauli_string,
            ):
                graph[i].add(j)
                graph[j].add(i)

    return graph


@dataclass
class CommutingGroup:
    """A group of qubit-wise commuting observables.

    Attributes:
        group_id: Unique identifier for this group.
        observable_indices: Indices of observables in this group.
        measurement_basis: Shared measurement basis for the group.
        observables: The Observable objects in this group.
    """

    group_id: str
    observable_indices: list[int]
    measurement_basis: str
    observables: list[Observable] = field(default_factory=list)

    @property
    def size(self) -> int:
        """Number of observables in this group."""
        return len(self.observable_indices)


def greedy_grouping(
    observables: list[Observable],
    use_qubitwise: bool = True,
) -> list[CommutingGroup]:
    """Partition observables into commuting groups using greedy algorithm.

    This algorithm iteratively builds groups by:
    1. Starting with the first ungrouped observable
    2. Adding all observables that commute with all current group members
    3. Repeating until all observables are grouped

    Args:
        observables: List of observables to partition.
        use_qubitwise: If True, use qubit-wise commutation (required for
            shared measurement basis). If False, use global commutation.

    Returns:
        List of CommutingGroup objects.
    """
    n = len(observables)
    if n == 0:
        return []

    # Build commutation graph
    if use_qubitwise:
        graph = build_qubitwise_commutation_graph(observables)
    else:
        graph = build_commutation_graph(observables)

    grouped = [False] * n
    groups: list[CommutingGroup] = []
    group_counter = 0

    for start in range(n):
        if grouped[start]:
            continue

        # Start a new group
        current_group = [start]
        grouped[start] = True

        # Find all observables that commute with entire current group
        candidates = set(range(n)) - set(current_group)

        for cand in sorted(candidates):
            if grouped[cand]:
                continue

            # Check if candidate commutes with all current group members
            commutes_with_all = all(cand in graph[member] for member in current_group)

            if commutes_with_all:
                current_group.append(cand)
                grouped[cand] = True

        # Create CommutingGroup
        group_observables = [observables[i] for i in current_group]

        # Find shared measurement basis
        if use_qubitwise:
            basis = shared_measurement_basis(group_observables)
        else:
            basis = None  # Global commutation doesn't guarantee shared basis

        group_id = f"group_{group_counter}"
        group_counter += 1

        # Update observable group_ids
        for obs in group_observables:
            obs.group_id = group_id

        groups.append(
            CommutingGroup(
                group_id=group_id,
                observable_indices=current_group,
                measurement_basis=basis or "",
                observables=group_observables,
            )
        )

    return groups


def sorted_insertion_grouping(
    observables: list[Observable],
) -> list[CommutingGroup]:
    """Partition observables using sorted insertion heuristic.

    This algorithm:
    1. Sorts observables by weight (locality) in descending order
    2. Inserts each observable into the first compatible group
    3. Creates new group if no compatible group exists

    This often produces fewer groups than greedy when there are
    many high-weight observables.

    Args:
        observables: List of observables to partition.

    Returns:
        List of CommutingGroup objects.
    """
    n = len(observables)
    if n == 0:
        return []

    # Sort by weight (descending), keeping track of original indices
    sorted_indices = sorted(range(n), key=lambda i: -observables[i].weight)

    groups: list[list[int]] = []
    group_bases: list[str | None] = []

    for idx in sorted_indices:
        obs = observables[idx]
        placed = False

        # Try to place in existing group
        for g_idx, (group, basis) in enumerate(zip(groups, group_bases)):
            # Check if observable fits in this group
            group_obs = [observables[i] for i in group]
            test_basis = shared_measurement_basis(group_obs + [obs])

            if test_basis is not None:
                groups[g_idx].append(idx)
                group_bases[g_idx] = test_basis
                placed = True
                break

        if not placed:
            # Create new group
            groups.append([idx])
            group_bases.append(obs.pauli_string.replace("I", "Z"))

    # Convert to CommutingGroup objects
    result: list[CommutingGroup] = []
    for g_idx, (group_indices, basis) in enumerate(zip(groups, group_bases)):
        group_id = f"group_{g_idx}"
        group_observables = [observables[i] for i in group_indices]

        for obs in group_observables:
            obs.group_id = group_id

        result.append(
            CommutingGroup(
                group_id=group_id,
                observable_indices=group_indices,
                measurement_basis=basis or "",
                observables=group_observables,
            )
        )

    return result


def partition_observable_set(
    observable_set: ObservableSet,
    method: str = "greedy",
) -> tuple[list[CommutingGroup], dict[str, Any]]:
    """Partition an ObservableSet into commuting groups.

    Args:
        observable_set: The ObservableSet to partition.
        method: Grouping method: "greedy" or "sorted_insertion".

    Returns:
        Tuple of (list of CommutingGroups, statistics dict).
    """
    if method == "greedy":
        groups = greedy_grouping(list(observable_set.observables))
    elif method == "sorted_insertion":
        groups = sorted_insertion_grouping(list(observable_set.observables))
    else:
        raise ValueError(f"Unknown grouping method: {method}")

    # Compute statistics
    group_sizes = [g.size for g in groups]
    stats = {
        "n_groups": len(groups),
        "n_observables": len(observable_set),
        "min_group_size": min(group_sizes) if group_sizes else 0,
        "max_group_size": max(group_sizes) if group_sizes else 0,
        "mean_group_size": np.mean(group_sizes) if group_sizes else 0,
        "method": method,
    }

    return groups, stats


def verify_grouping(groups: list[CommutingGroup]) -> bool:
    """Verify that a grouping is valid.

    Checks that:
    1. All observables in each group commute qubit-wise
    2. The measurement basis is valid for all observables

    Args:
        groups: List of CommutingGroups to verify.

    Returns:
        True if grouping is valid.
    """
    for group in groups:
        # Check pairwise qubit-wise commutation
        for i, obs1 in enumerate(group.observables):
            for obs2 in group.observables[i + 1 :]:
                if not qubitwise_commutes(obs1.pauli_string, obs2.pauli_string):
                    return False

        # Check measurement basis compatibility
        computed_basis = shared_measurement_basis(group.observables)
        if computed_basis is None:
            return False

    return True
