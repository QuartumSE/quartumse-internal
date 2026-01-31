# Comprehensive Benchmark Analysis

**Run ID:** M-PHASE-3__stress_random_500_20260130_225754_16f44471
**Protocols:** direct_grouped, direct_optimized, classical_shadows_v0
**Observables:** 63
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 63
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.11811456186005928
- **baseline_mean_se:** 0.1471057987085366
- **shadows_vs_baseline_ratio:** 0.8029225421227739
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.5555555555555556
- **baseline_wins_fraction:** 0.14285714285714285
- **optimal_pilot_fraction:** 0.2

---

## Task Results

### Worst Case


**Enhanced Analysis:**

### Average Target


### Fixed Budget


### Dominance

- crossover_n: None
- always_a_better: True
- always_b_better: False
- metric_used: mean_se

### Pilot Selection

- pilot_n: 100
- target_n: 1000
- selection_accuracy: 0.7
- regret: 0.008454885460261092
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.0000 | 0.0000 | Yes | 1.51 [1.33, 1.72] |
| 200 | 0.0000 | 0.0000 | Yes | 1.63 [1.50, 1.78] |
| 1000 | 0.0000 | 0.0000 | Yes | 1.55 [1.44, 1.67] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 55.6% of observables
- Protocol B (direct_grouped) wins on 14.3% of observables
- Crossover exists for 20.6% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 40.0% | 0.0138 |
| 5% | 40.0% | 0.0138 |
| 10% | 40.0% | 0.0138 |
| 20% | 90.0% | 0.0014 |

**Optimal pilot fraction:** 20%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 10501 (R² = 0.998)
- **direct_optimized:** N* = 10255 (R² = 0.996)
- **classical_shadows_v0:** N* = 5893 (R² = 1.000)
