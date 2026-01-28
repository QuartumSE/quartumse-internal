"""Task-level objective metrics for weighted observable suites.

This module computes aggregate metrics for suites with weighted objectives:
- QAOA cost estimation: C = Σ w_e (1 - ⟨Z_i Z_j⟩) / 2
- Chemistry energy estimation: E = Σ c_k ⟨P_k⟩

For these tasks, the relevant metric is the error in the *objective*, not
individual observable errors.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class ObjectiveEstimate:
    """Result of estimating a weighted objective."""

    # Point estimate
    estimate: float

    # Uncertainty quantification
    se: float | None = None  # Standard error (from bootstrap or analytic)
    ci_low: float | None = None  # 95% CI lower bound
    ci_high: float | None = None  # 95% CI upper bound

    # Comparison to truth
    true_value: float | None = None
    abs_error: float | None = None
    rel_error: float | None = None

    # Metadata
    n_observables: int = 0
    n_shots: int = 0
    protocol_id: str = ""


@dataclass
class ObjectiveAnalysis:
    """Complete objective-level analysis for a weighted suite."""

    # Per-protocol estimates at each shot budget
    estimates_by_protocol: dict[str, dict[int, ObjectiveEstimate]] = field(default_factory=dict)

    # N* for objective (shots needed to reach target error)
    n_star_objective: dict[str, int | None] = field(default_factory=dict)

    # Protocol comparison
    winner_at_max_n: str = ""
    objective_ratio: float = 1.0  # shadows_error / baseline_error

    # Metadata
    objective_type: str = ""  # "qaoa_cost", "energy", etc.
    target_epsilon: float = 0.01


def compute_weighted_objective(
    observable_estimates: dict[str, float],
    weights: dict[str, float],
    objective_type: str = "weighted_sum",
) -> float:
    """Compute a weighted objective from observable estimates.

    Args:
        observable_estimates: Dict mapping observable_id -> estimate value
        weights: Dict mapping observable_id -> coefficient
        objective_type: Type of objective transformation
            - "weighted_sum": E = Σ c_k ⟨P_k⟩
            - "qaoa_cost": C = Σ w_e (1 - ⟨Z_i Z_j⟩) / 2

    Returns:
        The computed objective value.
    """
    if objective_type == "qaoa_cost":
        # QAOA MAX-CUT cost: C = Σ (1 - ⟨Z_i Z_j⟩) / 2
        # Weights are edge weights (default 1.0)
        total = 0.0
        for obs_id, weight in weights.items():
            if obs_id in observable_estimates:
                expectation = observable_estimates[obs_id]
                total += weight * (1 - expectation) / 2
        return total
    else:
        # Generic weighted sum: E = Σ c_k ⟨P_k⟩
        total = 0.0
        for obs_id, coeff in weights.items():
            if obs_id in observable_estimates:
                total += coeff * observable_estimates[obs_id]
        return total


def bootstrap_objective_ci(
    replicate_estimates: list[dict[str, float]],
    weights: dict[str, float],
    objective_type: str = "weighted_sum",
    n_bootstrap: int = 1000,
    confidence: float = 0.95,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Compute bootstrap confidence interval for objective.

    Args:
        replicate_estimates: List of dicts, each mapping observable_id -> estimate
            for one replicate
        weights: Dict mapping observable_id -> coefficient
        objective_type: Type of objective ("weighted_sum" or "qaoa_cost")
        n_bootstrap: Number of bootstrap samples
        confidence: Confidence level (default 0.95)
        seed: Random seed

    Returns:
        Tuple of (se, ci_low, ci_high)
    """
    rng = np.random.default_rng(seed)
    n_replicates = len(replicate_estimates)

    if n_replicates < 2:
        # Can't bootstrap with fewer than 2 replicates
        return None, None, None

    # Compute objective for each replicate
    objective_values = [
        compute_weighted_objective(rep, weights, objective_type) for rep in replicate_estimates
    ]

    # Bootstrap resampling
    bootstrap_means = []
    for _ in range(n_bootstrap):
        indices = rng.choice(n_replicates, size=n_replicates, replace=True)
        sample = [objective_values[i] for i in indices]
        bootstrap_means.append(np.mean(sample))

    # Compute statistics
    se = np.std(bootstrap_means)
    alpha = 1 - confidence
    ci_low = np.percentile(bootstrap_means, 100 * alpha / 2)
    ci_high = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))

    return se, ci_low, ci_high


def compute_objective_metrics(
    long_form_results: list,
    weights: dict[str, float],
    objective_type: str = "weighted_sum",
    true_objective: float | None = None,
    target_epsilon: float = 0.01,
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> ObjectiveAnalysis:
    """Compute objective-level metrics from benchmark results.

    Args:
        long_form_results: List of LongFormRow from benchmark
        weights: Dict mapping observable_id -> coefficient
        objective_type: "weighted_sum" or "qaoa_cost"
        true_objective: Ground truth objective value (if known)
        target_epsilon: Target error for N* computation
        n_bootstrap: Bootstrap samples for CI
        seed: Random seed

    Returns:
        ObjectiveAnalysis with per-protocol metrics
    """
    # Group results by (protocol, N, replicate)
    by_protocol_n_rep = {}
    for row in long_form_results:
        key = (row.protocol_id, row.N_total, row.replicate)
        if key not in by_protocol_n_rep:
            by_protocol_n_rep[key] = {}
        by_protocol_n_rep[key][row.observable_id] = row.estimate

    # Get unique protocols and shot counts
    protocols = sorted({row.protocol_id for row in long_form_results})
    shot_counts = sorted({row.N_total for row in long_form_results})

    analysis = ObjectiveAnalysis(
        objective_type=objective_type,
        target_epsilon=target_epsilon,
    )

    for protocol in protocols:
        analysis.estimates_by_protocol[protocol] = {}

        for n_shots in shot_counts:
            # Gather all replicates for this (protocol, N)
            replicate_estimates = []
            for (p, n, _rep), obs_dict in by_protocol_n_rep.items():
                if p == protocol and n == n_shots:
                    replicate_estimates.append(obs_dict)

            if not replicate_estimates:
                continue

            # Compute objective for each replicate
            objective_values = [
                compute_weighted_objective(rep, weights, objective_type)
                for rep in replicate_estimates
            ]

            # Point estimate (mean across replicates)
            estimate = np.mean(objective_values)

            # Bootstrap CI
            se, ci_low, ci_high = bootstrap_objective_ci(
                replicate_estimates,
                weights,
                objective_type,
                n_bootstrap=n_bootstrap,
                seed=seed,
            )

            # Comparison to truth
            abs_error = None
            rel_error = None
            if true_objective is not None:
                abs_error = abs(estimate - true_objective)
                if abs(true_objective) > 1e-10:
                    rel_error = abs_error / abs(true_objective)

            analysis.estimates_by_protocol[protocol][n_shots] = ObjectiveEstimate(
                estimate=estimate,
                se=se,
                ci_low=ci_low,
                ci_high=ci_high,
                true_value=true_objective,
                abs_error=abs_error,
                rel_error=rel_error,
                n_observables=len(weights),
                n_shots=n_shots,
                protocol_id=protocol,
            )

        # Compute N* for objective
        n_star = None
        for n_shots in shot_counts:
            if n_shots in analysis.estimates_by_protocol[protocol]:
                est = analysis.estimates_by_protocol[protocol][n_shots]
                if est.se is not None and est.se <= target_epsilon:
                    n_star = n_shots
                    break
        analysis.n_star_objective[protocol] = n_star

    # Determine winner at max N
    max_n = max(shot_counts)
    best_protocol = None
    best_se = float("inf")

    for protocol in protocols:
        if max_n in analysis.estimates_by_protocol[protocol]:
            est = analysis.estimates_by_protocol[protocol][max_n]
            if est.se is not None and est.se < best_se:
                best_se = est.se
                best_protocol = protocol

    analysis.winner_at_max_n = best_protocol or ""

    # Compute ratio (shadows / baseline)
    shadows_se = None
    baseline_se = None
    for protocol in protocols:
        if max_n in analysis.estimates_by_protocol[protocol]:
            est = analysis.estimates_by_protocol[protocol][max_n]
            if "shadows" in protocol.lower():
                shadows_se = est.se
            elif "grouped" in protocol.lower() or "direct" in protocol.lower():
                baseline_se = est.se

    if shadows_se is not None and baseline_se is not None and baseline_se > 0:
        analysis.objective_ratio = shadows_se / baseline_se

    return analysis


def format_objective_analysis(analysis: ObjectiveAnalysis) -> str:
    """Format objective analysis for display."""
    lines = []
    lines.append(f"OBJECTIVE ANALYSIS ({analysis.objective_type})")
    lines.append("=" * 60)

    # Get shot counts
    shot_counts = set()
    for protocol_data in analysis.estimates_by_protocol.values():
        shot_counts.update(protocol_data.keys())
    shot_counts = sorted(shot_counts)
    max_n = max(shot_counts) if shot_counts else 0

    # Summary at max N
    lines.append(f"\nAt N={max_n}:")
    for protocol, estimates in analysis.estimates_by_protocol.items():
        if max_n in estimates:
            est = estimates[max_n]
            short_name = protocol.replace("classical_shadows_v0", "shadows").replace("direct_", "")

            se_str = f"SE={est.se:.4f}" if est.se is not None else "SE=N/A"
            ci_str = ""
            if est.ci_low is not None and est.ci_high is not None:
                ci_str = f" 95%CI=[{est.ci_low:.4f}, {est.ci_high:.4f}]"

            err_str = ""
            if est.abs_error is not None:
                err_str = f" |err|={est.abs_error:.4f}"

            lines.append(f"  {short_name}: Ê={est.estimate:.4f} {se_str}{ci_str}{err_str}")

    # N* for objective
    lines.append(f"\nN* for objective (SE <= {analysis.target_epsilon}):")
    for protocol, n_star in analysis.n_star_objective.items():
        short_name = protocol.replace("classical_shadows_v0", "shadows").replace("direct_", "")
        n_str = f"N*={n_star}" if n_star else f"N*>{max_n}"
        lines.append(f"  {short_name}: {n_str}")

    # Winner
    lines.append(f"\nWinner at max N: {analysis.winner_at_max_n}")
    lines.append(f"Ratio (shadows/baseline): {analysis.objective_ratio:.2f}x")

    return "\n".join(lines)
