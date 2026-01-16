# Comprehensive Benchmark Analysis

**Run ID:** ghz_4q_20260116_143354_67eda61e
**Protocols:** classical_shadows_v0, direct_optimized, direct_grouped
**Observables:** 17
**Shot Grid:** [100, 500, 1000, 5000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 17
- **n_shots_evaluated:** 4
- **max_shots:** 5000
- **shadows_mean_se:** 0.04988172748557596
- **baseline_mean_se:** 0.041406007259915174
- **shadows_vs_baseline_ratio:** 1.2046978394332184
- **winner_at_max_n:** direct_grouped
- **shadows_wins_fraction:** 0.5882352941176471
- **baseline_wins_fraction:** 0.4117647058823529
- **optimal_pilot_fraction:** 0.1

---

## Task Results

### Worst Case


**Enhanced Analysis:**

### Average Target


### Fixed Budget


### Dominance

- crossover_n: None
- always_a_better: False
- always_b_better: True
- metric_used: mean_se

### Pilot Selection

- pilot_n: 100
- target_n: 5000
- selection_accuracy: 0.35
- regret: 0.008575461060696957
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.0000 | 0.0000 | Yes | 0.73 [0.64, 0.83] |
| 500 | 0.0000 | 0.0000 | Yes | 0.71 [0.63, 0.80] |
| 1000 | 0.0000 | 0.0000 | Yes | 0.70 [0.62, 0.79] |
| 5000 | 0.0000 | 0.0000 | Yes | 0.69 [0.61, 0.77] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 58.8% of observables
- Protocol B (direct_grouped) wins on 41.2% of observables
- Crossover exists for 0.0% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 90.0% | 0.0003 |
| 5% | 90.0% | 0.0003 |
| 10% | 100.0% | 0.0000 |
| 20% | 100.0% | 0.0000 |

**Optimal pilot fraction:** 10%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 82793 (R² = 1.000)
- **direct_optimized:** N* = 71799 (R² = 1.000)
- **classical_shadows_v0:** N* = 129817 (R² = 1.000)
