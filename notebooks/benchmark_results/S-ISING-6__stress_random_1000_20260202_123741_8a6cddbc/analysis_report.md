# Comprehensive Benchmark Analysis

**Run ID:** S-ISING-6__stress_random_1000_20260202_123741_8a6cddbc
**Protocols:** direct_optimized, classical_shadows_v0, direct_grouped
**Observables:** 100
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 100
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.29834346336325035
- **baseline_mean_se:** 0.20553806429513327
- **shadows_vs_baseline_ratio:** 1.451524146568089
- **winner_at_max_n:** direct_grouped
- **shadows_wins_fraction:** 0.37
- **baseline_wins_fraction:** 0.29
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
- selection_accuracy: 0.1
- regret: 0.060560549389623554
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.0756 | 0.0000 | No | 0.77 [0.58, 1.01] |
| 200 | 0.7718 | 0.0000 | No | 1.03 [0.84, 1.27] |
| 1000 | 0.0000 | 0.0000 | Yes | 0.47 [0.42, 0.54] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 37.0% of observables
- Protocol B (direct_grouped) wins on 29.0% of observables
- Crossover exists for 21.0% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 0.0% | 0.0812 |
| 5% | 0.0% | 0.0812 |
| 10% | 0.0% | 0.0812 |
| 20% | 80.0% | 0.0215 |

**Optimal pilot fraction:** 20%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 103536 (R² = 0.881)
- **direct_optimized:** N* = 15227 (R² = 1.000)
- **classical_shadows_v0:** N* = 919420 (R² = 1.000)
