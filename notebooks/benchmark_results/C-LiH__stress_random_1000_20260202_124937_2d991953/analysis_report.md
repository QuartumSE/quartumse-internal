# Comprehensive Benchmark Analysis

**Run ID:** C-LiH__stress_random_1000_20260202_124937_2d991953
**Protocols:** direct_optimized, classical_shadows_v0, direct_grouped
**Observables:** 100
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 100
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.2979103971891202
- **baseline_mean_se:** 0.1963939622281472
- **shadows_vs_baseline_ratio:** 1.5169020157709496
- **winner_at_max_n:** direct_grouped
- **shadows_wins_fraction:** 0.32
- **baseline_wins_fraction:** 0.33
- **optimal_pilot_fraction:** 0.2

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
- selection_accuracy: 0.2
- regret: 0.06474063971083563
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.0320 | 0.0000 | Yes | 0.73 [0.55, 0.96] |
| 200 | 0.8626 | 0.0000 | No | 0.98 [0.80, 1.21] |
| 1000 | 0.0000 | 0.0000 | Yes | 0.43 [0.38, 0.50] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 32.0% of observables
- Protocol B (direct_grouped) wins on 33.0% of observables
- Crossover exists for 22.0% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 0.0% | 0.0614 |
| 5% | 0.0% | 0.0614 |
| 10% | 0.0% | 0.0614 |
| 20% | 80.0% | 0.0225 |

**Optimal pilot fraction:** 20%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 86609 (R² = 0.878)
- **direct_optimized:** N* = 14339 (R² = 1.000)
- **classical_shadows_v0:** N* = 920871 (R² = 1.000)
