"""Observable Suites for Benchmarking (Measurements Bible §3).

This module provides the ObservableSuite abstraction and circuit-specific suite
generators for comprehensive benchmarking of classical shadows vs direct measurement.

Key concepts:
- ObservableSuite: A named collection of observables with optional weights and objective type
- Workload suites: Task-aligned observables (what practitioners actually measure)
- Stress suites: Large sets for testing protocol scaling
- Post-hoc libraries: Observable pools for simulating "measure once, query later"

References:
    - Huang, Kueng, Preskill (2020): Classical shadows
    - Hadfield et al. (2020): Locally-biased classical shadows
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from itertools import combinations, product
from math import comb
from typing import Any, Literal

import numpy as np

from .core import Observable, ObservableSet


class ObjectiveType(Enum):
    """Type of objective function for the suite."""

    PER_OBSERVABLE = "per_observable"  # Evaluate each observable independently
    WEIGHTED_SUM = "weighted_sum"      # Evaluate sum: E = Σ w_k ⟨O_k⟩
    MAX_ERROR = "max_error"            # Evaluate worst-case observable
    CUSTOM = "custom"                  # User-defined objective


class SuiteType(Enum):
    """Category of observable suite."""

    WORKLOAD = "workload"      # Task-aligned (what practitioners measure)
    STRESS = "stress"          # Large sets for scaling tests
    POSTHOC = "posthoc"        # Library for post-hoc querying tests
    COMMUTING = "commuting"    # All-commuting baseline (grouped measurement advantage)
    DIAGNOSTIC = "diagnostic"  # System diagnostics (readout, crosstalk)


@dataclass
class ObservableSuite:
    """A named collection of observables for benchmarking.

    This class extends ObservableSet with:
    - Suite name and type for clear scenario identification
    - Optional weights for weighted-sum objectives (energy, cost)
    - Objective type specification
    - Commutation analysis metadata

    Attributes:
        name: Human-readable suite name (e.g., "workload_qaoa_cost")
        suite_type: Category (workload, stress, posthoc, commuting)
        observable_set: The underlying ObservableSet
        weights: Optional dict mapping observable_id -> coefficient
        objective: Type of objective function
        description: Human-readable description
        metadata: Additional suite-specific metadata
    """

    name: str
    suite_type: SuiteType
    observable_set: ObservableSet
    weights: dict[str, float] | None = None
    objective: ObjectiveType = ObjectiveType.PER_OBSERVABLE
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate suite configuration."""
        # If weights provided, ensure objective is WEIGHTED_SUM
        if self.weights and self.objective == ObjectiveType.PER_OBSERVABLE:
            self.objective = ObjectiveType.WEIGHTED_SUM

        # Validate weights keys match observable IDs
        if self.weights:
            obs_ids = {obs.observable_id for obs in self.observable_set}
            weight_ids = set(self.weights.keys())
            if not weight_ids.issubset(obs_ids):
                missing = weight_ids - obs_ids
                raise ValueError(f"Weight keys not found in observables: {missing}")

    @property
    def n_observables(self) -> int:
        """Number of observables in the suite."""
        return len(self.observable_set)

    @property
    def n_qubits(self) -> int:
        """Number of qubits."""
        return self.observable_set.n_qubits

    @property
    def observables(self) -> list[Observable]:
        """List of observables."""
        return self.observable_set.observables

    def locality_distribution(self) -> dict[int, int]:
        """Distribution of Pauli weights."""
        return self.observable_set.locality_distribution()

    def commutation_analysis(self) -> dict[str, Any]:
        """Analyze commutation structure of the suite.

        Returns dict with:
            - n_commuting_groups: Number of groups after greedy partitioning
            - max_group_size: Largest commuting group
            - fully_commuting: Whether all observables commute
            - grouping_efficiency: n_observables / n_groups (higher = better for direct)
        """
        from .grouping import partition_observable_set

        groups, stats = partition_observable_set(self.observable_set)

        return {
            "n_commuting_groups": len(groups),
            "max_group_size": max(len(g.observables) for g in groups) if groups else 0,
            "fully_commuting": len(groups) == 1,
            "grouping_efficiency": self.n_observables / len(groups) if groups else 0,
            "partition_stats": stats,
        }

    def compute_objective(self, estimates: dict[str, float]) -> float:
        """Compute the objective value from observable estimates.

        Args:
            estimates: Dict mapping observable_id -> estimated expectation value

        Returns:
            Objective value (interpretation depends on objective type)
        """
        if self.objective == ObjectiveType.PER_OBSERVABLE:
            # Return mean estimate (not very meaningful, but consistent)
            return np.mean(list(estimates.values()))

        elif self.objective == ObjectiveType.WEIGHTED_SUM:
            if not self.weights:
                raise ValueError("WEIGHTED_SUM objective requires weights")
            total = 0.0
            for obs_id, weight in self.weights.items():
                if obs_id in estimates:
                    total += weight * estimates[obs_id]
            return total

        elif self.objective == ObjectiveType.MAX_ERROR:
            # This requires truth values, return NaN for now
            return float('nan')

        else:
            raise ValueError(f"Unknown objective type: {self.objective}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "suite_type": self.suite_type.value,
            "objective": self.objective.value,
            "description": self.description,
            "n_observables": self.n_observables,
            "n_qubits": self.n_qubits,
            "weights": self.weights,
            "observable_set": self.observable_set.to_dict(),
            "locality_distribution": self.locality_distribution(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_pauli_strings(
        cls,
        name: str,
        suite_type: SuiteType,
        pauli_strings: list[str],
        weights: dict[str, float] | None = None,
        **kwargs: Any,
    ) -> ObservableSuite:
        """Create suite from Pauli strings.

        Args:
            name: Suite name
            suite_type: Suite category
            pauli_strings: List of Pauli string representations
            weights: Optional dict mapping Pauli string -> coefficient
            **kwargs: Additional arguments (objective, description, metadata)
        """
        obs_set = ObservableSet.from_pauli_strings(pauli_strings)

        # Convert weights from Pauli string keys to observable_id keys
        if weights:
            id_weights = {}
            for obs in obs_set.observables:
                if obs.pauli_string in weights:
                    id_weights[obs.observable_id] = weights[obs.pauli_string]
            weights = id_weights

        return cls(
            name=name,
            suite_type=suite_type,
            observable_set=obs_set,
            weights=weights,
            **kwargs,
        )


# =============================================================================
# PAULI STRING GENERATORS
# =============================================================================

def generate_all_k_local(n_qubits: int, k: int) -> list[str]:
    """Generate ALL k-local Pauli strings on n qubits.

    Total count: C(n,k) * 3^k

    Args:
        n_qubits: Number of qubits
        k: Locality (Pauli weight)

    Returns:
        List of Pauli strings
    """
    paulis = []
    pauli_ops = ['X', 'Y', 'Z']

    for positions in combinations(range(n_qubits), k):
        for ops in product(pauli_ops, repeat=k):
            pauli_list = ['I'] * n_qubits
            for pos, op in zip(positions, ops, strict=False):
                pauli_list[pos] = op
            paulis.append(''.join(pauli_list))

    return paulis


def generate_zz_correlators(
    n_qubits: int,
    pairs: list[tuple[int, int]] | None = None,
    graph: Literal['all', 'chain', 'ring'] = 'all',
) -> list[str]:
    """Generate Z_i Z_j correlator strings.

    Args:
        n_qubits: Number of qubits
        pairs: Explicit list of (i, j) pairs, or None to use graph
        graph: 'all' (all pairs), 'chain' (nearest-neighbor), 'ring' (chain + wrap)

    Returns:
        List of ZZ Pauli strings
    """
    return generate_edge_correlators(n_qubits, pairs=pairs, graph=graph, paulis=['ZZ'])


def generate_edge_correlators(
    n_qubits: int,
    pairs: list[tuple[int, int]] | None = None,
    graph: Literal['all', 'chain', 'ring'] = 'all',
    paulis: list[str] | None = None,
) -> list[str]:
    """Generate two-qubit correlator strings on graph edges.

    Args:
        n_qubits: Number of qubits
        pairs: Explicit list of (i, j) pairs, or None to use graph
        graph: 'all' (all pairs), 'chain' (nearest-neighbor), 'ring' (chain + wrap)
        paulis: List of two-character Pauli pairs, e.g., ['ZZ', 'XX', 'YY']
                Default: ['ZZ']

    Returns:
        List of Pauli strings for all (edge, pauli_type) combinations
    """
    if paulis is None:
        paulis = ['ZZ']

    if pairs is None:
        if graph == 'all':
            pairs = [(i, j) for i in range(n_qubits) for j in range(i + 1, n_qubits)]
        elif graph == 'chain':
            pairs = [(i, i + 1) for i in range(n_qubits - 1)]
        elif graph == 'ring':
            pairs = [(i, (i + 1) % n_qubits) for i in range(n_qubits)]
        else:
            raise ValueError(f"Unknown graph type: {graph}")

    result = []
    for i, j in pairs:
        for pp in paulis:
            if len(pp) != 2:
                raise ValueError(f"Pauli pair must be 2 characters, got: {pp}")
            pauli_list = ['I'] * n_qubits
            pauli_list[i] = pp[0]
            pauli_list[j] = pp[1]
            result.append(''.join(pauli_list))

    return result


def generate_single_qubit(n_qubits: int, paulis: str = 'XYZ') -> list[str]:
    """Generate single-qubit Pauli strings.

    Args:
        n_qubits: Number of qubits
        paulis: Which Paulis to include (default 'XYZ')

    Returns:
        List of single-qubit Pauli strings
    """
    result = []
    for i in range(n_qubits):
        for p in paulis:
            pauli_list = ['I'] * n_qubits
            pauli_list[i] = p
            result.append(''.join(pauli_list))
    return result


def generate_global_pauli(n_qubits: int, paulis: str = 'XYZ') -> list[str]:
    """Generate global (n-local) Pauli strings.

    Args:
        n_qubits: Number of qubits
        paulis: Which global Paulis (e.g., 'XYZ' -> X^n, Y^n, Z^n)

    Returns:
        List of global Pauli strings
    """
    return [p * n_qubits for p in paulis]


def sample_random_paulis(
    n_qubits: int,
    n_samples: int,
    strategy: Literal['stratified', 'uniform', 'importance', 'uniform_weight'] = 'stratified',
    max_weight: int | None = None,
    seed: int = 42,
) -> list[str]:
    """Sample random Pauli observables using various strategies.

    Strategies:
        'stratified': Equal samples per weight class (best for benchmarking)
        'uniform': Each qubit i.i.d. I/X/Y/Z (biases toward middle weights)
        'importance': Weight k sampled with prob ∝ 1/3^k (matches shadows variance)
        'uniform_weight': Uniform over weight classes, then uniform within

    Args:
        n_qubits: Number of qubits
        n_samples: Number of Paulis to sample
        strategy: Sampling strategy
        max_weight: Maximum Pauli weight (default: n_qubits)
        seed: Random seed

    Returns:
        List of sampled Pauli strings
    """
    rng = np.random.default_rng(seed)
    if max_weight is None:
        max_weight = n_qubits

    sampled = set()
    pauli_ops = ['X', 'Y', 'Z']

    if strategy == 'stratified':
        samples_per_k = max(1, n_samples // max_weight)
        remainder = n_samples - samples_per_k * max_weight

        for k in range(1, max_weight + 1):
            n_at_k = samples_per_k + (1 if k <= remainder else 0)
            max_possible = comb(n_qubits, k) * (3 ** k)

            if n_at_k >= max_possible:
                sampled.update(generate_all_k_local(n_qubits, k))
            else:
                count = 0
                attempts = 0
                while count < n_at_k and attempts < n_at_k * 100:
                    positions = tuple(sorted(rng.choice(n_qubits, k, replace=False)))
                    ops = tuple(rng.choice(pauli_ops, k))
                    pauli_list = ['I'] * n_qubits
                    for pos, op in zip(positions, ops, strict=False):
                        pauli_list[pos] = op
                    pauli = ''.join(pauli_list)
                    if pauli not in sampled:
                        sampled.add(pauli)
                        count += 1
                    attempts += 1

    elif strategy == 'uniform':
        attempts = 0
        while len(sampled) < n_samples and attempts < n_samples * 100:
            pauli_list = rng.choice(['I', 'X', 'Y', 'Z'], n_qubits)
            pauli = ''.join(pauli_list)
            weight = sum(1 for c in pauli if c != 'I')
            if 0 < weight <= max_weight and pauli not in sampled:
                sampled.add(pauli)
            attempts += 1

    elif strategy == 'importance':
        weights = np.array([1.0 / (3 ** k) for k in range(1, max_weight + 1)])
        weights /= weights.sum()

        attempts = 0
        while len(sampled) < n_samples and attempts < n_samples * 100:
            k = rng.choice(range(1, max_weight + 1), p=weights)
            positions = tuple(sorted(rng.choice(n_qubits, k, replace=False)))
            ops = tuple(rng.choice(pauli_ops, k))
            pauli_list = ['I'] * n_qubits
            for pos, op in zip(positions, ops, strict=False):
                pauli_list[pos] = op
            pauli = ''.join(pauli_list)
            if pauli not in sampled:
                sampled.add(pauli)
            attempts += 1

    elif strategy == 'uniform_weight':
        attempts = 0
        while len(sampled) < n_samples and attempts < n_samples * 100:
            k = rng.integers(1, max_weight + 1)
            positions = tuple(sorted(rng.choice(n_qubits, k, replace=False)))
            ops = tuple(rng.choice(pauli_ops, k))
            pauli_list = ['I'] * n_qubits
            for pos, op in zip(positions, ops, strict=False):
                pauli_list[pos] = op
            pauli = ''.join(pauli_list)
            if pauli not in sampled:
                sampled.add(pauli)
            attempts += 1

    else:
        raise ValueError(f"Unknown sampling strategy: {strategy}")

    return list(sampled)


# =============================================================================
# CIRCUIT-SPECIFIC SUITE BUILDERS
# =============================================================================

def make_ghz_suites(n_qubits: int, seed: int = 42) -> dict[str, ObservableSuite]:
    """Create benchmark suites for GHZ state verification.

    GHZ state: |00...0⟩ + |11...1⟩ / √2

    Suites:
        workload_stabilizers: GHZ stabilizer generators (X^n, Z_i Z_j pairs)
        stress_random_1000: 1000 random observables, stratified by weight
        commuting_z_only: All-Z correlators (grouped measurement advantage)
        posthoc_library: 2000 observables for post-hoc querying tests
    """
    suites = {}

    # === WORKLOAD: GHZ Stabilizers ===
    # Stabilizers: X^⊗n, Z_i Z_{i+1} for all i (and optionally all Z_i Z_j)
    stabilizer_paulis = []
    stabilizer_paulis.append('X' * n_qubits)  # Global X parity
    stabilizer_paulis.extend(generate_zz_correlators(n_qubits, graph='all'))  # All ZZ pairs

    suites['workload_stabilizers'] = ObservableSuite.from_pauli_strings(
        name='workload_stabilizers',
        suite_type=SuiteType.WORKLOAD,
        pauli_strings=stabilizer_paulis,
        description=f"GHZ stabilizer generators: X^{n_qubits} + all Z_i Z_j pairs",
    )

    # === STRESS: Random 1000 observables ===
    stress_paulis = sample_random_paulis(
        n_qubits, 1000, strategy='stratified', seed=seed
    )
    suites['stress_random_1000'] = ObservableSuite.from_pauli_strings(
        name='stress_random_1000',
        suite_type=SuiteType.STRESS,
        pauli_strings=stress_paulis,
        description="1000 random Paulis, stratified by weight",
    )

    # === COMMUTING: Z-only correlators ===
    z_paulis = generate_zz_correlators(n_qubits, graph='all')
    z_paulis.extend(generate_single_qubit(n_qubits, paulis='Z'))
    z_paulis.append('Z' * n_qubits)

    suites['commuting_z_only'] = ObservableSuite.from_pauli_strings(
        name='commuting_z_only',
        suite_type=SuiteType.COMMUTING,
        pauli_strings=list(set(z_paulis)),  # Deduplicate
        description="All-Z observables (fully commuting, grouped measurement advantage)",
    )

    # === POSTHOC: Large library for querying tests ===
    posthoc_paulis = sample_random_paulis(
        n_qubits, 2000, strategy='stratified', seed=seed + 1000
    )
    suites['posthoc_library'] = ObservableSuite.from_pauli_strings(
        name='posthoc_library',
        suite_type=SuiteType.POSTHOC,
        pauli_strings=posthoc_paulis,
        description="2000 observables for post-hoc querying benchmark",
    )

    return suites


def make_bell_suites(n_pairs: int, seed: int = 42) -> dict[str, ObservableSuite]:
    """Create benchmark suites for Bell pair verification.

    Bell pairs: ⊗_i (|00⟩ + |11⟩)_i / √2

    Suites:
        workload_pair_correlations: XX, YY, ZZ on each Bell pair
        diagnostics_single_qubit: Single-qubit Z for readout diagnostics
        diagnostics_cross_pair: Cross-pair correlators (crosstalk detection)
        stress_random_1000: Random observables
    """
    n_qubits = 2 * n_pairs
    suites = {}

    # === WORKLOAD: Pair correlations ===
    pair_paulis = []
    for i in range(n_pairs):
        q1, q2 = 2 * i, 2 * i + 1
        for pp in ['XX', 'YY', 'ZZ']:
            pauli_list = ['I'] * n_qubits
            pauli_list[q1] = pp[0]
            pauli_list[q2] = pp[1]
            pair_paulis.append(''.join(pauli_list))

    suites['workload_pair_correlations'] = ObservableSuite.from_pauli_strings(
        name='workload_pair_correlations',
        suite_type=SuiteType.WORKLOAD,
        pauli_strings=pair_paulis,
        description=f"XX, YY, ZZ on each of {n_pairs} Bell pairs",
    )

    # === DIAGNOSTICS: Single-qubit Z ===
    single_z = generate_single_qubit(n_qubits, paulis='Z')
    suites['diagnostics_single_qubit'] = ObservableSuite.from_pauli_strings(
        name='diagnostics_single_qubit',
        suite_type=SuiteType.DIAGNOSTIC,
        pauli_strings=single_z,
        description="Single-qubit Z for readout bias diagnostics",
    )

    # === DIAGNOSTICS: Cross-pair correlators ===
    cross_paulis = []
    for i in range(n_pairs):
        for j in range(i + 1, n_pairs):
            # Z on first qubit of pair i, Z on first qubit of pair j
            pauli_list = ['I'] * n_qubits
            pauli_list[2 * i] = 'Z'
            pauli_list[2 * j] = 'Z'
            cross_paulis.append(''.join(pauli_list))

    if cross_paulis:
        suites['diagnostics_cross_pair'] = ObservableSuite.from_pauli_strings(
            name='diagnostics_cross_pair',
            suite_type=SuiteType.DIAGNOSTIC,
            pauli_strings=cross_paulis,
            description="Cross-pair ZZ correlators for crosstalk detection",
        )

    # === STRESS: Random 1000 ===
    stress_paulis = sample_random_paulis(
        n_qubits, 1000, strategy='stratified', seed=seed
    )
    suites['stress_random_1000'] = ObservableSuite.from_pauli_strings(
        name='stress_random_1000',
        suite_type=SuiteType.STRESS,
        pauli_strings=stress_paulis,
        description="1000 random Paulis, stratified by weight",
    )

    return suites


def make_ising_suites(n_qubits: int, seed: int = 42) -> dict[str, ObservableSuite]:
    """Create benchmark suites for Ising/Trotter physics.

    Transverse-field Ising: H = -J Σ Z_i Z_{i+1} - h Σ X_i

    Suites:
        workload_energy: Hamiltonian terms (ZZ chain + X single-qubit)
        workload_correlations: Z_i Z_j at multiple distances
        stress_random_1000: Random observables
    """
    suites = {}

    # === WORKLOAD: Energy (Hamiltonian terms) ===
    energy_paulis = []
    energy_weights = {}

    # ZZ chain terms (J = 1.0)
    zz_chain = generate_zz_correlators(n_qubits, graph='chain')
    for ps in zz_chain:
        energy_paulis.append(ps)
        energy_weights[ps] = -1.0  # -J

    # X single-qubit terms (h = 0.5)
    x_single = generate_single_qubit(n_qubits, paulis='X')
    for ps in x_single:
        energy_paulis.append(ps)
        energy_weights[ps] = -0.5  # -h

    suites['workload_energy'] = ObservableSuite.from_pauli_strings(
        name='workload_energy',
        suite_type=SuiteType.WORKLOAD,
        pauli_strings=energy_paulis,
        weights=energy_weights,
        objective=ObjectiveType.WEIGHTED_SUM,
        description="Ising Hamiltonian: -J Σ Z_i Z_{i+1} - h Σ X_i",
    )

    # === WORKLOAD: Correlation functions ===
    corr_paulis = []
    for r in range(1, min(n_qubits, 5)):  # Distances 1, 2, 3, 4
        for i in range(n_qubits - r):
            pauli_list = ['I'] * n_qubits
            pauli_list[i] = 'Z'
            pauli_list[i + r] = 'Z'
            corr_paulis.append(''.join(pauli_list))

    suites['workload_correlations'] = ObservableSuite.from_pauli_strings(
        name='workload_correlations',
        suite_type=SuiteType.WORKLOAD,
        pauli_strings=list(set(corr_paulis)),
        description="Z_i Z_j correlators at distances r=1,2,3,4",
    )

    # === STRESS: Random 1000 ===
    stress_paulis = sample_random_paulis(
        n_qubits, 1000, strategy='stratified', seed=seed
    )
    suites['stress_random_1000'] = ObservableSuite.from_pauli_strings(
        name='stress_random_1000',
        suite_type=SuiteType.STRESS,
        pauli_strings=stress_paulis,
        description="1000 random Paulis, stratified by weight",
    )

    return suites


def make_qaoa_ring_suites(n_qubits: int, seed: int = 42) -> dict[str, ObservableSuite]:
    """Create benchmark suites for QAOA MAX-CUT on ring graph.

    Ring graph: edges (i, i+1) for i=0..n-2, PLUS wrap-around (n-1, 0)

    Cost function: C = Σ_e (1 - ⟨Z_i Z_j⟩) / 2

    Suites:
        workload_cost: All edge ZZ terms (INCLUDING wrap-around!)
        commuting_z_only: Same as workload (all commute in Z basis)
        stress_random_1000: Random observables
    """
    suites = {}

    # === WORKLOAD: Cost Hamiltonian ===
    # CRITICAL: Include wrap-around edge (n-1, 0)!
    edge_paulis = generate_zz_correlators(n_qubits, graph='ring')
    edge_weights = dict.fromkeys(edge_paulis, 0.5)  # (1 - ⟨ZZ⟩)/2, so weight is -0.5 on ⟨ZZ⟩

    suites['workload_cost'] = ObservableSuite.from_pauli_strings(
        name='workload_cost',
        suite_type=SuiteType.WORKLOAD,
        pauli_strings=edge_paulis,
        weights=edge_weights,
        objective=ObjectiveType.WEIGHTED_SUM,
        description=f"QAOA ring cost: {n_qubits} edges INCLUDING wrap (n-1,0)",
        metadata={'graph': 'ring', 'includes_wrap': True},
    )

    # === COMMUTING: Same terms (all ZZ commute) ===
    # This shows where grouped direct measurement dominates
    suites['commuting_cost'] = ObservableSuite.from_pauli_strings(
        name='commuting_cost',
        suite_type=SuiteType.COMMUTING,
        pauli_strings=edge_paulis,
        weights=edge_weights,
        objective=ObjectiveType.WEIGHTED_SUM,
        description="Same as workload_cost (all ZZ commute → grouped wins)",
    )

    # === STRESS: Random mixed to show where shadows helps ===
    stress_paulis = sample_random_paulis(
        n_qubits, 1000, strategy='stratified', seed=seed
    )
    suites['stress_random_1000'] = ObservableSuite.from_pauli_strings(
        name='stress_random_1000',
        suite_type=SuiteType.STRESS,
        pauli_strings=stress_paulis,
        description="1000 random Paulis (non-commuting → shadows may help)",
    )

    # === POSTHOC: Library for "measure once, query later" ===
    posthoc_paulis = sample_random_paulis(
        n_qubits, 2000, strategy='stratified', seed=seed + 1000
    )
    suites['posthoc_library'] = ObservableSuite.from_pauli_strings(
        name='posthoc_library',
        suite_type=SuiteType.POSTHOC,
        pauli_strings=posthoc_paulis,
        description="2000 observables for post-hoc querying benchmark",
    )

    return suites


def make_phase_sensing_suites(n_qubits: int, seed: int = 42) -> dict[str, ObservableSuite]:
    """Create benchmark suites for GHZ phase sensing / metrology.

    GHZ state with phase: (|00...0⟩ + e^{inφ}|11...1⟩) / √2

    Key observables for phase estimation:
        - X^⊗n: Real part of off-diagonal coherence
        - Y^⊗n: Imaginary part of off-diagonal coherence

    Suites:
        workload_phase_signal: X^n and Y^n (ALWAYS included for n >= 2)
        workload_stabilizers: Full GHZ stabilizer set
        stress_random_500: Random observables
    """
    suites = {}

    # === WORKLOAD: Phase signal observables ===
    # CRITICAL: Always include Y^n for all n >= 2
    phase_paulis = ['X' * n_qubits, 'Y' * n_qubits]

    suites['workload_phase_signal'] = ObservableSuite.from_pauli_strings(
        name='workload_phase_signal',
        suite_type=SuiteType.WORKLOAD,
        pauli_strings=phase_paulis,
        description=f"Phase sensing: X^{n_qubits} and Y^{n_qubits} (always included)",
        metadata={'includes_Y_global': True},
    )

    # === WORKLOAD: Full stabilizers (for fidelity estimation) ===
    stabilizer_paulis = list(phase_paulis)  # Copy
    stabilizer_paulis.extend(generate_zz_correlators(n_qubits, graph='chain'))

    suites['workload_stabilizers'] = ObservableSuite.from_pauli_strings(
        name='workload_stabilizers',
        suite_type=SuiteType.WORKLOAD,
        pauli_strings=list(set(stabilizer_paulis)),
        description="GHZ stabilizers for fidelity estimation",
    )

    # === STRESS: Random 500 ===
    stress_paulis = sample_random_paulis(
        n_qubits, 500, strategy='stratified', seed=seed
    )
    suites['stress_random_500'] = ObservableSuite.from_pauli_strings(
        name='stress_random_500',
        suite_type=SuiteType.STRESS,
        pauli_strings=stress_paulis,
        description="500 random Paulis for scaling test",
    )

    return suites


def make_chemistry_suites(
    n_qubits: int,
    hamiltonian_terms: list[str] | None = None,
    hamiltonian_coeffs: list[float] | None = None,
    molecule_name: str = "generic",
    seed: int = 42,
) -> dict[str, ObservableSuite]:
    """Create benchmark suites for chemistry / VQE.

    Energy estimation: E = Σ_k c_k ⟨P_k⟩

    Args:
        n_qubits: Number of qubits
        hamiltonian_terms: Pauli strings for Hamiltonian (optional)
        hamiltonian_coeffs: Coefficients for each term (optional)
        molecule_name: Name for labeling (H2, LiH, etc.)
        seed: Random seed

    Suites:
        workload_energy: Hamiltonian terms with weights (if provided)
        stress_random_1000: Random observables
    """
    suites = {}

    # === WORKLOAD: Energy ===
    if hamiltonian_terms and hamiltonian_coeffs:
        weights = dict(zip(hamiltonian_terms, hamiltonian_coeffs, strict=False))
        suites['workload_energy'] = ObservableSuite.from_pauli_strings(
            name='workload_energy',
            suite_type=SuiteType.WORKLOAD,
            pauli_strings=hamiltonian_terms,
            weights=weights,
            objective=ObjectiveType.WEIGHTED_SUM,
            description=f"{molecule_name} Hamiltonian energy estimation",
        )
    else:
        # Placeholder: use random 2-local as proxy for molecular Hamiltonian
        placeholder_paulis = generate_zz_correlators(n_qubits, graph='all')
        placeholder_paulis.extend(generate_single_qubit(n_qubits, paulis='XYZ'))

        suites['workload_energy_placeholder'] = ObservableSuite.from_pauli_strings(
            name='workload_energy_placeholder',
            suite_type=SuiteType.WORKLOAD,
            pauli_strings=placeholder_paulis,
            description=f"{molecule_name} placeholder (use actual Hamiltonian when available)",
            metadata={'is_placeholder': True},
        )

    # === STRESS: Random 1000 ===
    stress_paulis = sample_random_paulis(
        n_qubits, 1000, strategy='stratified', seed=seed
    )
    suites['stress_random_1000'] = ObservableSuite.from_pauli_strings(
        name='stress_random_1000',
        suite_type=SuiteType.STRESS,
        pauli_strings=stress_paulis,
        description="1000 random Paulis, stratified by weight",
    )

    return suites


# =============================================================================
# GENERIC SUITE GENERATORS
# =============================================================================

def make_stress_suite(
    n_qubits: int,
    n_observables: int = 1000,
    strategy: str = 'stratified',
    seed: int = 42,
    name: str | None = None,
) -> ObservableSuite:
    """Create a stress test suite with many observables.

    Args:
        n_qubits: Number of qubits
        n_observables: Number of observables to sample
        strategy: Sampling strategy ('stratified', 'uniform', 'importance')
        seed: Random seed
        name: Suite name (auto-generated if None)
    """
    paulis = sample_random_paulis(n_qubits, n_observables, strategy=strategy, seed=seed)

    if name is None:
        name = f"stress_{strategy}_{n_observables}"

    return ObservableSuite.from_pauli_strings(
        name=name,
        suite_type=SuiteType.STRESS,
        pauli_strings=paulis,
        description=f"{n_observables} observables, {strategy} sampling",
    )


def make_posthoc_library(
    n_qubits: int,
    n_observables: int = 2000,
    seed: int = 42,
    name: str | None = None,
) -> ObservableSuite:
    """Create a post-hoc querying library.

    Args:
        n_qubits: Number of qubits
        n_observables: Library size
        seed: Random seed
        name: Suite name
    """
    paulis = sample_random_paulis(n_qubits, n_observables, strategy='stratified', seed=seed)

    if name is None:
        name = f"posthoc_library_{n_observables}"

    return ObservableSuite.from_pauli_strings(
        name=name,
        suite_type=SuiteType.POSTHOC,
        pauli_strings=paulis,
        description=f"Library of {n_observables} observables for post-hoc querying tests",
    )


def make_commuting_suite(
    n_qubits: int,
    basis: Literal['Z', 'X', 'Y'] = 'Z',
    include_global: bool = True,
    name: str | None = None,
) -> ObservableSuite:
    """Create an all-commuting suite (grouped measurement advantage).

    Args:
        n_qubits: Number of qubits
        basis: Which Pauli basis ('Z', 'X', or 'Y')
        include_global: Include global string (e.g., Z^n)
        name: Suite name
    """
    # All single-qubit in this basis
    paulis = generate_single_qubit(n_qubits, paulis=basis)

    # All 2-local in this basis
    for i in range(n_qubits):
        for j in range(i + 1, n_qubits):
            pauli_list = ['I'] * n_qubits
            pauli_list[i] = basis
            pauli_list[j] = basis
            paulis.append(''.join(pauli_list))

    if include_global:
        paulis.append(basis * n_qubits)

    if name is None:
        name = f"commuting_{basis}_only"

    return ObservableSuite.from_pauli_strings(
        name=name,
        suite_type=SuiteType.COMMUTING,
        pauli_strings=list(set(paulis)),
        description=f"All-{basis} observables (fully commuting)",
    )
