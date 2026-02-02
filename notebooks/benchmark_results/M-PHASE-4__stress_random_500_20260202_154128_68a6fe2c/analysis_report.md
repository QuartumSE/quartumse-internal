# Comprehensive Benchmark Analysis

**Run ID:** M-PHASE-4__stress_random_500_20260202_154128_68a6fe2c
**Protocols:** direct_optimized, classical_shadows_v0, direct_grouped
**Observables:** 87
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 87
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.16156309922825465
- **baseline_mean_se:** 0.1650220478608175
- **shadows_vs_baseline_ratio:** 0.9790394757706546
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.45977011494252873
- **baseline_wins_fraction:** 0.3218390804597701
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
- selection_accuracy: 0.5
- regret: 0.014672976707933012
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.5054 | 0.0000 | No | 0.96 [0.84, 1.09] |
| 200 | 0.0004 | 0.0000 | Yes | 1.17 [1.06, 1.29] |
| 1000 | 0.2834 | 0.0000 | No | 1.04 [0.97, 1.13] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 46.0% of observables
- Protocol B (direct_grouped) wins on 32.2% of observables
- Crossover exists for 21.8% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 40.0% | 0.0067 |
| 5% | 40.0% | 0.0067 |
| 10% | 40.0% | 0.0067 |
| 20% | 60.0% | 0.0038 |

**Optimal pilot fraction:** 20%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 20139 (R² = 0.984)
- **direct_optimized:** N* = 12826 (R² = 0.997)
- **classical_shadows_v0:** N* = 12932 (R² = 1.000)
