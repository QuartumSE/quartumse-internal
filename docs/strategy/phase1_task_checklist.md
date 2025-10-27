# Phase 1 Operational Task Checklist

This checklist aggregates the outstanding Phase 1 tasks called out across the roadmap, experiment plans, and validation guides so the execution team can run them without cross-referencing multiple documents. Use it alongside the detailed procedures in `experiments/shadows` and the runtime runbook when scheduling IBM Quantum jobs.

## Shared infrastructure & preparation
- [x] Establish a reusable **readout calibration workflow** (circuit templates, manifest storage, reuse cadence) that precedes every hardware run.
- [x] Draft the **runtime budgeting checklist** (shot counts, batching, queue timing) to stay within the 10-minute IBM Quantum free-tier window.
- [x] Implement shared **analysis utilities** for shot-saving ratio (SSR), confidence-interval (CI) coverage, and variance tracking so experiments share the same metrics code.
- [x] Document how to generate and store **high-statistics reference datasets** (simulators or large-shot baselines) whenever analytical ground truth is unavailable.

### Readout calibration cadence and artifacts
- Invoke `quartumse calibrate-readout --backend <provider:name> --qubit <i> ...` before each hardware session to refresh confusion matrices. The CLI will reuse an existing archive unless `--force` is set or `--max-age-hours` expires.
- Calibrations live under `validation_data/calibrations/<backend>/q<indices>/confusion_matrix.npz` with a sibling `.manifest.json` capturing metadata (`backend_descriptor`, `shots_per_state`, reuse flag, etc.). The manager in `experiments/shadows/common_utils.py` uses the same layout so GHZ, Bell, Clifford, Ising, and H₂ scripts automatically share matrices.
- Surface the cached path in manifests via `MitigationConfig.confusion_matrix_path`; the CLI output and experiment metadata record this location directly for provenance linking.
- Recommended cadence: refresh for new backend calibrations, topology changes, or when the cached artifact exceeds its `--max-age-hours` threshold (default is unlimited reuse). Force a regeneration whenever qubit mappings change or significant readout drift is observed.

## Shadows workstream (S)
### Extended GHZ (S-T01/S-T02 bridge)
- [ ] Simulate connectivity-aware GHZ(4–5) preparation circuits for target backends.
- [ ] Integrate MEM-calibrated measurement routines and demonstrate mitigated fidelity ≥ 0.5.
- [ ] Expand observable estimation to full stabilizer + Mermin terms and compare against grouped measurement baselines.
- [ ] Run ≥10 hardware trials to study CI coverage/heavy tails; apply robust estimators if needed.
- [ ] Archive procedures, raw logs, processed metrics, and discussion notes in the experiment subfolders.

### Parallel Bell pairs (S‑BELL)
- [ ] Build 4-qubit (optionally 6/8-qubit) disjoint Bell-pair circuits and verify pairwise entanglement.
- [ ] Measure $ZZ$, $XX$, and CHSH combinations with MEM such that mitigated $S>2$.
- [ ] Quantify SSR gains for simultaneous subsystem observables versus per-pair grouped runs.
- [ ] File methodologies, datasets, and analyses under the dedicated directories.

### Random Clifford benchmarking (S‑CLIFF)
- [ ] Generate depth-limited random Clifford circuits (≥5 qubits) and capture stabilizer references from simulation.
- [ ] Estimate ≥50 Pauli observables with shadows and grouped baselines, reporting MAE distributions and CI coverage.
- [ ] Execute direct fidelity estimation (DFE) and compare shot requirements to shadows.
- [ ] Store scripts, calibration notes, stats summaries, and interpretation artifacts.

### Ising chain (S‑ISING)
- [ ] Assemble first-order Trotter circuits for the 6-qubit transverse-field Ising model and validate expected observables in simulation.
- [ ] Collect hardware data comparing grouped vs. shadow measurements for equal shot budgets (track energy error/variance).
- [ ] Extract auxiliary observables (magnetization, correlators, energy variance) from the same shadows datasets.
- [ ] Document procedures, execution logs, analyses, and interpretation materials.

### H₂ energy (S‑CHEM)
- [ ] Implement the 4-qubit H₂ ansatz and benchmark ideal expectations for validation.
- [ ] Run shadow+MEM versus grouped-measurement comparisons, targeting 0.02–0.05 Ha accuracy and ≥30% uncertainty reduction.
- [ ] Monitor and correct estimator bias from locally weighted sampling if uncertainties are exceeded.
- [ ] Capture methodology narratives, raw/processed data, and publication-ready discussion notes.

## Cross-experiment reporting
- [ ] Aggregate the high-impact findings (Hamiltonian efficiency gains, entanglement recovery, multi-observable accuracy) into a consolidated Phase 1 report.
- [ ] Ensure each experiment’s discussion notes document success criteria, SSR achievements, and limitations for manuscript prep.

## Validation gating tasks
- [ ] Complete the **extended IBM hardware validation** campaign (SSR ≥ 1.1×; manifests saved under `validation_data/`).
- [ ] Run the hardware validation post-checks: manifests present, calibration snapshot archived, v0 vs v1 MAE comparison, and results logged in `docs/archive/status_report_20251022.md`.
- [ ] Verify validation CI coverage ≥ 80% and document Phase 1 completion once criteria are met.

## Cross-workstream starters (C/O/B/M)
- [ ] Execute C/O/B/M starter experiments on simulator and generate first data drops (manifests + shot data for Phase 1 closure).
- [ ] Confirm patent theme shortlist drafting continues ahead of the Phase 2 gate review.

---

**Note:** Advanced shadow variants (v2 Fermionic, v3 Adaptive, v4 Robust) are Phase 2+ scope and intentionally excluded from this checklist to keep Phase 1 focused on v0/v1 hardware validation.

---

### How to use this checklist
1. Copy relevant tasks into your sprint tracker, linking back to their detailed procedure files (design docs in `experiments/shadows/**/` and the hardware validation design note).
2. Before each IBM Quantum run, execute `quartumse runtime-status --json --backend <backend>` and record queue depth/runtime budget in the runbook.
3. After completing an experiment, attach manifests, calibration data, and summary notebooks to the appropriate `results/` and `discussion/` folders and check the corresponding box here.
4. When preparing a public release or milestone summary, update [`CHANGELOG.md`](../../CHANGELOG.md) with the scope of work that shipped before tagging.

Update this document whenever a task is completed or a new Phase 1 dependency is identified.
