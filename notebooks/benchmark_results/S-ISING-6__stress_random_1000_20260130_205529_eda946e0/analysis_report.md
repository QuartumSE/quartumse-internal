# Comprehensive Benchmark Analysis

**Run ID:** S-ISING-6__stress_random_1000_20260130_205529_eda946e0
**Protocols:** direct_grouped, direct_optimized, classical_shadows_v0
**Observables:** 100
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 100
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.2983434633632503
- **baseline_mean_se:** 0.20640206317570745
- **shadows_vs_baseline_ratio:** 1.4454480675867776
- **winner_at_max_n:** direct_grouped
- **shadows_wins_fraction:** 0.39
- **baseline_wins_fraction:** 0.3
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
- regret: 0.05663137423300417
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.1078 | 0.0000 | No | 0.79 [0.61, 1.04] |
| 200 | 0.7184 | 0.0000 | No | 1.04 [0.86, 1.29] |
| 1000 | 0.0000 | 0.0000 | Yes | 0.48 [0.42, 0.55] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 39.0% of observables
- Protocol B (direct_grouped) wins on 30.0% of observables
- Crossover exists for 20.0% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 0.0% | 0.0602 |
| 5% | 0.0% | 0.0602 |
| 10% | 0.0% | 0.0602 |
| 20% | 80.0% | 0.0210 |

**Optimal pilot fraction:** 20%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 95887 (R² = 0.892)
- **direct_optimized:** N* = 14485 (R² = 1.000)
- **classical_shadows_v0:** N* = 919420 (R² = 1.000)
