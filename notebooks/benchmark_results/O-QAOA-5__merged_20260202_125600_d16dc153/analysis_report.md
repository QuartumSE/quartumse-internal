# Comprehensive Benchmark Analysis

**Run ID:** O-QAOA-5__merged_20260202_125600_d16dc153
**Protocols:** direct_optimized, classical_shadows_v0, direct_grouped
**Observables:** 237
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 237
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.2421766124835342
- **baseline_mean_se:** 0.2843523221255006
- **shadows_vs_baseline_ratio:** 0.8516779841053947
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.5316455696202531
- **baseline_wins_fraction:** 0.270042194092827
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
- selection_accuracy: 0.9
- regret: 0.0030990770342993303
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.0000 | nan | Yes | nan [nan, nan] |
| 200 | 0.0014 | 0.0000 | Yes | 1.18 [1.06, 1.32] |
| 1000 | 0.0000 | 0.0000 | Yes | 1.38 [1.31, 1.45] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 53.2% of observables
- Protocol B (direct_grouped) wins on 27.0% of observables
- Crossover exists for 15.6% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 0.0% | 0.0422 |
| 5% | 0.0% | 0.0422 |
| 10% | 0.0% | 0.0422 |
| 20% | 60.0% | 0.0162 |

**Optimal pilot fraction:** 20%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 102602 (R² = 1.000)
- **direct_optimized:** N* not reached
- **classical_shadows_v0:** N* = 91285 (R² = 0.985)
