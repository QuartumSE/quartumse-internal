# Comprehensive Benchmark Analysis

**Run ID:** S-BELL-2__readout_1e-2_20260219_184525_29df7d2e
**Protocols:** direct_optimized, classical_shadows_v0, direct_grouped
**Observables:** 87
**Shot Grid:** [5000, 10000, 20000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 87
- **n_shots_evaluated:** 3
- **max_shots:** 20000
- **shadows_mean_se:** 0.03654621797733701
- **baseline_mean_se:** 0.039048221960447334
- **shadows_vs_baseline_ratio:** 0.9359252775799971
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.6781609195402298
- **baseline_wins_fraction:** 0.3218390804597701
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
- selection_accuracy: 0.1
- regret: 0.005087265236472105
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 5000 | 0.0002 | 0.0000 | Yes | 1.14 [1.06, 1.23] |
| 10000 | 0.0000 | 0.0000 | Yes | 1.15 [1.07, 1.24] |
| 20000 | 0.0000 | 0.0000 | Yes | 1.14 [1.06, 1.23] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 67.8% of observables
- Protocol B (direct_grouped) wins on 32.2% of observables
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

- **direct_grouped:** N* = 12191 (R² = 1.000)
- **direct_optimized:** N* = 10823 (R² = 1.000)
- **classical_shadows_v0:** N* = 10659 (R² = 1.000)
