# Comprehensive Benchmark Analysis

**Run ID:** S-BELL-2__merged_20260202_091440_5134b467
**Protocols:** direct_optimized, classical_shadows_v0, direct_grouped
**Observables:** 87
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 87
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.16162769372645533
- **baseline_mean_se:** 0.1691842467258343
- **shadows_vs_baseline_ratio:** 0.955335362803462
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.4827586206896552
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
- selection_accuracy: 0.7
- regret: 0.00885183327566334
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.2770 | 0.0000 | No | 0.93 [0.81, 1.06] |
| 200 | 0.0000 | 0.0000 | Yes | 1.23 [1.13, 1.36] |
| 1000 | 0.0208 | 0.0000 | Yes | 1.10 [1.01, 1.19] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 48.3% of observables
- Protocol B (direct_grouped) wins on 31.0% of observables
- Crossover exists for 19.5% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 30.0% | 0.0070 |
| 5% | 30.0% | 0.0070 |
| 10% | 30.0% | 0.0070 |
| 20% | 40.0% | 0.0037 |

**Optimal pilot fraction:** 20%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 26126 (R² = 0.971)
- **direct_optimized:** N* = 10987 (R² = 1.000)
- **classical_shadows_v0:** N* = 12962 (R² = 1.000)
