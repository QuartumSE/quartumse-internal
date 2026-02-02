# Comprehensive Benchmark Analysis

**Run ID:** S-GHZ-5__merged_20260202_083546_ed5e9543
**Protocols:** direct_optimized, classical_shadows_v0, direct_grouped
**Observables:** 237
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 237
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.24211344686909902
- **baseline_mean_se:** 0.27710379299430377
- **shadows_vs_baseline_ratio:** 0.8737283753964205
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.4978902953586498
- **baseline_wins_fraction:** 0.29957805907172996
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
- regret: 0.002457928326161213
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.0000 | nan | Yes | nan [nan, nan] |
| 200 | 0.6178 | 0.0000 | No | 1.03 [0.92, 1.15] |
| 1000 | 0.0000 | 0.0000 | Yes | 1.31 [1.24, 1.38] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 49.8% of observables
- Protocol B (direct_grouped) wins on 30.0% of observables
- Crossover exists for 16.5% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 0.0% | 0.0350 |
| 5% | 0.0% | 0.0350 |
| 10% | 0.0% | 0.0350 |
| 20% | 60.0% | 0.0138 |

**Optimal pilot fraction:** 20%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 135864 (R² = 1.000)
- **direct_optimized:** N* not reached
- **classical_shadows_v0:** N* = 91374 (R² = 0.985)
