# Comprehensive Benchmark Analysis

**Run ID:** S-ISING-4__stress_random_1000_20260130_204922_792421ff
**Protocols:** direct_grouped, direct_optimized, classical_shadows_v0
**Observables:** 87
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 87
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.16155636732844408
- **baseline_mean_se:** 0.17035886478171072
- **shadows_vs_baseline_ratio:** 0.9483296776804323
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.5402298850574713
- **baseline_wins_fraction:** 0.28735632183908044
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
- selection_accuracy: 0.4
- regret: 0.010948431189593006
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.3994 | 0.0000 | No | 1.06 [0.93, 1.21] |
| 200 | 0.0000 | 0.0000 | Yes | 1.25 [1.14, 1.38] |
| 1000 | 0.0028 | 0.0000 | Yes | 1.11 [1.03, 1.20] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 54.0% of observables
- Protocol B (direct_grouped) wins on 28.7% of observables
- Crossover exists for 14.9% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 50.0% | 0.0057 |
| 5% | 50.0% | 0.0057 |
| 10% | 50.0% | 0.0057 |
| 20% | 70.0% | 0.0026 |

**Optimal pilot fraction:** 20%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 19910 (R² = 0.988)
- **direct_optimized:** N* = 16795 (R² = 0.991)
- **classical_shadows_v0:** N* = 12937 (R² = 1.000)
