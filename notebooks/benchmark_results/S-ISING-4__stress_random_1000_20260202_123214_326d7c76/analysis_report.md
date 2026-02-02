# Comprehensive Benchmark Analysis

**Run ID:** S-ISING-4__stress_random_1000_20260202_123214_326d7c76
**Protocols:** direct_optimized, classical_shadows_v0, direct_grouped
**Observables:** 87
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 87
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.1615563673284441
- **baseline_mean_se:** 0.170190650259363
- **shadows_vs_baseline_ratio:** 0.9492669960555375
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.4942528735632184
- **baseline_wins_fraction:** 0.27586206896551724
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
- selection_accuracy: 0.2
- regret: 0.012989246132354726
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.3518 | 0.0000 | No | 1.06 [0.94, 1.21] |
| 200 | 0.0000 | 0.0000 | Yes | 1.23 [1.12, 1.35] |
| 1000 | 0.0044 | 0.0000 | Yes | 1.11 [1.04, 1.19] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 49.4% of observables
- Protocol B (direct_grouped) wins on 27.6% of observables
- Crossover exists for 20.7% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 70.0% | 0.0030 |
| 5% | 70.0% | 0.0030 |
| 10% | 70.0% | 0.0030 |
| 20% | 60.0% | 0.0019 |

**Optimal pilot fraction:** 2%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 18944 (R² = 0.991)
- **direct_optimized:** N* = 19646 (R² = 0.983)
- **classical_shadows_v0:** N* = 12937 (R² = 1.000)
