"""Notebook A: Protocol Comparison (Measurements Bible §12).

This notebook demonstrates the basic protocol comparison workflow
per the Measurements Bible methodology.

Sections:
1. Setup and observable generation
2. Protocol execution
3. Results analysis
4. Visualization
5. Report generation

To run as a notebook:
    jupyter nbconvert --to notebook --execute notebook_a_protocol_comparison.py
"""

# %% [markdown]
# # Notebook A: Protocol Comparison
#
# This notebook compares baseline measurement protocols following the
# Measurements Bible methodology.

# %% Setup
import numpy as np
import sys
sys.path.insert(0, "../src")

from quartumse.observables import generate_observable_set, partition_observable_set
from quartumse.protocols import (
    DirectNaiveProtocol,
    DirectGroupedProtocol,
    DirectOptimizedProtocol,
)
from quartumse.stats import construct_simultaneous_cis, FWERMethod
from quartumse.benchmarking import (
    quick_comparison,
    compute_ssf,
    simulate_protocol_execution,
)

# Set random seed for reproducibility
SEED = 42
np.random.seed(SEED)

# %% [markdown]
# ## 1. Observable Generation
#
# Generate a set of random Pauli observables per §3.3.

# %% Observable Generation
# Configuration
N_QUBITS = 4
N_OBSERVABLES = 20

# Generate observables
observable_set = generate_observable_set(
    generator_id="random_pauli",
    n_qubits=N_QUBITS,
    n_observables=N_OBSERVABLES,
    seed=SEED,
    max_weight=3,
)

print(f"Generated {len(observable_set)} observables on {observable_set.n_qubits} qubits")
print(f"Locality distribution: {observable_set.locality_distribution()}")
print(f"Mean locality: {observable_set.mean_locality():.2f}")

# %% [markdown]
# ## 2. Commuting Group Analysis
#
# Partition observables into commuting groups for the grouped baseline (§4.1B).

# %% Grouping Analysis
groups, stats = partition_observable_set(observable_set, method="greedy")

print(f"\nGrouping Statistics:")
print(f"  Number of groups: {stats['n_groups']}")
print(f"  Min group size: {stats['min_group_size']}")
print(f"  Max group size: {stats['max_group_size']}")
print(f"  Mean group size: {stats['mean_group_size']:.2f}")

# Show first few groups
print(f"\nFirst 3 groups:")
for g in groups[:3]:
    print(f"  {g.group_id}: {g.size} observables, basis={g.measurement_basis[:8]}...")

# %% [markdown]
# ## 3. Protocol Comparison
#
# Compare the three baseline protocols at a fixed shot budget.

# %% Protocol Comparison
N_SHOTS = 1000

# Create protocols
protocols = {
    "direct_naive": DirectNaiveProtocol(),
    "direct_grouped": DirectGroupedProtocol(),
    "direct_optimized": DirectOptimizedProtocol(),
}

# Generate "true" expectations for evaluation
rng = np.random.default_rng(SEED)
true_expectations = {
    obs.observable_id: rng.uniform(-0.5, 0.5)
    for obs in observable_set.observables
}

# Run comparison
results = quick_comparison(
    observable_set=observable_set,
    protocols=list(protocols.values()),
    n_shots=N_SHOTS,
    seed=SEED,
    true_expectations=true_expectations,
)

# %% [markdown]
# ## 4. Results Analysis
#
# Analyze the estimation results.

# %% Results Analysis
print(f"\nResults at N={N_SHOTS} shots:")
print("-" * 60)

for protocol_id, estimates in results.items():
    se_values = [e.se for e in estimates.estimates]
    print(f"\n{protocol_id}:")
    print(f"  Mean SE: {np.mean(se_values):.4f}")
    print(f"  Max SE:  {np.max(se_values):.4f}")
    print(f"  Min SE:  {np.min(se_values):.4f}")
    print(f"  Median SE: {np.median(se_values):.4f}")
    print(f"  Num settings: {estimates.estimates[0].n_settings}")

# %% SSF Computation
# Compute shot-savings factor relative to direct_grouped baseline
ssf = compute_ssf(results, baseline_id="direct_grouped", metric="mean_se")

print(f"\nShot-Savings Factor (vs direct_grouped):")
for protocol_id, ssf_value in ssf.items():
    print(f"  {protocol_id}: {ssf_value:.2f}x")

# %% [markdown]
# ## 5. Confidence Intervals with FWER Control
#
# Construct simultaneous confidence intervals per §6.3.

# %% FWER-Controlled CIs
ALPHA = 0.05  # Global significance level

# Get estimates from best protocol
best_protocol = min(results.keys(), key=lambda p: np.mean([e.se for e in results[p].estimates]))
best_estimates = results[best_protocol]

estimates_list = [e.estimate for e in best_estimates.estimates]
ses_list = [e.se for e in best_estimates.estimates]

# Construct simultaneous CIs
sim_cis = construct_simultaneous_cis(
    estimates=estimates_list,
    standard_errors=ses_list,
    alpha=ALPHA,
    fwer_method=FWERMethod.BONFERRONI,
)

print(f"\nSimultaneous CIs ({best_protocol}, α={ALPHA}):")
print(f"  FWER method: {sim_cis.fwer_adjustment.method.value}")
print(f"  Coverage guarantee: {sim_cis.coverage_guarantee:.1%}")
print(f"  Individual CI confidence: {sim_cis.fwer_adjustment.confidence_individual[0]:.4f}")

# Check coverage against truth
if true_expectations:
    truths = [true_expectations[e.observable_id] for e in best_estimates.estimates]
    coverage = sim_cis.coverage_fraction(truths)
    all_covered = sim_cis.all_contain(truths)
    print(f"\n  Empirical coverage: {coverage:.1%}")
    print(f"  Family-wise coverage: {all_covered}")

# %% [markdown]
# ## 6. Summary Table
#
# Create a summary table in tidy format per §10.1.

# %% Summary Table
print("\n" + "=" * 70)
print("SUMMARY TABLE")
print("=" * 70)
print(f"{'Protocol':<20} {'Mean SE':<12} {'Max SE':<12} {'SSF':<10}")
print("-" * 70)
for protocol_id in results:
    estimates = results[protocol_id]
    se_values = [e.se for e in estimates.estimates]
    ssf_val = ssf.get(protocol_id, 1.0)
    print(f"{protocol_id:<20} {np.mean(se_values):<12.4f} {np.max(se_values):<12.4f} {ssf_val:<10.2f}x")
print("=" * 70)

# %% [markdown]
# ## Conclusions
#
# This notebook demonstrated:
# 1. Observable generation with reproducible seeds
# 2. Commuting group analysis for baseline protocols
# 3. Protocol comparison at fixed shot budget
# 4. FWER-controlled simultaneous confidence intervals
# 5. Shot-savings factor computation
#
# The methodology follows Measurements Bible requirements for
# reproducibility, strong baselines, and proper statistical inference.
