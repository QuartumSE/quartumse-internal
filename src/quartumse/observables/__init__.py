"""Observable representations and generators (Measurements Bible §3).

This package provides:
- Observable and ObservableSet classes with full metadata (§3.2)
- Seeded observable generators for reproducible benchmarks (§3.3)
- Commutation analysis and grouping utilities (§4.1B)

Usage:
    from quartumse.observables import (
        Observable,
        ObservableSet,
        generate_observable_set,
        partition_observable_set,
    )

    # Create from Pauli strings
    obs_set = ObservableSet.from_pauli_strings(["XXII", "YYII", "ZZII"])

    # Generate random observables
    obs_set = generate_observable_set(
        generator_id="random_pauli",
        n_qubits=4,
        n_observables=100,
        seed=42,
        weight_distribution="uniform",
    )

    # Partition into commuting groups
    groups, stats = partition_observable_set(obs_set)
"""

from .core import (
    Observable,
    ObservableSet,
    ObservableType,
)
from .generators import (
    ClusteredSupportGenerator,
    CorrelatorGenerator,
    GeneratorConfig,
    HamiltonianGenerator,
    ObservableGenerator,
    RandomPauliGenerator,
    generate_observable_set,
    get_generator,
    list_generators,
)
from .grouping import (
    CommutingGroup,
    build_commutation_graph,
    build_qubitwise_commutation_graph,
    greedy_grouping,
    partition_observable_set,
    pauli_commutes,
    qubitwise_commutes,
    shared_measurement_basis,
    sorted_insertion_grouping,
    verify_grouping,
)
from .suites import (
    ObjectiveType,
    # Core classes
    ObservableSuite,
    SuiteType,
    # Pauli string generators
    generate_all_k_local,
    generate_edge_correlators,
    generate_global_pauli,
    generate_single_qubit,
    generate_zz_correlators,
    make_bell_suites,
    make_chemistry_suites,
    make_commuting_suite,
    # Circuit-specific suite builders
    make_ghz_suites,
    make_ising_suites,
    make_phase_sensing_suites,
    make_posthoc_library,
    make_qaoa_ring_suites,
    # Generic suite builders
    make_stress_suite,
    sample_random_paulis,
)

__all__ = [
    # Core classes
    "Observable",
    "ObservableSet",
    "ObservableType",
    # Generators
    "ObservableGenerator",
    "GeneratorConfig",
    "RandomPauliGenerator",
    "HamiltonianGenerator",
    "CorrelatorGenerator",
    "ClusteredSupportGenerator",
    "generate_observable_set",
    "get_generator",
    "list_generators",
    # Grouping
    "CommutingGroup",
    "pauli_commutes",
    "qubitwise_commutes",
    "shared_measurement_basis",
    "build_commutation_graph",
    "build_qubitwise_commutation_graph",
    "greedy_grouping",
    "sorted_insertion_grouping",
    "partition_observable_set",
    "verify_grouping",
    # Suites (Benchmarking)
    "ObservableSuite",
    "ObjectiveType",
    "SuiteType",
    "generate_all_k_local",
    "generate_zz_correlators",
    "generate_edge_correlators",
    "generate_single_qubit",
    "generate_global_pauli",
    "sample_random_paulis",
    "make_ghz_suites",
    "make_bell_suites",
    "make_ising_suites",
    "make_qaoa_ring_suites",
    "make_phase_sensing_suites",
    "make_chemistry_suites",
    "make_stress_suite",
    "make_posthoc_library",
    "make_commuting_suite",
]
