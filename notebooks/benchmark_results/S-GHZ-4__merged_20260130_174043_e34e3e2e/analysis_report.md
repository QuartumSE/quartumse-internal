# Comprehensive Benchmark Analysis

**Run ID:** S-GHZ-4__merged_20260130_174043_e34e3e2e
**Protocols:** direct_grouped, direct_optimized, classical_shadows_v0
**Observables:** 180
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 180
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.1730226352033466
- **baseline_mean_se:** 0.23611487094459033
- **shadows_vs_baseline_ratio:** 0.7327900801468378
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.6166666666666667
- **baseline_wins_fraction:** 0.2777777777777778
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
- selection_accuracy: 0.7
- regret: 0.0016439736806403455
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.0000 | nan | Yes | nan [nan, nan] |
| 200 | 0.0000 | 0.0000 | Yes | 1.69 [1.56, 1.83] |
| 1000 | 0.0000 | 0.0000 | Yes | 1.86 [1.77, 1.96] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 61.7% of observables
- Protocol B (direct_grouped) wins on 27.8% of observables
- Crossover exists for 4.4% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 0.0% | 0.0631 |
| 5% | 0.0% | 0.0631 |
| 10% | 0.0% | 0.0631 |
| 20% | 80.0% | 0.0123 |

**Optimal pilot fraction:** 20%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 34225 (R² = 1.000)
- **direct_optimized:** N* = 23476 (R² = 1.000)
- **classical_shadows_v0:** N* = 16246 (R² = 0.999)
