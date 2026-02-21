# Comprehensive Benchmark Analysis

**Run ID:** C-LiH__depol_low_20260221_150007_72f5c700
**Protocols:** classical_shadows_v0, direct_optimized, direct_grouped
**Observables:** 116
**Shot Grid:** [5000, 10000, 20000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 116
- **n_shots_evaluated:** 3
- **max_shots:** 20000
- **shadows_mean_se:** 0.06314075104033257
- **baseline_mean_se:** 0.04089763292939538
- **shadows_vs_baseline_ratio:** 1.5438729950297398
- **winner_at_max_n:** direct_grouped
- **shadows_wins_fraction:** 0.45689655172413796
- **baseline_wins_fraction:** 0.5431034482758621
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

- pilot_n: 5000
- target_n: 20000
- selection_accuracy: 0.4
- regret: 0.0031114563553434004
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 5000 | 0.0000 | 0.0000 | Yes | 0.41 [0.37, 0.47] |
| 10000 | 0.0000 | 0.0000 | Yes | 0.41 [0.37, 0.47] |
| 20000 | 0.0000 | 0.0000 | Yes | 0.42 [0.37, 0.47] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 45.7% of observables
- Protocol B (direct_grouped) wins on 54.3% of observables
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

- **direct_grouped:** N* = 13454 (R² = 1.000)
- **direct_optimized:** N* = 11727 (R² = 1.000)
- **classical_shadows_v0:** N* = 31922 (R² = 1.000)
