# Comprehensive Benchmark Analysis

**Run ID:** ghz_4q_20260116_145649_b1ef9493
**Protocols:** classical_shadows_v0, direct_optimized, direct_grouped
**Observables:** 22
**Shot Grid:** [100, 500, 1000, 5000]

---

## Executive Summary

- **n_protocols:** 3
- **n_observables:** 22
- **n_shots_evaluated:** 4
- **max_shots:** 5000
- **shadows_mean_se:** 0.07249165815911877
- **baseline_mean_se:** 0.04053672828641835
- **shadows_vs_baseline_ratio:** 1.788295731390014
- **winner_at_max_n:** direct_grouped
- **shadows_wins_fraction:** 0.45454545454545453
- **baseline_wins_fraction:** 0.5454545454545454
- **optimal_pilot_fraction:** 0.1

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
- target_n: 5000
- selection_accuracy: 0.55
- regret: 0.0038921702451488933
- criterion_type: truth_based

### Bias Variance


---

## Statistical Significance

| N | Diff. P-value | K-S P-value | Reject Null | SSF (95% CI) |
|---|---------------|-------------|-------------|--------------|
| 100 | 0.0000 | 0.0000 | Yes | 0.40 [0.34, 0.48] |
| 500 | 0.0000 | 0.0000 | Yes | 0.33 [0.29, 0.38] |
| 1000 | 0.0000 | 0.0000 | Yes | 0.32 [0.28, 0.36] |
| 5000 | 0.0000 | 0.0000 | Yes | 0.31 [0.27, 0.36] |

---

## Performance by Locality

---

## Per-Observable Crossover Analysis

- Protocol A (classical_shadows_v0) wins on 45.5% of observables
- Protocol B (direct_grouped) wins on 54.5% of observables
- Crossover exists for 0.0% of observables

---

## Multi-Pilot Fraction Analysis

| Pilot % | Accuracy | Mean Regret |
|---------|----------|-------------|
| 2% | 85.0% | 0.0005 |
| 5% | 85.0% | 0.0005 |
| 10% | 100.0% | 0.0000 |
| 20% | 100.0% | 0.0000 |

**Optimal pilot fraction:** 10%

---

## Interpolated N* (Power-Law)

- **direct_grouped:** N* = 82803 (R² = 1.000)
- **direct_optimized:** N* = 63872 (R² = 1.000)
- **classical_shadows_v0:** N* = 446135 (R² = 1.000)
