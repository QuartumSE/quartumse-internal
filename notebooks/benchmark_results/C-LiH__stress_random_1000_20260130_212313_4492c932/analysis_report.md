# Comprehensive Benchmark Analysis

**Run ID:** C-LiH__stress_random_1000_20260130_212313_4492c932
**Protocols:** direct_grouped, direct_optimized, classical_shadows_v0
**Observables:** 100
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 100
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.2979103971891202
- **baseline_mean_se:** 0.1963757374801043
- **shadows_vs_baseline_ratio:** 1.5170427926174068
- **winner_at_max_n:** direct_grouped
- **shadows_wins_fraction:** 0.35
- **baseline_wins_fraction:** 0.33
- **optimal_pilot_fraction:** 0.2

---

## Task Results

### Worst Case


**Enhanced Analysis:**

### Average Target


### Fixed Budget


### Dominance

- crossover_n: 200
- always_a_better: False
- always_b_better: False
- metric_used: mean_se

### Pilot Selection

- pilot_n: 100
- target_n: 1000
- selection_accuracy: 0.2
- regret: 0.05438660101529826
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.0614 | 0.0000 | No | 0.76 [0.57, 1.00] |
| 200 | 0.9284 | 0.0000 | No | 1.01 [0.83, 1.25] |
| 1000 | 0.0000 | 0.0000 | Yes | 0.43 [0.38, 0.50] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 35.0% of observables
- Protocol B (direct_grouped) wins on 33.0% of observables
- Crossover exists for 21.0% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 0.0% | 0.0696 |
| 5% | 0.0% | 0.0696 |
| 10% | 0.0% | 0.0696 |
| 20% | 70.0% | 0.0237 |

**Optimal pilot fraction:** 20%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 79410 (R² = 0.882)
- **direct_optimized:** N* = 13971 (R² = 1.000)
- **classical_shadows_v0:** N* = 920871 (R² = 1.000)
