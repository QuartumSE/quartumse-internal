# Comprehensive Benchmark Analysis

**Run ID:** M-PHASE-4__stress_random_500_20260130_230251_6454dec9
**Protocols:** direct_grouped, direct_optimized, classical_shadows_v0
**Observables:** 87
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 87
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.16156309922825465
- **baseline_mean_se:** 0.164820727546134
- **shadows_vs_baseline_ratio:** 0.9802353237582481
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.47126436781609193
- **baseline_wins_fraction:** 0.3218390804597701
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
- selection_accuracy: 0.6
- regret: 0.01440133186286809
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.9950 | 0.0000 | No | 1.00 [0.87, 1.14] |
| 200 | 0.0002 | 0.0000 | Yes | 1.20 [1.08, 1.32] |
| 1000 | 0.3286 | 0.0000 | No | 1.04 [0.96, 1.13] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 47.1% of observables
- Protocol B (direct_grouped) wins on 32.2% of observables
- Crossover exists for 20.7% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 40.0% | 0.0075 |
| 5% | 40.0% | 0.0075 |
| 10% | 40.0% | 0.0075 |
| 20% | 80.0% | 0.0020 |

**Optimal pilot fraction:** 20%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 18526 (R² = 0.987)
- **direct_optimized:** N* = 14016 (R² = 0.994)
- **classical_shadows_v0:** N* = 12932 (R² = 1.000)
