# Comprehensive Benchmark Analysis

**Run ID:** C-H2__stress_random_1000_20260202_124438_14375f28
**Protocols:** direct_optimized, classical_shadows_v0, direct_grouped
**Observables:** 87
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 87
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.16114611817478433
- **baseline_mean_se:** 0.16278755316486676
- **shadows_vs_baseline_ratio:** 0.9899167045749497
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.5057471264367817
- **baseline_wins_fraction:** 0.3448275862068966
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

- pilot_n: 100
- target_n: 1000
- selection_accuracy: 0.4
- regret: 0.018350930601527253
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.9620 | 0.0000 | No | 1.00 [0.88, 1.14] |
| 200 | 0.0170 | 0.0000 | Yes | 1.13 [1.03, 1.25] |
| 1000 | 0.6232 | 0.0000 | No | 1.02 [0.95, 1.10] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 50.6% of observables
- Protocol B (direct_grouped) wins on 34.5% of observables
- Crossover exists for 12.6% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 70.0% | 0.0037 |
| 5% | 70.0% | 0.0037 |
| 10% | 70.0% | 0.0037 |
| 20% | 70.0% | 0.0033 |

**Optimal pilot fraction:** 2%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 16061 (R² = 0.994)
- **direct_optimized:** N* = 19544 (R² = 0.978)
- **classical_shadows_v0:** N* = 12870 (R² = 1.000)
