# Comprehensive Benchmark Analysis

**Run ID:** M-PHASE-3__depol_low_20260221_173059_df628c58
**Protocols:** classical_shadows_v0, direct_optimized, direct_grouped
**Observables:** 63
**Shot Grid:** [5000, 10000, 20000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 63
- **n_shots_evaluated:** 3
- **max_shots:** 20000
- **shadows_mean_se:** 0.026482968740446124
- **baseline_mean_se:** 0.033343423341354046
- **shadows_vs_baseline_ratio:** 0.7942486429580471
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.5873015873015873
- **baseline_wins_fraction:** 0.20634920634920634
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
- selection_accuracy: 0.4
- regret: 0.00230931050173014
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 5000 | 0.0000 | 0.0000 | Yes | 1.58 [1.47, 1.70] |
| 10000 | 0.0000 | 0.0000 | Yes | 1.58 [1.47, 1.70] |
| 20000 | 0.0000 | 0.0000 | Yes | 1.59 [1.48, 1.70] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 58.7% of observables
- Protocol B (direct_grouped) wins on 20.6% of observables
- Crossover exists for 14.3% of observables

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

- **direct_grouped:** N* = 8865 (R² = 1.000)
- **direct_optimized:** N* = 7489 (R² = 1.000)
- **classical_shadows_v0:** N* = 5607 (R² = 1.000)
