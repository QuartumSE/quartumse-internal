# Comprehensive Benchmark Analysis

**Run ID:** S-BELL-2__merged_20260130_203220_94b461c1
**Protocols:** direct_grouped, direct_optimized, classical_shadows_v0
**Observables:** 87
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 87
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.16162769372645533
- **baseline_mean_se:** 0.16926937732201902
- **shadows_vs_baseline_ratio:** 0.9548548962815282
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.4942528735632184
- **baseline_wins_fraction:** 0.3103448275862069
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
- selection_accuracy: 0.6
- regret: 0.008444417323291483
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.2326 | 0.0000 | No | 0.92 [0.80, 1.05] |
| 200 | 0.0000 | 0.0000 | Yes | 1.23 [1.12, 1.35] |
| 1000 | 0.0174 | 0.0000 | Yes | 1.10 [1.02, 1.19] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 49.4% of observables
- Protocol B (direct_grouped) wins on 31.0% of observables
- Crossover exists for 18.4% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 30.0% | 0.0061 |
| 5% | 30.0% | 0.0061 |
| 10% | 30.0% | 0.0061 |
| 20% | 60.0% | 0.0026 |

**Optimal pilot fraction:** 20%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 26747 (R² = 0.970)
- **direct_optimized:** N* = 11188 (R² = 1.000)
- **classical_shadows_v0:** N* = 12962 (R² = 1.000)
