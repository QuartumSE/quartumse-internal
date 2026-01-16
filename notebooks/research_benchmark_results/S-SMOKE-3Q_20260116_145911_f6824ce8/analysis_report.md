# Comprehensive Benchmark Analysis

**Run ID:** S-SMOKE-3Q_20260116_145911_f6824ce8
**Protocols:** classical_shadows_v0, direct_grouped, direct_optimized
**Observables:** 7
**Shot Grid:** [100, 500, 1000, 5000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 7
- **n_shots_evaluated:** 4
- **max_shots:** 5000
- **shadows_mean_se:** 0.04274056445960207
- **baseline_mean_se:** 0.01142842213522822
- **shadows_vs_baseline_ratio:** 3.739848244479339
- **winner_at_max_n:** direct_grouped
- **shadows_wins_fraction:** 0.0
- **baseline_wins_fraction:** 1.0
- **optimal_pilot_fraction:** 0.02

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
- selection_accuracy: 0.4
- regret: 0.0033995975855130784
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.0000 | 0.0000 | Yes | 0.07 [0.04, 0.12] |
| 500 | 0.0000 | 0.0000 | Yes | 0.07 [0.04, 0.11] |
| 1000 | 0.0000 | 0.0000 | Yes | 0.07 [0.05, 0.11] |
| 5000 | 0.0000 | 0.0000 | Yes | 0.07 [0.04, 0.11] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 0.0% of observables
- Protocol B (direct_grouped) wins on 100.0% of observables
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

- **direct_grouped:** N* = 6559 (R² = 1.000)
- **direct_optimized:** N* = 4609 (R² = 1.000)
- **classical_shadows_v0:** N* = 90724 (R² = 1.000)
