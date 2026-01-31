# Comprehensive Benchmark Analysis

**Run ID:** O-QAOA-7__merged_20260130_224211_213a14d1
**Protocols:** direct_grouped, direct_optimized, classical_shadows_v0
**Observables:** 275
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 275
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.4048277996952669
- **baseline_mean_se:** 0.35001842960710206
- **shadows_vs_baseline_ratio:** 1.1565899548480596
- **winner_at_max_n:** direct_grouped
- **shadows_wins_fraction:** 0.5490909090909091
- **baseline_wins_fraction:** 0.4509090909090909
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
- target_n: 1000
- selection_accuracy: 0.1
- regret: 0.08965254952889365
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.0000 | nan | Yes | nan [nan, nan] |
| 200 | 0.0000 | nan | Yes | nan [nan, nan] |
| 1000 | 0.0000 | 0.0000 | Yes | 0.75 [0.68, 0.83] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 54.9% of observables
- Protocol B (direct_grouped) wins on 45.1% of observables
- Crossover exists for 0.0% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 0.0% | 0.0490 |
| 5% | 0.0% | 0.0490 |
| 10% | 0.0% | 0.0490 |
| 20% | 0.0% | 0.0490 |

**Optimal pilot fraction:** 2%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* not reached
- **direct_optimized:** N* not reached
- **classical_shadows_v0:** N* = 2920998 (R² = 1.000)
