# Comprehensive Benchmark Analysis

**Run ID:** C-H2__stress_random_1000_20260130_210353_b35154ac
**Protocols:** direct_grouped, direct_optimized, classical_shadows_v0
**Observables:** 87
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 87
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.16114611817478433
- **baseline_mean_se:** 0.1633997121117885
- **shadows_vs_baseline_ratio:** 0.9862080911411741
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.5287356321839081
- **baseline_wins_fraction:** 0.3448275862068966
- **optimal_pilot_fraction:** 0.02

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
- selection_accuracy: 0.4
- regret: 0.01996252257024784
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.2270 | 0.0000 | No | 1.08 [0.95, 1.23] |
| 200 | 0.0016 | 0.0000 | Yes | 1.16 [1.06, 1.29] |
| 1000 | 0.4922 | 0.0000 | No | 1.03 [0.95, 1.11] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 52.9% of observables
- Protocol B (direct_grouped) wins on 34.5% of observables
- Crossover exists for 10.3% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 70.0% | 0.0043 |
| 5% | 70.0% | 0.0043 |
| 10% | 70.0% | 0.0043 |
| 20% | 70.0% | 0.0037 |

**Optimal pilot fraction:** 2%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 14350 (R² = 0.996)
- **direct_optimized:** N* = 19144 (R² = 0.977)
- **classical_shadows_v0:** N* = 12870 (R² = 1.000)
