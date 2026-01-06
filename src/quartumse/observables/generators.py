"""Seeded observable generators (Measurements Bible §3.3).

This module implements the required observable generators for reproducible
benchmark specification. All generators are seeded and produce ObservableSets
with full generation metadata.

Required generators per §3.3:
1. RandomPauliGenerator: Random Pauli strings with controlled weight distribution
2. HamiltonianGenerator: Pauli sums with controlled coefficient distribution
3. CorrelatorGenerator: Structured correlators (e.g., 2-point Z_i Z_j)
4. ClusteredSupportGenerator: Observables with overlapping supports
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.random import Generator

from .core import Observable, ObservableSet


@dataclass
class GeneratorConfig:
    """Configuration for observable generators.

    Attributes:
        n_qubits: Number of qubits.
        n_observables: Number of observables to generate.
        seed: Random seed for reproducibility.
        extra: Additional generator-specific parameters.
    """

    n_qubits: int
    n_observables: int
    seed: int
    extra: dict[str, Any] = field(default_factory=dict)


class ObservableGenerator(ABC):
    """Abstract base class for observable generators (§3.3).

    All generators must:
    - Be deterministically reproducible from seed
    - Record generator_id and generator_version
    - Produce ObservableSets with full metadata
    """

    generator_id: str = "abstract_generator"
    generator_version: str = "0.0.0"

    def __init__(self, config: GeneratorConfig) -> None:
        """Initialize generator with configuration.

        Args:
            config: Generator configuration including seed.
        """
        self.config = config
        self.rng = np.random.default_rng(config.seed)

    @abstractmethod
    def generate(self) -> ObservableSet:
        """Generate an ObservableSet.

        Returns:
            ObservableSet with full generation metadata.
        """
        ...

    def _create_observable_set(
        self,
        observables: list[Observable],
        extra_params: dict[str, Any] | None = None,
    ) -> ObservableSet:
        """Create ObservableSet with proper metadata."""
        params = {
            "n_qubits": self.config.n_qubits,
            "n_observables": self.config.n_observables,
            **self.config.extra,
            **(extra_params or {}),
        }
        return ObservableSet(
            observables=observables,
            generator_id=self.generator_id,
            generator_version=self.generator_version,
            generator_seed=self.config.seed,
            generator_params=params,
        )


class RandomPauliGenerator(ObservableGenerator):
    """Generate random Pauli strings with controlled weight distribution.

    This generator creates random Pauli strings where the weight (number of
    non-identity operators) follows a configurable distribution.

    Config.extra parameters:
        weight_distribution: "uniform", "fixed", or "geometric"
        min_weight: Minimum Pauli weight (default 1)
        max_weight: Maximum Pauli weight (default n_qubits)
        fixed_weight: Fixed weight if weight_distribution="fixed"
        geometric_p: Probability parameter for geometric distribution
        allow_identity: Whether to allow all-identity observable (default False)
    """

    generator_id = "random_pauli"
    generator_version = "1.0.0"

    def generate(self) -> ObservableSet:
        """Generate random Pauli string observables."""
        n = self.config.n_qubits
        m = self.config.n_observables
        extra = self.config.extra

        weight_dist = extra.get("weight_distribution", "uniform")
        min_weight = extra.get("min_weight", 1)
        max_weight = extra.get("max_weight", n)
        allow_identity = extra.get("allow_identity", False)

        if min_weight < 0:
            min_weight = 0
        if max_weight > n:
            max_weight = n
        if not allow_identity and min_weight == 0:
            min_weight = 1

        observables: list[Observable] = []
        generated_strings: set[str] = set()

        while len(observables) < m:
            # Determine weight for this observable
            if weight_dist == "fixed":
                weight = extra.get("fixed_weight", min_weight)
            elif weight_dist == "geometric":
                p = extra.get("geometric_p", 0.5)
                weight = min(
                    min_weight + self.rng.geometric(p) - 1,
                    max_weight,
                )
            else:  # uniform
                weight = self.rng.integers(min_weight, max_weight + 1)

            # Generate Pauli string with this weight
            pauli_string = self._generate_pauli_string(n, weight)

            # Avoid duplicates
            if pauli_string not in generated_strings:
                generated_strings.add(pauli_string)
                observables.append(Observable(pauli_string=pauli_string))

        return self._create_observable_set(observables)

    def _generate_pauli_string(self, n_qubits: int, weight: int) -> str:
        """Generate a random Pauli string with specified weight."""
        # Choose which qubits have non-identity operators
        non_identity_positions = self.rng.choice(
            n_qubits, size=weight, replace=False
        )

        # Build Pauli string
        paulis = ["I"] * n_qubits
        pauli_choices = ["X", "Y", "Z"]

        for pos in non_identity_positions:
            paulis[pos] = self.rng.choice(pauli_choices)

        return "".join(paulis)


class HamiltonianGenerator(ObservableGenerator):
    """Generate Hamiltonian-like Pauli sums with coefficient distribution.

    This generator creates observables representing terms in a Hamiltonian,
    with coefficients following a configurable distribution.

    Config.extra parameters:
        coefficient_distribution: "uniform", "normal", "exponential", or "heavy_tailed"
        coefficient_scale: Scale parameter for coefficient distribution
        weight_distribution: Same as RandomPauliGenerator
        include_identity: Whether to include identity term (default False)
        normalize: Whether to normalize coefficients (default False)
    """

    generator_id = "hamiltonian"
    generator_version = "1.0.0"

    def generate(self) -> ObservableSet:
        """Generate Hamiltonian-like observable set."""
        n = self.config.n_qubits
        m = self.config.n_observables
        extra = self.config.extra

        coef_dist = extra.get("coefficient_distribution", "uniform")
        coef_scale = extra.get("coefficient_scale", 1.0)
        normalize = extra.get("normalize", False)

        # Generate Pauli strings using RandomPauliGenerator logic
        pauli_config = GeneratorConfig(
            n_qubits=n,
            n_observables=m,
            seed=self.config.seed,
            extra={k: v for k, v in extra.items() if k.startswith("weight")},
        )
        pauli_gen = RandomPauliGenerator(pauli_config)
        base_set = pauli_gen.generate()

        # Generate coefficients
        coefficients = self._generate_coefficients(m, coef_dist, coef_scale)

        if normalize:
            norm = np.sqrt(np.sum(coefficients**2))
            if norm > 0:
                coefficients = coefficients / norm

        # Create observables with coefficients
        observables = [
            Observable(
                pauli_string=obs.pauli_string,
                coefficient=float(coef),
            )
            for obs, coef in zip(base_set.observables, coefficients)
        ]

        return self._create_observable_set(
            observables,
            extra_params={"coefficient_distribution": coef_dist},
        )

    def _generate_coefficients(
        self,
        n: int,
        distribution: str,
        scale: float,
    ) -> np.ndarray:
        """Generate coefficients from specified distribution."""
        if distribution == "uniform":
            return self.rng.uniform(-scale, scale, size=n)
        elif distribution == "normal":
            return self.rng.normal(0, scale, size=n)
        elif distribution == "exponential":
            # Exponentially decaying magnitudes with random signs
            magnitudes = scale * np.exp(-np.arange(n) / (n / 3))
            signs = self.rng.choice([-1, 1], size=n)
            return magnitudes * signs
        elif distribution == "heavy_tailed":
            # Cauchy-like heavy tails (use t-distribution with low df)
            return self.rng.standard_t(df=2, size=n) * scale
        else:
            raise ValueError(f"Unknown coefficient distribution: {distribution}")


class CorrelatorGenerator(ObservableGenerator):
    """Generate structured correlator observables.

    This generator creates 2-point or k-point correlators, commonly used
    for studying correlations in quantum systems.

    Config.extra parameters:
        correlator_type: "two_point_z", "two_point_xx", "k_local"
        interaction_graph: "chain", "all_pairs", "nearest_neighbor", "random"
        k: For k-local correlators, the locality (default 2)
        periodic: Whether to use periodic boundary conditions (default False)
    """

    generator_id = "correlator"
    generator_version = "1.0.0"

    def generate(self) -> ObservableSet:
        """Generate correlator observables."""
        n = self.config.n_qubits
        m = self.config.n_observables
        extra = self.config.extra

        correlator_type = extra.get("correlator_type", "two_point_z")
        graph = extra.get("interaction_graph", "all_pairs")
        periodic = extra.get("periodic", False)

        # Generate pairs/tuples based on graph structure
        if correlator_type in ["two_point_z", "two_point_xx"]:
            pairs = self._generate_pairs(n, m, graph, periodic)
            observables = self._create_two_point_observables(
                pairs, n, correlator_type
            )
        else:
            k = extra.get("k", 2)
            tuples = self._generate_k_tuples(n, m, k, graph)
            observables = self._create_k_local_observables(tuples, n)

        return self._create_observable_set(observables)

    def _generate_pairs(
        self,
        n_qubits: int,
        n_observables: int,
        graph: str,
        periodic: bool,
    ) -> list[tuple[int, int]]:
        """Generate qubit pairs based on interaction graph."""
        if graph == "chain":
            # Nearest-neighbor chain
            pairs = [(i, i + 1) for i in range(n_qubits - 1)]
            if periodic and n_qubits > 2:
                pairs.append((n_qubits - 1, 0))
        elif graph == "all_pairs":
            # All pairs of qubits
            pairs = [
                (i, j) for i in range(n_qubits) for j in range(i + 1, n_qubits)
            ]
        elif graph == "nearest_neighbor":
            # Same as chain
            pairs = [(i, i + 1) for i in range(n_qubits - 1)]
            if periodic and n_qubits > 2:
                pairs.append((n_qubits - 1, 0))
        elif graph == "random":
            # Random pairs
            all_pairs = [
                (i, j) for i in range(n_qubits) for j in range(i + 1, n_qubits)
            ]
            n_pairs = min(n_observables, len(all_pairs))
            indices = self.rng.choice(len(all_pairs), size=n_pairs, replace=False)
            pairs = [all_pairs[i] for i in indices]
        else:
            raise ValueError(f"Unknown interaction graph: {graph}")

        # Limit to requested number
        if len(pairs) > n_observables:
            indices = self.rng.choice(len(pairs), size=n_observables, replace=False)
            pairs = [pairs[i] for i in sorted(indices)]

        return pairs[:n_observables]

    def _create_two_point_observables(
        self,
        pairs: list[tuple[int, int]],
        n_qubits: int,
        correlator_type: str,
    ) -> list[Observable]:
        """Create two-point correlator observables."""
        observables = []
        for i, j in pairs:
            paulis = ["I"] * n_qubits
            if correlator_type == "two_point_z":
                paulis[i] = "Z"
                paulis[j] = "Z"
            elif correlator_type == "two_point_xx":
                paulis[i] = "X"
                paulis[j] = "X"
            pauli_string = "".join(paulis)
            observables.append(Observable(pauli_string=pauli_string))
        return observables

    def _generate_k_tuples(
        self,
        n_qubits: int,
        n_observables: int,
        k: int,
        graph: str,
    ) -> list[tuple[int, ...]]:
        """Generate k-tuples of qubits."""
        if graph == "chain":
            # Consecutive k-tuples along chain
            tuples = [
                tuple(range(i, i + k)) for i in range(n_qubits - k + 1)
            ]
        else:
            # Random k-tuples
            from itertools import combinations

            all_tuples = list(combinations(range(n_qubits), k))
            n_tuples = min(n_observables, len(all_tuples))
            indices = self.rng.choice(len(all_tuples), size=n_tuples, replace=False)
            tuples = [all_tuples[i] for i in indices]

        return tuples[:n_observables]

    def _create_k_local_observables(
        self,
        tuples: list[tuple[int, ...]],
        n_qubits: int,
    ) -> list[Observable]:
        """Create k-local Z-string observables."""
        observables = []
        for qubit_tuple in tuples:
            paulis = ["I"] * n_qubits
            for i in qubit_tuple:
                paulis[i] = "Z"
            pauli_string = "".join(paulis)
            observables.append(Observable(pauli_string=pauli_string))
        return observables


class ClusteredSupportGenerator(ObservableGenerator):
    """Generate observables with overlapping (clustered) supports.

    This generator creates sets where many observables act on a common
    subset of qubits, simulating scenarios where certain qubits are
    more "interesting" than others.

    Config.extra parameters:
        n_clusters: Number of qubit clusters
        cluster_size: Size of each cluster
        observables_per_cluster: Observables generated per cluster
        cluster_overlap: Allowed overlap between clusters (0-1)
        weight_in_cluster: Weight of observables within their cluster
    """

    generator_id = "clustered_support"
    generator_version = "1.0.0"

    def generate(self) -> ObservableSet:
        """Generate clustered-support observables."""
        n = self.config.n_qubits
        m = self.config.n_observables
        extra = self.config.extra

        n_clusters = extra.get("n_clusters", max(1, n // 4))
        cluster_size = extra.get("cluster_size", min(4, n))
        obs_per_cluster = extra.get(
            "observables_per_cluster", m // n_clusters + 1
        )
        weight_in_cluster = extra.get("weight_in_cluster", 2)

        # Generate cluster centers
        clusters = self._generate_clusters(n, n_clusters, cluster_size)

        # Generate observables within each cluster
        observables: list[Observable] = []
        generated_strings: set[str] = set()

        for cluster_qubits in clusters:
            for _ in range(obs_per_cluster):
                if len(observables) >= m:
                    break

                pauli_string = self._generate_clustered_observable(
                    n, cluster_qubits, weight_in_cluster
                )

                if pauli_string not in generated_strings:
                    generated_strings.add(pauli_string)
                    observables.append(Observable(pauli_string=pauli_string))

            if len(observables) >= m:
                break

        return self._create_observable_set(observables[:m])

    def _generate_clusters(
        self,
        n_qubits: int,
        n_clusters: int,
        cluster_size: int,
    ) -> list[list[int]]:
        """Generate qubit clusters."""
        clusters = []
        for _ in range(n_clusters):
            # Random cluster center
            center = self.rng.integers(0, n_qubits)
            # Qubits around center
            cluster_qubits = sorted(
                set(
                    (center + offset) % n_qubits
                    for offset in range(-cluster_size // 2, cluster_size // 2 + 1)
                )
            )[:cluster_size]
            clusters.append(cluster_qubits)
        return clusters

    def _generate_clustered_observable(
        self,
        n_qubits: int,
        cluster_qubits: list[int],
        weight: int,
    ) -> str:
        """Generate observable with support in cluster."""
        weight = min(weight, len(cluster_qubits))
        positions = self.rng.choice(cluster_qubits, size=weight, replace=False)

        paulis = ["I"] * n_qubits
        pauli_choices = ["X", "Y", "Z"]

        for pos in positions:
            paulis[pos] = self.rng.choice(pauli_choices)

        return "".join(paulis)


# Generator registry
_GENERATORS: dict[str, type[ObservableGenerator]] = {
    "random_pauli": RandomPauliGenerator,
    "hamiltonian": HamiltonianGenerator,
    "correlator": CorrelatorGenerator,
    "clustered_support": ClusteredSupportGenerator,
}


def get_generator(generator_id: str) -> type[ObservableGenerator]:
    """Get a generator class by ID."""
    if generator_id not in _GENERATORS:
        available = ", ".join(sorted(_GENERATORS.keys()))
        raise KeyError(
            f"Generator '{generator_id}' not found. Available: {available}"
        )
    return _GENERATORS[generator_id]


def list_generators() -> list[str]:
    """List all available generator IDs."""
    return sorted(_GENERATORS.keys())


def generate_observable_set(
    generator_id: str,
    n_qubits: int,
    n_observables: int,
    seed: int,
    **kwargs: Any,
) -> ObservableSet:
    """Convenience function to generate an ObservableSet.

    Args:
        generator_id: ID of the generator to use.
        n_qubits: Number of qubits.
        n_observables: Number of observables to generate.
        seed: Random seed for reproducibility.
        **kwargs: Additional generator-specific parameters.

    Returns:
        Generated ObservableSet.
    """
    generator_cls = get_generator(generator_id)
    config = GeneratorConfig(
        n_qubits=n_qubits,
        n_observables=n_observables,
        seed=seed,
        extra=kwargs,
    )
    generator = generator_cls(config)
    return generator.generate()
