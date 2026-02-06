# Comprehensive Benchmark Analysis

**Run ID:** C-H2__readout_1e-2_20260206_141837_e01dec4e
**Protocols:** classical_shadows_v0, direct_grouped, direct_optimized
**Observables:** 89
**Shot Grid:** [5000, 10000, 20000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 89
- **n_shots_evaluated:** 3
- **max_shots:** 20000
- **shadows_mean_se:** 0.036074917567963175
- **baseline_mean_se:** 0.03808599299965552
- **shadows_vs_baseline_ratio:** 0.9471964553553709
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.651685393258427
- **baseline_wins_fraction:** 0.33707865168539325
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

- pilot_n: 5000
- target_n: 20000
- selection_accuracy: 0.3
- regret: 0.003128317346234627
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 5000 | 0.0028 | 0.0000 | Yes | 1.11 [1.03, 1.20] |
| 10000 | 0.0012 | 0.0000 | Yes | 1.13 [1.04, 1.21] |
| 20000 | 0.0026 | 0.0000 | Yes | 1.11 [1.03, 1.20] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 65.2% of observables
- Protocol B (direct_grouped) wins on 33.7% of observables
- Crossover exists for 1.1% of observables

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

- **direct_grouped:** N* = 11627 (R² = 1.000)
- **direct_optimized:** N* = 9877 (R² = 1.000)
- **classical_shadows_v0:** N* = 10386 (R² = 1.000)
