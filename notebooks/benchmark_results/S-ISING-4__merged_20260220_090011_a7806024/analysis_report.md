# Comprehensive Benchmark Analysis

**Run ID:** S-ISING-4__merged_20260220_090011_a7806024
**Protocols:** classical_shadows_v0, direct_optimized, direct_grouped
**Observables:** 89
**Shot Grid:** [5000, 10000, 20000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 89
- **n_shots_evaluated:** 3
- **max_shots:** 20000
- **shadows_mean_se:** 0.03617091251190693
- **baseline_mean_se:** 0.03777875753458653
- **shadows_vs_baseline_ratio:** 0.9574405002280021
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.6629213483146067
- **baseline_wins_fraction:** 0.29213483146067415
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

- pilot_n: 5000
- target_n: 20000
- selection_accuracy: 0.5
- regret: 0.0019997637430462763
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 5000 | 0.0068 | 0.0000 | Yes | 1.10 [1.02, 1.18] |
| 10000 | 0.0070 | 0.0000 | Yes | 1.10 [1.02, 1.18] |
| 20000 | 0.0110 | 0.0000 | Yes | 1.09 [1.02, 1.17] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 66.3% of observables
- Protocol B (direct_grouped) wins on 29.2% of observables
- Crossover exists for 0.0% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 100.0% | 0.0000 |
| 5% | 100.0% | 0.0000 |
| 10% | 100.0% | 0.0000 |
| 20% | 100.0% | 0.0000 |

**Optimal pilot fraction:** 2%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 11436 (R² = 1.000)
- **direct_optimized:** N* = 10003 (R² = 1.000)
- **classical_shadows_v0:** N* = 10441 (R² = 1.000)
