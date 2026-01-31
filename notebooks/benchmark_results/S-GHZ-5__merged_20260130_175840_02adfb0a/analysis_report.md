# Comprehensive Benchmark Analysis

**Run ID:** S-GHZ-5__merged_20260130_175840_02adfb0a
**Protocols:** direct_grouped, direct_optimized, classical_shadows_v0
**Observables:** 237
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 237
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.24211344686909902
- **baseline_mean_se:** 0.2771834659537162
- **shadows_vs_baseline_ratio:** 0.8734772329801478
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.4936708860759494
- **baseline_wins_fraction:** 0.2911392405063291
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
- selection_accuracy: 0.5
- regret: 0.006331994477506103
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.0000 | nan | Yes | nan [nan, nan] |
| 200 | 0.5918 | 0.0000 | No | 1.03 [0.92, 1.16] |
| 1000 | 0.0000 | 0.0000 | Yes | 1.31 [1.24, 1.38] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 49.4% of observables
- Protocol B (direct_grouped) wins on 29.1% of observables
- Crossover exists for 17.7% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 0.0% | 0.0351 |
| 5% | 0.0% | 0.0351 |
| 10% | 0.0% | 0.0351 |
| 20% | 40.0% | 0.0219 |

**Optimal pilot fraction:** 20%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 135287 (R² = 1.000)
- **direct_optimized:** N* not reached
- **classical_shadows_v0:** N* = 91374 (R² = 0.985)
