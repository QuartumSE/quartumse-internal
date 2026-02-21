# Comprehensive Benchmark Analysis

**Run ID:** O-QAOA-7__readout_1e-2_20260221_125757_f942d7c8
**Protocols:** classical_shadows_v0, direct_optimized, direct_grouped
**Observables:** 280
**Shot Grid:** [5000, 10000, 20000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 280
- **n_shots_evaluated:** 3
- **max_shots:** 20000
- **shadows_mean_se:** 0.11382210551998034
- **baseline_mean_se:** 0.07508044852279282
- **shadows_vs_baseline_ratio:** 1.516001938712798
- **winner_at_max_n:** direct_grouped
- **shadows_wins_fraction:** 0.55
- **baseline_wins_fraction:** 0.45
- **optimal_pilot_fraction:** 0.02

---

## Task Results

### Worst Case


**Enhanced Analysis:**

### Average Target


### Fixed Budget


### Dominance

- crossover_n: None
- always_a_better: False
- always_b_better: True
- metric_used: mean_se

### Pilot Selection

- pilot_n: 5000
- target_n: 20000
- selection_accuracy: 0.8
- regret: 0.0002918957886102774
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 5000 | 0.0000 | 0.0000 | Yes | 0.47 [0.43, 0.50] |
| 10000 | 0.0000 | 0.0000 | Yes | 0.44 [0.41, 0.47] |
| 20000 | 0.0000 | 0.0000 | Yes | 0.44 [0.41, 0.47] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 55.0% of observables
- Protocol B (direct_grouped) wins on 45.0% of observables
- Crossover exists for 0.0% of observables

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

- **direct_grouped:** N* = 44615 (R² = 1.000)
- **direct_optimized:** N* = 35455 (R² = 1.000)
- **classical_shadows_v0:** N* = 112719 (R² = 1.000)
