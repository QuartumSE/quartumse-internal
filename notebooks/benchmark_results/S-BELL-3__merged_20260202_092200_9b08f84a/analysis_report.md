# Comprehensive Benchmark Analysis

**Run ID:** S-BELL-3__merged_20260202_092200_9b08f84a
**Protocols:** direct_optimized, classical_shadows_v0, direct_grouped
**Observables:** 103
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 103
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.2924864515425386
- **baseline_mean_se:** 0.20756839133573488
- **shadows_vs_baseline_ratio:** 1.4091088226889597
- **winner_at_max_n:** direct_grouped
- **shadows_wins_fraction:** 0.3592233009708738
- **baseline_wins_fraction:** 0.3300970873786408
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
- regret: 0.06648894075288433
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.0078 | 0.0000 | Yes | 0.67 [0.52, 0.89] |
| 200 | 0.9872 | 0.0000 | No | 1.00 [0.82, 1.24] |
| 1000 | 0.0000 | 0.0000 | Yes | 0.50 [0.44, 0.57] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 35.9% of observables
- Protocol B (direct_grouped) wins on 33.0% of observables
- Crossover exists for 22.3% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 0.0% | 0.0507 |
| 5% | 0.0% | 0.0507 |
| 10% | 0.0% | 0.0507 |
| 20% | 70.0% | 0.0337 |

**Optimal pilot fraction:** 20%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 175324 (R² = 0.837)
- **direct_optimized:** N* = 14668 (R² = 1.000)
- **classical_shadows_v0:** N* = 789433 (R² = 1.000)
