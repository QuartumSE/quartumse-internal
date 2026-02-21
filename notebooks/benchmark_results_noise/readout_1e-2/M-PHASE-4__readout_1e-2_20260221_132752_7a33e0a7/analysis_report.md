# Comprehensive Benchmark Analysis

**Run ID:** M-PHASE-4__readout_1e-2_20260221_132752_7a33e0a7
**Protocols:** classical_shadows_v0, direct_optimized, direct_grouped
**Observables:** 91
**Shot Grid:** [5000, 10000, 20000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 91
- **n_shots_evaluated:** 3
- **max_shots:** 20000
- **shadows_mean_se:** 0.036763435350249035
- **baseline_mean_se:** 0.037165049375200904
- **shadows_vs_baseline_ratio:** 0.9891937712527337
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.6373626373626373
- **baseline_wins_fraction:** 0.3626373626373626
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
- selection_accuracy: 0.2
- regret: 0.0025856542296829495
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 5000 | 0.5374 | 0.0000 | No | 1.02 [0.95, 1.10] |
| 10000 | 0.4884 | 0.0000 | No | 1.03 [0.96, 1.11] |
| 20000 | 0.5548 | 0.0000 | No | 1.02 [0.95, 1.10] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 63.7% of observables
- Protocol B (direct_grouped) wins on 36.3% of observables
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

- **direct_grouped:** N* = 11046 (R² = 1.000)
- **direct_optimized:** N* = 9563 (R² = 1.000)
- **classical_shadows_v0:** N* = 10788 (R² = 1.000)
