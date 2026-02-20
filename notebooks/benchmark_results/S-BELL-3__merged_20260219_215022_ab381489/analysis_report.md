# Comprehensive Benchmark Analysis

**Run ID:** S-BELL-3__merged_20260219_215022_ab381489
**Protocols:** direct_optimized, classical_shadows_v0, direct_grouped
**Observables:** 103
**Shot Grid:** [5000, 10000, 20000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 103
- **n_shots_evaluated:** 3
- **max_shots:** 20000
- **shadows_mean_se:** 0.0688022660733205
- **baseline_mean_se:** 0.04502844455683222
- **shadows_vs_baseline_ratio:** 1.5279734121502329
- **winner_at_max_n:** direct_grouped
- **shadows_wins_fraction:** 0.5145631067961165
- **baseline_wins_fraction:** 0.4854368932038835
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
- selection_accuracy: 0.6
- regret: 0.0014162363319640743
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 5000 | 0.0000 | 0.0000 | Yes | 0.42 [0.38, 0.47] |
| 10000 | 0.0000 | 0.0000 | Yes | 0.42 [0.38, 0.47] |
| 20000 | 0.0000 | 0.0000 | Yes | 0.43 [0.39, 0.48] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 51.5% of observables
- Protocol B (direct_grouped) wins on 48.5% of observables
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

- **direct_grouped:** N* = 16233 (R² = 1.000)
- **direct_optimized:** N* = 13550 (R² = 1.000)
- **classical_shadows_v0:** N* = 37817 (R² = 1.000)
