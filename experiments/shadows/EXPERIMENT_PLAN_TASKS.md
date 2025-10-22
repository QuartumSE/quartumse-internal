# QuartumSE Shadow Validation Tasks

Derived from the “Experiment Plan for Validating QuartumSE’s Shadow-Based Measurements on IBM Q” to organize implementation, execution, and analysis workstreams.

## Repository scaffolding and shared infrastructure
- [x] Establish per-experiment folders under `experiments/shadows` (`extended_ghz`, `parallel_bell_pairs`, `random_clifford`, `ising_trotter`, `h2_energy`) with `scripts/`, `methodology/`, `results/`, and `discussion/` subdirectories to keep code, procedures, raw outputs, and interpretations clearly separated as the plan expands into multiple experimental families.【F:Research/experiment_plan_text.md†L226-L515】【F:experiments/shadows/extended_ghz/scripts/.gitkeep†L1-L1】
- [ ] Define a shared calibration workflow (readout error calibration circuits, storage format, reuse policy) that can be triggered before each experiment, aligning with the plan’s emphasis on measurement error mitigation (MEM).【F:Research/experiment_plan_text.md†L126-L138】【F:Research/experiment_plan_text.md†L904-L917】
- [ ] Create a runtime budgeting checklist covering shot allocations, batching strategy, and monthly scheduling so all experiments stay within the 10-minute IBM Q free-tier allowance.【F:Research/experiment_plan_text.md†L904-L917】
- [ ] Develop common analysis utilities for shot-saving ratio (SSR), confidence interval (CI) coverage, and variance tracking to reuse across experiments.【F:Research/experiment_plan_text.md†L942-L966】
- [ ] Document how high-statistics references (simulators or large-shot baselines) will be generated for ground-truth comparisons when exact analytical values are unavailable.【F:Research/experiment_plan_text.md†L995-L1001】

## Extended GHZ entanglement (4–5 qubits)
- [ ] Design and simulate 4- and 5-qubit GHZ preparation circuits, including connectivity-aware CNOT chains for target backends.【F:Research/experiment_plan_text.md†L117-L124】
- [ ] Implement MEM-calibrated measurement routines and demonstrate fidelity improvement above the 0.5 entanglement threshold after mitigation.【F:Research/experiment_plan_text.md†L126-L139】【F:Research/experiment_plan_text.md†L582-L607】
- [ ] Expand observable estimation to the full GHZ stabilizer set plus additional non-commuting parity checks (e.g., Mermin terms) and compare direct grouping vs. shadows for shot efficiency.【F:Research/experiment_plan_text.md†L161-L190】【F:Research/experiment_plan_text.md†L545-L599】
- [ ] Run repeated hardware trials (≥10) to evaluate CI coverage and heavy-tail behavior, applying robust estimators if under-coverage appears.【F:Research/experiment_plan_text.md†L192-L205】
- [ ] Populate the methodology, results, and discussion subdirectories with experiment-specific procedures, raw logs, processed metrics (fidelity, MAE, SSR), and narrative interpretation.【F:Research/experiment_plan_text.md†L545-L599】

## Parallel Bell pair validation
- [ ] Build circuits for 4-qubit (and optional 6/8-qubit) disjoint Bell-pair states and verify entanglement locally per pair.【F:Research/experiment_plan_text.md†L236-L278】
- [ ] Measure $ZZ$ and $XX$ correlations for each pair plus the CHSH combination, applying MEM so the mitigated S-value comfortably exceeds 2.【F:Research/experiment_plan_text.md†L252-L264】【F:Research/experiment_plan_text.md†L923-L934】
- [ ] Compare joint shadow-based acquisition vs. per-pair grouped measurement to quantify SSR for simultaneous subsystem observables.【F:Research/experiment_plan_text.md†L271-L275】
- [ ] Archive methodologies, raw datasets, correlation analyses, and interpretive notes in the experiment’s dedicated folders.【F:Research/experiment_plan_text.md†L608-L628】

## Random Clifford state benchmarking
- [ ] Generate depth-limited random Clifford circuits on five qubits and capture ideal stabilizer data from simulation for reference.【F:Research/experiment_plan_text.md†L284-L344】
- [ ] Implement large-scale observable estimation (≥50 Pauli operators) using shadows and grouped baselines, reporting MAE distributions and CI coverage across repeated runs.【F:Research/experiment_plan_text.md†L303-L327】【F:Research/experiment_plan_text.md†L694-L719】
- [ ] Execute direct fidelity estimation (DFE) via stabilizer expectations and compare shot requirements between approaches.【F:Research/experiment_plan_text.md†L332-L363】【F:Research/experiment_plan_text.md†L675-L705】
- [ ] Store scripts, calibration notes, statistical summaries, and discussion artifacts in the corresponding folders.【F:Research/experiment_plan_text.md†L675-L720】

## Trotterized Ising chain simulation
- [ ] Assemble first-order Trotter circuits for the 6-qubit transverse-field Ising model and validate expected observables via simulation.【F:Research/experiment_plan_text.md†L382-L398】
- [ ] Collect hardware data comparing two-basis grouped measurements against shadow-based runs for identical shot budgets, focusing on energy error and variance.【F:Research/experiment_plan_text.md†L400-L429】【F:Research/experiment_plan_text.md†L769-L804】
- [ ] Extract additional observables (magnetization, correlators, energy variance) from the same shadow datasets to evidence parallel measurement gains.【F:Research/experiment_plan_text.md†L430-L441】
- [ ] Document procedures, execution logs, analysis notebooks, and interpretation within the designated directories.【F:Research/experiment_plan_text.md†L769-L810】

## H₂ ground-state energy estimation
- [ ] Implement the selected 4-qubit H₂ ansatz circuit (e.g., UCC-style) and benchmark ideal expectation values for validation.【F:Research/experiment_plan_text.md†L450-L456】
- [ ] Run comparative experiments between biased shadow+MEM estimators and optimally grouped measurements, targeting the stated 0.02–0.05 Ha accuracy window and ≥30% uncertainty reduction.【F:Research/experiment_plan_text.md†L462-L505】【F:Research/experiment_plan_text.md†L873-L903】
- [ ] Check for estimator bias introduced by locally weighted sampling and adjust weighting or post-processing if discrepancies exceed quoted uncertainties.【F:Research/experiment_plan_text.md†L888-L896】
- [ ] Capture methodology narratives, raw/processed datasets, and publication-ready discussion materials in the experiment-specific folders.【F:Research/experiment_plan_text.md†L872-L903】【F:Research/experiment_plan_text.md†L1015-L1034】

## Cross-experiment reporting and publication readiness
- [ ] Aggregate high-impact findings (Hamiltonian efficiency gains, entanglement recovery, multi-observable accuracy) into a cohesive report highlighting publication opportunities.【F:Research/experiment_plan_text.md†L1010-L1044】
- [ ] Ensure every experiment’s discussion notes address success criteria, SSR achievements, and limitations to support future manuscript drafting.【F:Research/experiment_plan_text.md†L923-L957】【F:Research/experiment_plan_text.md†L1015-L1034】
