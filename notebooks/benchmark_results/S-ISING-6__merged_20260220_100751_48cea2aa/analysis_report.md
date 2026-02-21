# Comprehensive Benchmark Analysis

**Run ID:** S-ISING-6__merged_20260220_100751_48cea2aa
**Protocols:** classical_shadows_v0, direct_optimized, direct_grouped
**Observables:** 115
**Shot Grid:** [5000, 10000, 20000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 115
- **n_shots_evaluated:** 3
- **max_shots:** 20000
- **shadows_mean_se:** 0.06371851040744547
- **baseline_mean_se:** 0.04660668367375851
- **shadows_vs_baseline_ratio:** 1.3671539226748637
- **winner_at_max_n:** direct_grouped
- **shadows_wins_fraction:** 0.5739130434782609
- **baseline_wins_fraction:** 0.4260869565217391
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
- selection_accuracy: 0.8
- regret: 0.0020496694082190537
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 5000 | 0.0000 | 0.0000 | Yes | 0.52 [0.47, 0.58] |
| 10000 | 0.0000 | 0.0000 | Yes | 0.52 [0.47, 0.58] |
| 20000 | 0.0000 | 0.0000 | Yes | 0.54 [0.48, 0.60] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 57.4% of observables
- Protocol B (direct_grouped) wins on 42.6% of observables
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

- **direct_grouped:** N* = 17381 (R² = 1.000)
- **direct_optimized:** N* = 13701 (R² = 1.000)
- **classical_shadows_v0:** N* = 32500 (R² = 1.000)
