# Comprehensive Benchmark Analysis

**Run ID:** O-QAOA-7__merged_20260202_130742_b9229acd
**Protocols:** direct_optimized, classical_shadows_v0, direct_grouped
**Observables:** 275
**Shot Grid:** [100, 200, 1000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 275
- **n_shots_evaluated:** 3
- **max_shots:** 1000
- **shadows_mean_se:** 0.40482779969526694
- **baseline_mean_se:** 0.33003825867124936
- **shadows_vs_baseline_ratio:** 1.2266087008370605
- **winner_at_max_n:** direct_grouped
- **shadows_wins_fraction:** 0.5418181818181819
- **baseline_wins_fraction:** 0.4581818181818182
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

- pilot_n: 100
- target_n: 1000
- selection_accuracy: 0.1
- regret: 0.08947631804102044
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.0000 | nan | Yes | nan [nan, nan] |
| 200 | 0.0000 | nan | Yes | nan [nan, nan] |
| 1000 | 0.0000 | 0.0000 | Yes | 0.66 [0.60, 0.74] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 54.2% of observables
- Protocol B (direct_grouped) wins on 45.8% of observables
- Crossover exists for 0.0% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 0.0% | 0.0343 |
| 5% | 0.0% | 0.0343 |
| 10% | 0.0% | 0.0343 |
| 20% | 0.0% | 0.0343 |

**Optimal pilot fraction:** 2%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* not reached
- **direct_optimized:** N* not reached
- **classical_shadows_v0:** N* = 2920998 (R² = 1.000)
