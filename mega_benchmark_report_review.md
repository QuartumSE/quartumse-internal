# Mega Benchmark Report Review

## High-confidence findings

1. **Executive conclusion was overstated relative to the stated aggregate metric.**
   - The report states shadows wins in 23/42 conditions (54.8%).
   - This is only a slight majority and should be described as mixed/conditional rather than broad dominance.

2. **Overview coverage is incomplete.**
   - The circuit overview implies a full 12 circuits × 4 conditions matrix (48 cells), but only 42 winner cells are populated.
   - 6 cells are explicitly shown as missing (`—`), so some cross-condition summaries are partial.

3. **Merged vs ideal rows are repeatedly identical in several sections.**
   - Multiple per-circuit tables show exact numeric equality between merged and ideal for MAE, N*, crossover stats, and/or Bayesian probabilities.
   - This is plausible only if these datasets were intentionally reused; otherwise it suggests duplicated data paths.

4. **Language should separate statistical tendency from universal behavior.**
   - Because there are 19 grouped wins out of 42, statements like “generally outperforms across most circuits and noise conditions” can mislead unless accompanied by caveats and distributional context.

## Recommended follow-ups

- Add a **data lineage appendix** that maps each condition to source artifact directories.
- Add a **coverage panel** that reports populated cells / expected cells.
- Add a **duplicate-condition check** in the report generation step:
  - For each circuit and metric table, flag condition pairs with exact row equality across all `N`.
- Add a **family-level breakdown** (stabilizer / molecular / optimization / misc) to avoid one aggregate headline.

## Changes applied in this patch

- Updated the executive summary wording to present the 23/42 result as a mixed outcome.
- Added caveats for partial coverage and potential merged-vs-ideal duplication signals.
