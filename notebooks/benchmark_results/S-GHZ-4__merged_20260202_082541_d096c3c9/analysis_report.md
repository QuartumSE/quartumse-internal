# Comprehensive Benchmark Analysis

**Run ID:** S-GHZ-4__merged_20260202_082541_d096c3c9
**Protocols:** direct_optimized, classical_shadows_v0, direct_grouped
**Observables:** 180
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 180
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.1730226352033466
- **baseline_mean_se:** 0.2296159264896487
- **shadows_vs_baseline_ratio:** 0.753530636347852
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.6444444444444445
- **baseline_wins_fraction:** 0.2833333333333333
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
- selection_accuracy: 0.8
- regret: 0.0018150269632519367
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.0000 | nan | Yes | nan [nan, nan] |
| 200 | 0.0000 | 0.0000 | Yes | 1.73 [1.60, 1.87] |
| 1000 | 0.0000 | 0.0000 | Yes | 1.76 [1.68, 1.85] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 64.4% of observables
- Protocol B (direct_grouped) wins on 28.3% of observables
- Crossover exists for 1.1% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 0.0% | 0.0566 |
| 5% | 0.0% | 0.0566 |
| 10% | 0.0% | 0.0566 |
| 20% | 80.0% | 0.0112 |

**Optimal pilot fraction:** 20%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 26649 (R² = 1.000)
- **direct_optimized:** N* = 21109 (R² = 1.000)
- **classical_shadows_v0:** N* = 16246 (R² = 0.999)
