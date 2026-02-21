# Comprehensive Benchmark Analysis

**Run ID:** O-QAOA-5__merged_20260220_141618_5a4298c7
**Protocols:** classical_shadows_v0, direct_optimized, direct_grouped
**Observables:** 239
**Shot Grid:** [5000, 10000, 20000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 239
- **n_shots_evaluated:** 3
- **max_shots:** 20000
- **shadows_mean_se:** 0.0552866457249582
- **baseline_mean_se:** 0.06341186152774529
- **shadows_vs_baseline_ratio:** 0.8718659946730632
- **winner_at_max_n:** classical_shadows_v0
- **shadows_wins_fraction:** 0.6610878661087866
- **baseline_wins_fraction:** 0.27615062761506276
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
- selection_accuracy: 0.4
- regret: 0.0033093900426218867
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 5000 | 0.0000 | 0.0000 | Yes | 1.33 [1.27, 1.40] |
| 10000 | 0.0000 | 0.0000 | Yes | 1.32 [1.26, 1.39] |
| 20000 | 0.0000 | 0.0000 | Yes | 1.32 [1.25, 1.38] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 66.1% of observables
- Protocol B (direct_grouped) wins on 27.6% of observables
- Crossover exists for 4.2% of observables

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

- **direct_grouped:** N* = 32134 (R² = 1.000)
- **direct_optimized:** N* = 25657 (R² = 1.000)
- **classical_shadows_v0:** N* = 24534 (R² = 1.000)
