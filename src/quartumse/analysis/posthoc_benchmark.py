"""Post-hoc querying benchmark mode.

This module simulates the "measure once, decide observables later" scenario,
which is the core advantage of classical shadows over direct measurement.

Key concept:
- Shadows: quantum cost = one acquisition run; new queries cost 0 quantum shots
- Direct: new queries may require additional shots if not covered by prior bases

This allows us to quantify the "option value" of shadows.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class QueryRound:
    """A single round of observable queries."""
    round_id: int
    observable_ids: list[str]
    n_observables: int = 0

    def __post_init__(self):
        self.n_observables = len(self.observable_ids)


@dataclass
class PosthocCostAccounting:
    """Cost accounting for a single protocol in post-hoc mode."""
    protocol_id: str

    # Per-round costs
    shots_per_round: list[int] = field(default_factory=list)
    cumulative_shots: list[int] = field(default_factory=list)

    # Per-round coverage
    observables_answered_per_round: list[int] = field(default_factory=list)
    cumulative_observables_answered: list[int] = field(default_factory=list)

    # Error tracking (observables meeting epsilon)
    observables_at_epsilon_per_round: list[int] = field(default_factory=list)
    cumulative_at_epsilon: list[int] = field(default_factory=list)


@dataclass
class CoverageAtBudget:
    """Coverage metrics at a fixed shot budget."""

    shot_budget: int
    total_observables: int

    # Per-protocol coverage
    shadows_observables_covered: int = 0
    shadows_observables_at_epsilon: int = 0
    direct_observables_covered: int = 0
    direct_observables_at_epsilon: int = 0

    # Coverage percentages
    shadows_coverage_pct: float = 0.0
    direct_coverage_pct: float = 0.0


@dataclass
class PosthocBenchmarkResult:
    """Complete results from a post-hoc benchmark."""

    # Library info
    library_size: int
    n_rounds: int
    observables_per_round: int

    # Per-protocol accounting
    shadows_costs: PosthocCostAccounting | None = None
    direct_costs: PosthocCostAccounting | None = None

    # Summary metrics
    shadows_total_shots: int = 0
    direct_total_shots: int = 0
    shot_savings_factor: float = 1.0  # direct_shots / shadows_shots

    # Break-even analysis
    breakeven_round: int | None = None  # Round where shadows becomes cheaper
    breakeven_observables: int | None = None

    # Coverage at fixed budgets
    coverage_at_budgets: list[CoverageAtBudget] = field(default_factory=list)


def compute_coverage_at_budget(
    shadows_costs: PosthocCostAccounting,
    direct_costs: PosthocCostAccounting,
    library_size: int,
    shot_budget: int,
) -> CoverageAtBudget:
    """Compute how many observables each protocol can answer at a fixed shot budget.

    Args:
        shadows_costs: Shadows cost accounting
        direct_costs: Direct measurement cost accounting
        library_size: Total observables in library
        shot_budget: Fixed quantum shot budget

    Returns:
        CoverageAtBudget with coverage metrics
    """
    # For shadows: after paying acquisition cost, all observables are covered
    shadows_covered = 0
    if shadows_costs.cumulative_shots:
        # Find how many rounds we can afford
        for i, cum_shots in enumerate(shadows_costs.cumulative_shots):
            if cum_shots <= shot_budget:
                shadows_covered = shadows_costs.cumulative_observables_answered[i]

    # For direct: find how many observables we can cover
    direct_covered = 0
    if direct_costs.cumulative_shots:
        for i, cum_shots in enumerate(direct_costs.cumulative_shots):
            if cum_shots <= shot_budget:
                direct_covered = direct_costs.cumulative_observables_answered[i]

    return CoverageAtBudget(
        shot_budget=shot_budget,
        total_observables=library_size,
        shadows_observables_covered=shadows_covered,
        shadows_observables_at_epsilon=shadows_covered,  # Simplified: assume all covered meet ε
        direct_observables_covered=direct_covered,
        direct_observables_at_epsilon=direct_covered,
        shadows_coverage_pct=100 * shadows_covered / library_size if library_size > 0 else 0,
        direct_coverage_pct=100 * direct_covered / library_size if library_size > 0 else 0,
    )


def generate_query_rounds(
    library_observable_ids: list[str],
    n_rounds: int = 5,
    observables_per_round: int = 50,
    strategy: str = "random",
    seed: int = 42,
) -> list[QueryRound]:
    """Generate query rounds from a library.

    Args:
        library_observable_ids: All observable IDs in the library
        n_rounds: Number of query rounds
        observables_per_round: Observables requested per round
        strategy: "random" (i.i.d. draws), "sequential" (fixed order),
                  "structured" (e.g., increasing locality)
        seed: Random seed

    Returns:
        List of QueryRound objects
    """
    rng = np.random.default_rng(seed)
    library = list(library_observable_ids)

    rounds = []

    if strategy == "random":
        # Random draws without replacement across rounds
        rng.shuffle(library)
        for i in range(n_rounds):
            start = i * observables_per_round
            end = start + observables_per_round
            obs_ids = library[start:end] if end <= len(library) else library[start:]
            rounds.append(QueryRound(round_id=i, observable_ids=obs_ids))

    elif strategy == "sequential":
        # Fixed sequential order
        for i in range(n_rounds):
            start = i * observables_per_round
            end = start + observables_per_round
            obs_ids = library[start:end] if end <= len(library) else library[start:]
            rounds.append(QueryRound(round_id=i, observable_ids=obs_ids))

    elif strategy == "structured":
        # Could implement locality-based ordering, etc.
        # For now, same as random
        rng.shuffle(library)
        for i in range(n_rounds):
            start = i * observables_per_round
            end = start + observables_per_round
            obs_ids = library[start:end] if end <= len(library) else library[start:]
            rounds.append(QueryRound(round_id=i, observable_ids=obs_ids))

    return rounds


def compute_direct_measurement_coverage(
    observable_ids: list[str],
    measurement_bases: dict[str, set[str]],
) -> tuple[set[str], set[str]]:
    """Determine which observables are covered by existing measurement bases.

    For direct measurement, an observable is "covered" if it can be estimated
    from an existing measurement basis (i.e., it commutes with/is compatible
    with measurements already taken).

    Args:
        observable_ids: Observables we want to estimate
        measurement_bases: Dict mapping basis_id -> set of compatible observable_ids

    Returns:
        Tuple of (covered_obs_ids, uncovered_obs_ids)
    """
    requested = set(observable_ids)
    covered = set()

    for _basis_id, compatible in measurement_bases.items():
        covered.update(requested & compatible)

    uncovered = requested - covered
    return covered, uncovered


def simulate_posthoc_benchmark(
    library_observable_ids: list[str],
    query_rounds: list[QueryRound],
    shadows_shots_per_acquisition: int,
    direct_shots_per_basis: int,
    observable_to_basis: dict[str, str] | None = None,
    basis_to_observables: dict[str, set[str]] | None = None,
) -> PosthocBenchmarkResult:
    """Simulate post-hoc querying benchmark.

    Args:
        library_observable_ids: All observables in the library
        query_rounds: List of QueryRound defining the query process
        shadows_shots_per_acquisition: Shots for one shadows acquisition
        direct_shots_per_basis: Shots per measurement basis for direct
        observable_to_basis: Maps observable_id -> measurement basis needed
        basis_to_observables: Maps basis_id -> set of observables measurable in that basis

    Returns:
        PosthocBenchmarkResult with cost accounting for both protocols
    """
    n_rounds = len(query_rounds)
    library_size = len(library_observable_ids)
    obs_per_round = query_rounds[0].n_observables if query_rounds else 0

    # === SHADOWS ACCOUNTING ===
    # Shadows: pay once for acquisition, all queries are "free"
    shadows = PosthocCostAccounting(protocol_id="classical_shadows")

    shadows_paid = False
    for i, qr in enumerate(query_rounds):
        if not shadows_paid:
            # First round: pay for acquisition
            shadows.shots_per_round.append(shadows_shots_per_acquisition)
            shadows_paid = True
        else:
            # Subsequent rounds: 0 quantum cost
            shadows.shots_per_round.append(0)

        # All observables in library are "answerable" after acquisition
        shadows.observables_answered_per_round.append(qr.n_observables)

        # Cumulative
        if i == 0:
            shadows.cumulative_shots.append(shadows.shots_per_round[0])
            shadows.cumulative_observables_answered.append(qr.n_observables)
        else:
            shadows.cumulative_shots.append(shadows.cumulative_shots[-1] + shadows.shots_per_round[i])
            shadows.cumulative_observables_answered.append(
                shadows.cumulative_observables_answered[-1] + qr.n_observables
            )

    # === DIRECT MEASUREMENT ACCOUNTING ===
    # Direct: need to pay for each new basis that isn't already measured
    direct = PosthocCostAccounting(protocol_id="direct_grouped")

    # Track which bases have been measured
    measured_bases: set[str] = set()

    # If no basis mapping provided, assume each observable needs its own basis
    # (worst case for direct measurement)
    if observable_to_basis is None:
        # Simple model: each unique Pauli string is its own "basis"
        observable_to_basis = {obs_id: obs_id for obs_id in library_observable_ids}

    if basis_to_observables is None:
        # Inverse mapping
        basis_to_observables = {}
        for obs_id, basis in observable_to_basis.items():
            if basis not in basis_to_observables:
                basis_to_observables[basis] = set()
            basis_to_observables[basis].add(obs_id)

    for i, qr in enumerate(query_rounds):
        # Determine which bases are needed for this round's observables
        needed_bases = set()
        for obs_id in qr.observable_ids:
            if obs_id in observable_to_basis:
                basis = observable_to_basis[obs_id]
                if basis not in measured_bases:
                    needed_bases.add(basis)

        # Cost = shots per new basis
        round_cost = len(needed_bases) * direct_shots_per_basis
        direct.shots_per_round.append(round_cost)

        # Update measured bases
        measured_bases.update(needed_bases)

        # All requested observables are answered (assuming we pay for needed bases)
        direct.observables_answered_per_round.append(qr.n_observables)

        # Cumulative
        if i == 0:
            direct.cumulative_shots.append(round_cost)
            direct.cumulative_observables_answered.append(qr.n_observables)
        else:
            direct.cumulative_shots.append(direct.cumulative_shots[-1] + round_cost)
            direct.cumulative_observables_answered.append(
                direct.cumulative_observables_answered[-1] + qr.n_observables
            )

    # === SUMMARY ===
    shadows_total = shadows.cumulative_shots[-1] if shadows.cumulative_shots else 0
    direct_total = direct.cumulative_shots[-1] if direct.cumulative_shots else 0

    savings = direct_total / shadows_total if shadows_total > 0 else float('inf')

    # Find break-even round (where shadows becomes cheaper cumulatively)
    breakeven_round = None
    breakeven_obs = None
    for i in range(n_rounds):
        if (shadows.cumulative_shots[i] < direct.cumulative_shots[i]):
            breakeven_round = i
            breakeven_obs = shadows.cumulative_observables_answered[i]
            break

    # Compute coverage at various fixed budgets
    budget_points = [
        shadows_total // 2,  # Half shadows cost
        shadows_total,        # Full shadows cost
        shadows_total * 2,    # 2x shadows cost
        direct_total // 2,    # Half direct cost
        direct_total,         # Full direct cost
    ]
    # Remove duplicates and sort
    budget_points = sorted({b for b in budget_points if b > 0})

    coverage_at_budgets = [
        compute_coverage_at_budget(shadows, direct, library_size, budget)
        for budget in budget_points
    ]

    return PosthocBenchmarkResult(
        library_size=library_size,
        n_rounds=n_rounds,
        observables_per_round=obs_per_round,
        shadows_costs=shadows,
        direct_costs=direct,
        shadows_total_shots=shadows_total,
        direct_total_shots=direct_total,
        shot_savings_factor=savings,
        breakeven_round=breakeven_round,
        breakeven_observables=breakeven_obs,
        coverage_at_budgets=coverage_at_budgets,
    )


def format_posthoc_result(result: PosthocBenchmarkResult) -> str:
    """Format post-hoc benchmark result for display."""
    lines = []
    lines.append("POST-HOC QUERYING BENCHMARK")
    lines.append("=" * 70)
    lines.append(f"Library size: {result.library_size} observables")
    lines.append(f"Query rounds: {result.n_rounds}")
    lines.append(f"Observables per round: {result.observables_per_round}")
    lines.append("")

    # Per-round breakdown
    lines.append(f"{'Round':<8} {'Shadows Shots':>15} {'Direct Shots':>15} {'Obs Queried':>12}")
    lines.append("-" * 55)

    shadows = result.shadows_costs
    direct = result.direct_costs

    if shadows and direct:
        for i in range(result.n_rounds):
            lines.append(
                f"{i:<8} {shadows.shots_per_round[i]:>15,} {direct.shots_per_round[i]:>15,} "
                f"{shadows.observables_answered_per_round[i]:>12}"
            )

    lines.append("-" * 55)
    lines.append(f"{'TOTAL':<8} {result.shadows_total_shots:>15,} {result.direct_total_shots:>15,}")
    lines.append("")

    # Summary
    lines.append(f"Shot savings factor: {result.shot_savings_factor:.1f}x")
    lines.append(f"  (Direct uses {result.shot_savings_factor:.1f}x more shots than Shadows)")

    if result.breakeven_round is not None:
        lines.append("\nBreak-even point:")
        lines.append(f"  Round {result.breakeven_round} ({result.breakeven_observables} observables)")
        lines.append("  After this, shadows has lower cumulative quantum cost")
    else:
        lines.append("\nNo break-even: Direct is always cheaper (fully commuting observables?)")

    # Coverage at fixed budgets
    if result.coverage_at_budgets:
        lines.append("\nCOVERAGE AT FIXED SHOT BUDGETS:")
        lines.append(f"{'Budget':>12} {'Shadows':>12} {'Direct':>12} {'Shadows %':>12} {'Direct %':>12}")
        lines.append("-" * 65)
        for cov in result.coverage_at_budgets:
            lines.append(
                f"{cov.shot_budget:>12,} {cov.shadows_observables_covered:>12} "
                f"{cov.direct_observables_covered:>12} {cov.shadows_coverage_pct:>11.1f}% "
                f"{cov.direct_coverage_pct:>11.1f}%"
            )

    return "\n".join(lines)


def run_posthoc_benchmark_from_suite(
    posthoc_suite,  # ObservableSuite with suite_type=POSTHOC
    n_rounds: int = 5,
    observables_per_round: int | None = None,
    shadows_shots: int = 1000,
    direct_shots_per_basis: int = 100,
    seed: int = 42,
) -> PosthocBenchmarkResult:
    """Run post-hoc benchmark using a posthoc library suite.

    Args:
        posthoc_suite: ObservableSuite with POSTHOC type
        n_rounds: Number of query rounds
        observables_per_round: Observables per round (default: library_size // n_rounds)
        shadows_shots: Total shots for shadows acquisition
        direct_shots_per_basis: Shots per measurement basis for direct
        seed: Random seed

    Returns:
        PosthocBenchmarkResult
    """
    # Get observable IDs from suite
    library_ids = [obs.observable_id for obs in posthoc_suite.observables]
    library_size = len(library_ids)

    if observables_per_round is None:
        observables_per_round = max(1, library_size // n_rounds)

    # Generate query rounds
    rounds = generate_query_rounds(
        library_observable_ids=library_ids,
        n_rounds=n_rounds,
        observables_per_round=observables_per_round,
        strategy="random",
        seed=seed,
    )

    # Build basis mapping from observable Pauli strings
    # For simplicity: observables with same non-identity positions can share a basis
    # In practice, this depends on grouping strategy
    observable_to_basis = {}
    basis_to_observables = {}

    for obs in posthoc_suite.observables:
        # Use the Pauli string's "basis" (Z positions) as grouping key
        # This is a simplification - real grouping is more complex
        pauli = obs.pauli_string

        # Extract measurement basis (which qubits in which Pauli basis)
        # For now, use the full string as the basis (conservative)
        basis = pauli

        observable_to_basis[obs.observable_id] = basis
        if basis not in basis_to_observables:
            basis_to_observables[basis] = set()
        basis_to_observables[basis].add(obs.observable_id)

    # Run simulation
    return simulate_posthoc_benchmark(
        library_observable_ids=library_ids,
        query_rounds=rounds,
        shadows_shots_per_acquisition=shadows_shots,
        direct_shots_per_basis=direct_shots_per_basis,
        observable_to_basis=observable_to_basis,
        basis_to_observables=basis_to_observables,
    )
