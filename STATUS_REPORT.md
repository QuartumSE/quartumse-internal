# QuartumSE Development Review — May 2025

This document summarizes how the current repository state aligns with the long-term direction in `PROJECT_BIBLE.md` and the near-term execution plan in `ROADMAP.md`. It highlights completed work, active gaps, and concrete next actions to keep Phase 1 on track.

## Snapshot Summary

- **Measurement stack foundations exist.** Baseline (v0) and noise-aware (v1) classical shadows are implemented with shot persistence, manifests, and MEM integration. Provenance schemas and report generators are in place.
- **Roadmap execution is partial.** Shadows workstream S‑T01/S‑T02 scaffolding and tests are in good shape, but chemistry (C), optimization (O), benchmarking (B), and metrology (M) experiments are still placeholders.
- **Observability deliverables need polish.** CLI support is informational only, and replay tooling lacks parity for noise-aware runs. Automated ZNE, adaptive shadows, and SSR/RMSE@$ dashboards are not ready yet.

## Alignment with the Project Bible

| Theme | Bible Expectations | Current Evidence | Gap / Risk |
| --- | --- | --- | --- |
| Vendor-neutral positioning | Multi-provider connectors, provenance, reproducibility | IBM connector with calibration snapshots (`src/quartumse/connectors/ibm.py`); manifests + shot data in `src/quartumse/reporting/` | Only IBM + Aer supported. AWS Braket connector and manifest parity pending. |
| Measurement efficiency | Classical shadows v0→v4, mitigation orchestration, cost-for-accuracy metrics | Baseline + MEM-aware shadows (`src/quartumse/shadows/`), SSR utilities (`src/quartumse/utils/metrics.py`), GHZ experiment scaffold (`experiments/shadows/S_T01_ghz_baseline.py`) | Higher-order shadows (v2+), adaptive policies, and RMSE@$ analytics not yet built. |
| Provenance & reporting | Manifest schema, replay, PDF/HTML reports | Manifest datamodel + report generator (`src/quartumse/reporting/`) and replay interface in `ShadowEstimator` | Replay only supports baseline shadows; PDF generation depends on optional deps; reports are not wired into CLI/CI. |
| Local-first & R&D focus | Offline-first data storage, notebooks for iteration | Parquet shot persistence (`ShotDataWriter`), R&D notebooks under `notebooks/` | Need consistent data dir strategy, more domain notebooks (chemistry, optimization), and reproducibility docs. |

## Phase 1 Roadmap Progress Check

| Deliverable (Roadmap P1) | Status | Notes |
| --- | --- | --- |
| SDK skeleton (`Estimator`, `Shadows`, `Report`) | ✅ | Core APIs shipped; tests cover baseline usage.
| Provenance Manifest v1 + reporting | ✅ | JSON schema + report generator present; CLI surface still minimal.
| Classical Shadows v0 (baseline) | ✅ | Implementation + tests + GHZ experiment script.
| Classical Shadows v1 (noise-aware + MEM) | ✅ | Measurement error mitigation integrated and exercised via tests.
| Mitigation core (MEM, ZNE hooks) | ⚠️ | MEM operational; ZNE class exists but not connected to estimator.
| Data/shot persistence (Parquet/DuckDB) | ✅ | Parquet persistence implemented; no DuckDB yet.
| Test harness + fixtures | ⚠️ | Unit tests exist for core modules; end-to-end regression/CI notebooks missing.
| Workstreams C/O/B/M starter experiments | ❌ | `experiments/` directories exist but contain only S‑T01/S‑T02 logic.
| Reporting automation (CLI/CI) | ⚠️ | CLI can parse config but does not execute experiments.

## Risks & Gaps

1. **Replay parity for noise-aware runs** — manifests do not capture calibrated confusion matrices, so v1 experiments cannot be replayed offline.
2. **Experiment coverage beyond shadows** — chemistry, optimization, benchmarking, and metrology workstreams lack executable notebooks/scripts, blocking roadmap validation metrics (SSR, RMSE@$, CI coverage) for those domains.
3. **Documentation drift** — README still implied future capabilities (bootstrap CIs, multi-provider support) as current features; new team members risk overestimating maturity.
4. **Benchmark automation** — no pytest/CLI bridge to run S‑T01 metrics or aggregate SSR trends; experiment scripts carry unused imports and manual boilerplate.

## Immediate Next Actions

1. **Provenance & replay (Workstream P)**
   - Persist MEM calibration artifacts alongside manifests so noise-aware runs can be replayed.
   - Integrate report generation into experiment scripts/notebooks and surface via CLI (`quartumse report`).
2. **Shadows & mitigation (Workstream S)**
   - Wire the ZNE helper into the estimator pipeline with configurable scale factors.
   - Prototype variance-aware shot allocation (foundation for adaptive shadows v3).
3. **Domain experiments (Workstreams C/O/B/M)**
   - Stand up minimal VQE (H₂) and QAOA (MAX-CUT-5) notebooks with SSR/CI plots referencing the new GHZ notebook pattern.
   - Populate benchmarking scripts (RB/XEB) that emit manifests and metrics tables.
4. **Tooling & automation**
   - Harden CLI `quartumse run` to execute experiment configs and write manifests/reports.
   - Add CI jobs that execute lightweight Aer simulations from notebooks to prevent regressions.

## Supporting Updates in this PR

- README now distinguishes shipped vs planned features and links to this review + notebook catalog.
- The S‑T01 experiment script has clean imports, and `ShadowEstimator` handles target precision estimation reliably while making replay limitations explicit.
- A new S‑T01 GHZ notebook demonstrates the baseline workflow end-to-end, saving artifacts to a notebook-local directory for iterative R&D.

This document should be updated at the close of every milestone or when roadmap scope changes materially.
