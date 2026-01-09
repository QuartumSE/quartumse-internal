# Benchmarking Improvement Analysis

This document reviews the fairness and completeness of the QuartumSE benchmarking infrastructure and proposes improvements for more rigorous protocol comparisons.

## Executive Summary

The current benchmarking infrastructure (based on the Measurements Bible) is **well-designed** with:
- Unified protocol interface (5-method contract)
- Strong baselines (DirectGrouped required)
- Deterministic seeding for reproducibility
- Comprehensive artifact generation (long-form, summary, manifest)
- 8-task evaluation suite

However, there are opportunities to improve fairness and extract deeper insights from the data already being collected.

---

## Current Benchmark Approaches

### Implemented Tasks (Measurements Bible §8)

| Task | Name | Description | Status |
|------|------|-------------|--------|
| 1 | Worst-Case Guarantee | Min N where ALL observables meet target | ✅ `WorstCaseTask` |
| 2 | Average Target | Min N where mean SE meets target | ✅ `AverageTargetTask` |
| 3 | Fixed-Budget Distribution | Compare error distributions at fixed N | ✅ `FixedBudgetDistributionTask` |
| 4 | Dominance & Crossover | Find where protocol A beats B | ✅ `DominanceTask` |
| 5 | Pilot Selection | Use x% of shots to choose protocol | ✅ `PilotSelectionTask` |
| 6 | Bias-Variance | Decompose estimation error | ✅ `BiasVarianceTask` |
| 7 | Noise Sensitivity | Robustness to noise profiles | ✅ `NoiseSensitivityTask` |
| 8 | Adaptive Efficiency | Evaluate adaptive protocols | ✅ `AdaptiveEfficiencyTask` |

---

## Detailed Analysis of Comparison Approaches

### 1. Fix Worst-Case Error (Task 1)

**Definition:** Keep adding shots until ALL observables are below a fixed target of standard error, then compare total shots.

**Current Implementation:** `src/quartumse/tasks/task1_worstcase.py`
- Computes N* such that `max_i(SE_i) ≤ ε` with probability `1-δ`
- Uses FWER correction (Bonferroni by default)
- Identifies blocking observable (worst performer)

**Fairness Considerations:**
- This is the **best case for brute force** methods (DirectNaive/Grouped)
- Shadows can suffer from high-variance observables dragging down the whole protocol
- Example from GHZ benchmark: DirectGrouped max_se=0.045 vs Shadows max_se=0.153

**Sophistication Improvements:**

| Enhancement | Effort | Value | Description |
|-------------|--------|-------|-------------|
| Interpolate N* | Medium | High | Fit power-law (`SE ∝ N^{-0.5}`) to avoid grid quantization |
| 95th percentile target | Low | High | More robust than strict max |
| Per-observable N* | Low | Medium | Track which observables need most shots |
| Alternative FWER methods | Low | Low | Holm, Hochberg (already parameterized) |

**Implementation Notes:**
```python
# Current: Grid search for N*
for n in sorted_ns:
    if max_se(n) <= epsilon:
        return n

# Improved: Interpolation
from scipy.optimize import brentq
def se_at_n(n):
    return a * n**(-0.5)  # Fit from data
n_star = brentq(lambda n: se_at_n(n) - epsilon, n_min, n_max)
```

---

### 2. Fix Mean Standard Error (Task 2)

**Definition:** Target mean SE across observables instead of per-observable.

**Current Implementation:** `src/quartumse/tasks/task2_average_target.py`
- Computes N* where `mean(SE_i) ≤ ε`
- More lenient than worst-case

**Fairness Considerations:**
- **Favors shadows** which can have low median but high worst-case
- From GHZ benchmark:
  - Shadows: median_se=0.043, mean_se=0.057
  - DirectGrouped: median_se=0.045, mean_se=0.036

**Sophistication Improvements:**

| Enhancement | Effort | Value | Description |
|-------------|--------|-------|-------------|
| Weighted means | Low | High | Weight by observable importance/application relevance |
| Median SE target | Trivial | High | Robust to outliers |
| L_p norm targets | Low | Medium | `(Σ SE_i^p)^{1/p}` interpolates between mean (p=1) and max (p→∞) |
| Trimmed mean | Low | Medium | Exclude top/bottom 5% |

---

### 3. Fix Shot Budget, Compare Errors (Task 3)

**Definition:** Fix the shot budget and compare errors (mean and distribution).

**Current Implementation:** `src/quartumse/tasks/task3_distribution.py`
- Primary mode of current benchmarks
- Reports: mean_se, max_se, median_se, mean_abs_error, max_abs_error

**Fairness Considerations:**
- Most straightforward comparison (equal resources → compare outcomes)
- Misses the question "how many resources does each need to achieve X?"

**Sophistication Improvements:**

| Enhancement | Effort | Value | Description |
|-------------|--------|-------|-------------|
| K-S test | Medium | High | Statistical test for distribution differences |
| Per-observable heatmap | Low | High | Visualize where each protocol wins |
| Q-Q plots | Low | Medium | Compare distributional shapes |
| Bootstrap CIs on summaries | Medium | High | Uncertainty quantification on comparisons |

**Visualization Ideas:**
```python
# Per-observable comparison heatmap
# Rows: observables, Columns: protocols
# Color: SE or rank

# Distribution comparison
from scipy.stats import ks_2samp
stat, pvalue = ks_2samp(se_protocol_a, se_protocol_b)
```

---

### 4. Dominance and Crossover (Task 4)

**Definition:** How many shots are necessary for one protocol to beat the other across ALL observables.

**Current Implementation:** `src/quartumse/tasks/task4_dominance.py`
- `compare_protocols()` method
- Returns: crossover_n, a_dominates_at, b_dominates_at, blocking_observables
- Supports metrics: mean_se, max_se, median_se, mean_error, max_error

**GHZ Benchmark Results:**
```python
{
    'crossover_n': None,           # No crossover found
    'a_dominates_at': [],          # Shadows never wins
    'b_dominates_at': [100, 500, 1000, 5000],  # Grouped always wins
    'blocking_observables': ['obs_b3f1d11a', ...]  # 10+ observables blocking
}
```

**Fairness Considerations:**
- Most stringent comparison (requires uniform dominance)
- "Blocking observables" reveal why protocol can't win

**Sophistication Improvements:**

| Enhancement | Effort | Value | Description |
|-------------|--------|-------|-------------|
| Per-observable crossover | Medium | Very High | At what N does A beat B for each observable? |
| Interpolate crossover | Medium | High | Precision between grid points |
| Statistical significance | Medium | High | Bootstrap test for dominance |
| Pareto frontier | Low | High | Multi-metric visualization |
| Soft dominance | Low | High | "Wins on 90%+ observables" criterion |

**Per-Observable Crossover Table:**
```
Observable | A beats B at N | B beats A at N | Notes
-----------|----------------|----------------|-------
obs_001    | 500            | never          | Easy for A
obs_002    | never          | always         | Hard for A
obs_003    | 2000           | never          | Late crossover
```

---

### 5. Pilot-Based Selection (Task 5)

**Definition:** Use the first x% of shots to estimate which protocol would be best, then evaluate regret.

**Current Implementation:** `src/quartumse/tasks/task5_pilot_selection.py`
- Uses pilot_n to select protocol
- Compares to oracle choice at target_n
- Reports selection_accuracy and regret

**GHZ Benchmark Results:**
- Config: pilot_n=100, target_n=5000
- Selection accuracy: ~60%
- With 4 protocols, random would be 25%

**Fairness Considerations:**
- Tests "online" decision-making with limited information
- 60% accuracy suggests pilot signal is weak at 100 shots

**Sophistication Improvements:**

| Enhancement | Effort | Value | Description |
|-------------|--------|-------|-------------|
| Multiple pilot fractions | Low | Very High | Test 2%, 5%, 10%, 20% of budget |
| Bayesian selection | High | High | Principled uncertainty handling |
| Risk-adjusted | Medium | High | Mean-variance tradeoff |
| Sequential testing | High | Medium | Adaptive pilot with early stopping |
| Cross-validation | Medium | Medium | Reduce selection variance |

**Pilot Fraction Analysis:**
```python
pilot_fractions = [0.02, 0.05, 0.10, 0.20]
for frac in pilot_fractions:
    pilot_n = int(frac * target_n)
    accuracy = run_pilot_selection(pilot_n, target_n)
    print(f"{frac*100}% pilot: {accuracy:.1%} accuracy")
```

---

## Additional Benchmarks to Implement

### 6. Sample Complexity Curves

**Description:** Plot SE(N) or error(N) for each protocol.

**Data Status:** Available in long-form results, needs visualization.

**Value:** Visual intuition for scaling behavior. Shadows might win asymptotically.

**Implementation:**
```python
import matplotlib.pyplot as plt

for protocol in protocols:
    ns = sorted(results_by_n.keys())
    mean_ses = [np.mean([r.se for r in results_by_n[n] if r.protocol_id == protocol]) for n in ns]
    plt.loglog(ns, mean_ses, label=protocol)

plt.xlabel('Shots (N)')
plt.ylabel('Mean SE')
plt.legend()
```

---

### 7. Observable-Property Analysis

**Description:** Analyze performance as function of observable properties.

**Properties to Analyze:**
- **Locality (Pauli weight):** Shadows variance scales with weight
- **Commutation structure:** Grouped wins when observables highly commute
- **Coefficient magnitude:** Affects signal-to-noise
- **Support overlap:** Which qubits the observable acts on

**Implementation:**
```python
# Group observables by locality
by_locality = {}
for obs in observable_set:
    locality = sum(1 for c in obs.pauli_string if c != 'I')
    by_locality.setdefault(locality, []).append(obs.observable_id)

# Compare protocol performance per locality group
for locality, obs_ids in by_locality.items():
    subset_rows = [r for r in long_form if r.observable_id in obs_ids]
    # Compute metrics for each protocol on this subset
```

---

### 8. Per-Observable Crossover Points

**Description:** For each observable individually, at what N does protocol A beat B?

**Value:** Identifies which observables are "easy" vs "hard" for each protocol.

**Implementation:**
```python
def per_observable_crossover(results_a, results_b, observable_ids):
    crossovers = {}
    for obs_id in observable_ids:
        obs_a = [r for r in results_a if r.observable_id == obs_id]
        obs_b = [r for r in results_b if r.observable_id == obs_id]
        # Find N where SE_a < SE_b
        for n in sorted_ns:
            se_a = get_se(obs_a, n)
            se_b = get_se(obs_b, n)
            if se_a < se_b:
                crossovers[obs_id] = n
                break
    return crossovers
```

---

### 9. Cost-Normalized Comparison

**Description:** Account for circuit depth overhead in comparisons.

**Current Status:** Circuit depth is tracked (`circuit_depth`, `twoq_gate_count`) but not penalized.

**Issue:** Shadows with random Cliffords have:
- More gates per measurement
- Higher noise sensitivity in practice
- Should compare `error / (N × effective_cost)` not just `error / N`

**Implementation:**
```python
# Define cost model
def compute_cost(n_shots, circuit_depth, twoq_gates, noise_factor=1.0):
    base_cost = n_shots
    depth_penalty = 1 + 0.01 * circuit_depth  # Example
    gate_penalty = 1 + 0.005 * twoq_gates
    return base_cost * depth_penalty * gate_penalty * noise_factor

# Normalize metrics by cost
cost_normalized_se = se / compute_cost(...)
```

---

### 10. Bootstrap Hypothesis Testing

**Description:** Statistical significance of protocol differences.

**Quantities to Test:**
- `SE_A - SE_B` at each N
- `N*_A - N*_B`
- SSF confidence intervals

**Implementation:**
```python
from scipy.stats import bootstrap

def se_difference(results_a, results_b):
    return np.mean([r.se for r in results_a]) - np.mean([r.se for r in results_b])

# Bootstrap CI
rng = np.random.default_rng(42)
res = bootstrap((results_a, results_b), se_difference,
                n_resamples=10000, random_state=rng, paired=True)
ci = res.confidence_interval
```

---

## Fairness Assessment

### What's Already Fair

| Aspect | Status | Notes |
|--------|--------|-------|
| Same shot budgets | ✅ | All protocols get identical N_total |
| Same observable set | ✅ | Shared across all protocols |
| Same circuit/truth | ✅ | Ground truth computed once |
| Deterministic seeding | ✅ | Full reproducibility |
| Strong baseline | ✅ | DirectGrouped required, not just DirectNaive |
| Multiple replicates | ✅ | 20 replicates for statistical power |
| Multiple metrics | ✅ | mean, max, median SE tracked |
| Settings tracking | ✅ | n_settings recorded per estimate |

### Potential Fairness Gaps

| Issue | Impact | Current Status | Recommendation |
|-------|--------|----------------|----------------|
| Circuit depth not penalized | Shadows may look better than reality | Tracked but not in comparisons | Add cost-normalized metrics |
| Observable set may favor grouping | GHZ stabilizers highly commute | Single test case | Add adversarial observable sets |
| Small qubit count (4) | Shadows expected to win at scale | Limited testing | Add 6, 8, 10 qubit benchmarks |
| Fixed ε=0.01 | Different optimal ε per protocol | Single target | Add ε sweep |
| No significance tests | Differences might be noise | Not implemented | Add bootstrap testing |
| No interpolation | N* quantized to grid | Grid search only | Fit power-law for interpolation |

---

## Recommendations

### Immediate Improvements (Can Run Now)

1. **Run dominance with `max_se` metric** instead of `mean_error`
   - More fair for worst-case guarantees
   - Current notebook uses `mean_error`

2. **Add pilot fractions 5%, 10%, 20%** to Task 5
   - Find where pilot selection becomes reliable
   - Current: only 100 shots (2% of 5000)

3. **Generate per-observable performance table**
   - Identify which observables each protocol struggles with
   - Data already available

### Publication-Grade Improvements

4. **Interpolate N*** between grid points
   - Fit `SE ∝ N^{-0.5}` power law
   - Avoid reporting quantized N* values

5. **Add statistical significance**
   - Bootstrap CIs on SSF
   - Hypothesis tests for dominance claims

6. **Scale to more qubits** (6, 8, 10)
   - Shadows theoretically shine at larger scales
   - Current 4-qubit results may not generalize

### Deep Understanding Improvements

7. **Observable property analysis**
   - Correlate performance with locality, commutation
   - Explain *why* each protocol wins/loses

8. **Adversarial observable sets**
   - Design sets where shadows should theoretically win
   - Low commutation, high locality

9. **Cost-normalized comparisons**
   - Penalize circuit depth
   - More realistic for hardware deployment

---

## Summary: Benchmark Capability Matrix

| Approach | Implemented | Data Ready | Sophistication Available |
|----------|-------------|------------|--------------------------|
| 1. Fix worst-case SE | ✅ Task 1 | ✅ | Interpolation, percentiles |
| 2. Fix mean SE | ✅ Task 2 | ✅ | Weighted, median, L_p norms |
| 3. Fix budget, compare | ✅ Task 3 | ✅ | K-S tests, heatmaps, bootstrap |
| 4. Dominance crossover | ✅ Task 4 | ✅ | Per-observable, significance |
| 5. Pilot selection | ✅ Task 5 | ✅ | Multiple fractions, Bayesian |
| 6. Sample complexity curves | ⚠️ Data only | ✅ | Needs plotting code |
| 7. Observable property analysis | ❌ | ✅ | Needs implementation |
| 8. Per-observable crossover | ❌ | ✅ | Needs implementation |
| 9. Cost-normalized | ⚠️ Partial | ✅ | Needs weighting logic |
| 10. Bootstrap significance | ❌ | ✅ | Needs implementation |

---

## Conclusion

The QuartumSE benchmarking infrastructure is well-designed and follows rigorous methodology. The main gaps are:

1. **Interpretive analysis** — data is collected but not deeply analyzed for *why* protocols differ
2. **Statistical rigor** — no significance testing on comparisons
3. **Cost fairness** — circuit depth overhead not penalized
4. **Scale testing** — limited to 4 qubits where shadows are expected to underperform

Addressing these gaps will strengthen publication claims and provide actionable insights for protocol selection in real applications.

---

*Document created: 2025-01-09*
*Based on analysis of GHZ shadows benchmark (notebook_j) and Measurements Bible specification*
