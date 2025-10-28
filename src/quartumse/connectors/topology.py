"""Topology helpers for selecting qubit chains."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, Iterable, List, MutableMapping, Sequence, Set

LOGGER = logging.getLogger(__name__)


def _normalise_edges(raw_edges: Iterable[Sequence[int]] | None) -> List[Sequence[int]]:
    """Normalise assorted coupling-map representations into edge pairs."""

    if raw_edges is None:
        return []

    # ``CouplingMap`` instances expose ``get_edges`` for a flat edge list.
    if hasattr(raw_edges, "get_edges"):
        try:  # pragma: no cover - defensive against unexpected objects
            return list(raw_edges.get_edges())
        except Exception:  # pragma: no cover - degrade gracefully
            return []

    edges: List[Sequence[int]] = []
    for entry in raw_edges:
        if entry is None:
            continue
        if isinstance(entry, Sequence) and not isinstance(entry, (str, bytes)):
            if len(entry) < 2:
                continue
            if len(entry) == 2:
                edges.append((int(entry[0]), int(entry[1])))
            else:
                # Some backends provide multi-hop paths; split them into pairs.
                for left, right in zip(entry[:-1], entry[1:]):
                    edges.append((int(left), int(right)))
    return edges


def _build_adjacency(num_qubits: int, edges: Iterable[Sequence[int]]) -> Dict[int, Set[int]]:
    """Construct an undirected adjacency map for the device graph."""

    adjacency: Dict[int, Set[int]] = defaultdict(set)
    for qubit in range(num_qubits):
        adjacency[qubit]  # ensure all keys exist

    for edge in edges:
        if len(edge) < 2:
            continue
        left, right = int(edge[0]), int(edge[1])
        if not (0 <= left < num_qubits and 0 <= right < num_qubits):
            continue
        adjacency[left].add(right)
        adjacency[right].add(left)
    return adjacency


def _depth_first_path(
    adjacency: MutableMapping[int, Set[int]],
    start: int,
    length: int,
    path: List[int],
    visited: Set[int],
) -> List[int] | None:
    if len(path) == length:
        return path.copy()

    for neighbour in sorted(adjacency[start]):
        if neighbour in visited:
            continue
        visited.add(neighbour)
        path.append(neighbour)
        result = _depth_first_path(adjacency, neighbour, length, path, visited)
        if result is not None:
            return result
        path.pop()
        visited.remove(neighbour)
    return None


def _find_simple_path(adjacency: MutableMapping[int, Set[int]], length: int) -> List[int] | None:
    for start in sorted(adjacency):
        result = _depth_first_path(adjacency, start, length, [start], {start})
        if result is not None:
            return result
    return None


def _greedy_chain(
    num_qubits: int,
    adjacency: MutableMapping[int, Set[int]],
    length: int,
) -> List[int]:
    """Best-effort greedy chain selection when an exact path is unavailable."""

    nodes = list(range(num_qubits))
    degree = {node: len(adjacency.get(node, set())) for node in nodes}
    start_candidates = sorted(nodes, key=lambda item: (-degree[item], item))

    best_chain: List[int] = []
    for start in start_candidates:
        chain = [start]
        visited = {start}
        current = start
        while len(chain) < length:
            candidates = [
                node
                for node in sorted(adjacency.get(current, set()), key=lambda item: (-degree[item], item))
                if node not in visited
            ]
            if not candidates:
                break
            current = candidates[0]
            chain.append(current)
            visited.add(current)
        if len(chain) == length:
            return chain
        if len(chain) > len(best_chain):
            best_chain = chain

    if len(best_chain) >= length:
        return best_chain[:length]

    # Fall back to a trivial sequential allocation when no connectivity data exist.
    return list(range(length)) if length <= num_qubits else []


def get_linear_chain(backend, length: int) -> List[int]:
    """Select a linear chain of ``length`` qubits on ``backend``.

    The function first attempts to locate a simple path of the requested length
    using the backend coupling map.  When no such path exists, a greedy heuristic
    is used to assemble a best-effort chain.  A :class:`ValueError` is raised if a
    chain of the requested length cannot be identified.
    """

    if length <= 0:
        raise ValueError("Chain length must be a positive integer")

    try:
        configuration = backend.configuration()
    except Exception:  # pragma: no cover - defensive against custom backends
        configuration = None

    num_qubits = None
    coupling_map = None

    if configuration is not None:
        num_qubits = getattr(
            configuration,
            "num_qubits",
            getattr(configuration, "n_qubits", getattr(configuration, "number_of_qubits", None)),
        )
        coupling_map = getattr(configuration, "coupling_map", None)

    if num_qubits is None:
        num_qubits = getattr(backend, "num_qubits", getattr(backend, "n_qubits", None))
    if num_qubits is None:
        raise ValueError("Unable to determine the number of qubits for backend")

    if length > int(num_qubits):
        raise ValueError(
            f"Requested chain length {length} exceeds backend capacity of {num_qubits} qubits"
        )

    if coupling_map is None:
        coupling_map = getattr(backend, "coupling_map", None)
        if coupling_map is not None and hasattr(coupling_map, "get_edges"):
            coupling_map = coupling_map.get_edges()

    edges = _normalise_edges(coupling_map)
    adjacency = _build_adjacency(int(num_qubits), edges)

    if length == 1:
        return [min(adjacency)] if adjacency else [0]

    simple_path = _find_simple_path(adjacency, length)
    if simple_path is not None:
        return simple_path

    greedy_chain = _greedy_chain(int(num_qubits), adjacency, length)
    if len(greedy_chain) == length:
        backend_name = getattr(backend, "name", None)
        if backend_name is None:
            backend_name = getattr(backend, "__class__", type(backend))
        backend_name = str(backend_name)
        LOGGER.info(
            "Falling back to greedy linear chain of length %s on backend %s", length, backend_name
        )
        return greedy_chain

    raise ValueError(
        f"Unable to find a connected chain of {length} qubits for backend with {num_qubits} qubits"
    )
