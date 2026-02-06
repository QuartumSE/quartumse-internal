# Comprehensive Benchmark Analysis

**Run ID:** C-H2__depol_low_20260206_145957_34659266
**Protocols:** direct_optimized, direct_grouped, classical_shadows_v0
**Observables:** 255
**Shot Grid:** [5000, 10000, 20000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 255
- **n_shots_evaluated:** 3
- **max_shots:** 20000
- **shadows_mean_se:** 0.04077974328584594
- **baseline_mean_se:** 0.06181329722269527
- **shadows_vs_baseline_ratio:** 0.6597244463263046
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.7137254901960784
- **baseline_wins_fraction:** 0.15294117647058825
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
- selection_accuracy: 0.1
- regret: 0.004100234543695777
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 5000 | 0.0000 | 0.0000 | Yes | 2.32 [2.24, 2.40] |
| 10000 | 0.0000 | 0.0000 | Yes | 2.29 [2.21, 2.37] |
| 20000 | 0.0000 | 0.0000 | Yes | 2.30 [2.22, 2.38] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 71.4% of observables
- Protocol B (direct_grouped) wins on 15.3% of observables
- Crossover exists for 5.9% of observables

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

- **direct_grouped:** N* = 30330 (R² = 1.000)
- **direct_optimized:** N* = 23380 (R² = 1.000)
- **classical_shadows_v0:** N* = 13299 (R² = 1.000)
