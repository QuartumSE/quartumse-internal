# Review: Bayesian Adaptive Protocol Implementation and Report

## Scope
This review covers:
- `bayesian_adaptive_protocol.py` (implementation)
- `bayesian_adaptive_report.html` (reported results and interpretation)

## Executive assessment
The implementation is clear and reproducible, and the report is internally consistent with the code path. However, several methodological choices can overstate confidence and should be addressed before treating the conclusions as publication-grade.

## What is implemented correctly
1. **Adaptive commit loop is implemented as described**: explore in fixed shot batches, compute `P(best)`, and commit once a threshold is crossed. This behavior is encoded in `simulate_one_replicate` and used in threshold sweeps in `run_adaptive_simulation`.
2. **Outputs capture the right operational metrics**: commit step, exploration budget, final MAE, selection accuracy, regret, and per-replicate details.
3. **CLI and configuration surface key controls** (`--batch-size`, `--thresholds`, `--n-mc`) and make the analysis reproducible.

## Key issues and risks

### 1) NaN handling can bias `P(best)` toward the first protocol
When a protocol has no estimable errors at a step, the code inserts `np.array([np.nan])`. In `bayesian_p_best`, this can lead to `NaN` draws and then `argmin` behavior that deterministically favors low-index columns, biasing winner probabilities.

**Why it matters**: reported certainty can be inflated or distorted in sparse-data regimes.

**Recommendation**: treat missing protocol evidence explicitly (e.g., mask invalid protocols, impute conservative large-error priors, or use `np.nanargmin` after replacing NaNs with `+inf`).

### 2) Subsampling is prefix-based, not randomized
Shots are taken via slicing (`bs_all[:n_sub]`) rather than random subsampling. If shot order has structure, early-batch estimates can be biased.

**Why it matters**: early commitment claims (step 1) are sensitive to first-batch composition.

**Recommendation**: subsample with RNG-based index selection per replicate and step, with deterministic seeds for reproducibility.

### 3) Budget accounting for grouped direct protocols is approximate
For grouped protocols, each group gets `ceil(frac * group_size)` shots independently. Summed over groups, this can exceed the intended per-protocol `n_shots` exploration target.

**Why it matters**: protocol comparisons may not be budget-fair at small `n_shots`.

**Recommendation**: allocate exact integer quotas that sum to `n_shots` (e.g., largest-remainder method).

### 4) Posterior model assumptions are strong for absolute-error data
The script models protocol mean absolute error with a Student-t posterior over observable-wise errors. Absolute errors are nonnegative, often skewed, and observables are not independent.

**Why it matters**: `P(best)=1.000` can look overconfident when model assumptions are violated.

**Recommendation**: add sensitivity checks (bootstrap over observables, hierarchical model, or rank-based Bayesian comparison).

### 5) Report claims exceed what is directly demonstrated
The report states “zero overlap” of posteriors and interprets noise-profile equivalence as a data-generation issue. These claims may be true, but no direct diagnostic plots/statistics are embedded to verify them within the report itself.

**Why it matters**: strong narrative claims without direct diagnostics reduce auditability.

**Recommendation**: include posterior overlap plots, calibration checks, and explicit cross-profile raw-data checksum comparisons in the report appendix.

## Report/result-specific comments
- The central result (“single-step commitment across all thresholds and configs”) is plausible given the observed large performance gaps and is consistent with the summary tables.
- The practical interpretation is fair: adaptive brings automation rather than gains over a perfectly chosen fixed 1% pilot in this dataset.
- The report appropriately acknowledges that this benchmark is easy and that adaptive value should be tested on closer protocol matchups.

## Suggested next actions (priority order)
1. Fix NaN handling in Bayesian comparison and add a regression test.
2. Replace prefix slicing with randomized subsampling (seeded).
3. Enforce exact budget conservation across grouped direct settings.
4. Add a robustness section in report generation: posterior overlap, alternative uncertainty estimators, and noise-profile data validation artifacts.
5. Re-run the study on harder scenarios where protocol MAEs are closer.

## Bottom line
The current pipeline is a solid engineering prototype, but confidence statements in the report should be softened until NaN handling, randomized subsampling, and model-robustness diagnostics are added.
