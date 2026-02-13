# Comprehensive Benchmark Analysis

**Run ID:** C-H2__merged_20260213_081258_8aa6fa3b
**Protocols:** classical_shadows_v0, direct_grouped, direct_optimized
**Observables:** 89
**Shot Grid:** [5000, 10000, 20000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 89
- **n_shots_evaluated:** 3
- **max_shots:** 20000
- **shadows_mean_se:** 0.03607491756796318
- **baseline_mean_se:** 0.03752785477984987
- **shadows_vs_baseline_ratio:** 0.9612837658744399
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.6179775280898876
- **baseline_wins_fraction:** 0.3707865168539326
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
- selection_accuracy: 0.5
- regret: 0.0027972944064420108
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 5000 | 0.0416 | 0.0000 | Yes | 1.08 [1.00, 1.17] |
| 10000 | 0.0266 | 0.0000 | Yes | 1.09 [1.01, 1.18] |
| 20000 | 0.0456 | 0.0000 | Yes | 1.08 [1.00, 1.17] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 61.8% of observables
- Protocol B (direct_grouped) wins on 37.1% of observables
- Crossover exists for 1.1% of observables

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

- **direct_grouped:** N* = 11289 (R² = 1.000)
- **direct_optimized:** N* = 9714 (R² = 1.000)
- **classical_shadows_v0:** N* = 10386 (R² = 1.000)
