# QuartumSE Research Experiments Index

**Last Updated:** November 3, 2025
**Phase:** Phase 1 (Foundation & R&D)

---

## Quick Navigation

- [Experiment Status Dashboard](#experiment-status-dashboard)
- [Workstream Organization](#workstream-organization)
- [Completed Experiments](#completed-experiments)
- [Planned Experiments](#planned-experiments)
- [Data Locations](#data-locations)

---

## Experiment Status Dashboard

### Phase 1 Progress (Nov 2025)

| Workstream | Completed | Planned | Total | Progress |
|------------|-----------|---------|-------|----------|
| **S (Shadows)** | 2 | 5 | 7 | 29% |
| **C (Chemistry)** | 1 | 0 | 1 | 100% |
| **O (Optimization)** | 0 | 1 | 1 | 0% |
| **B (Benchmarking)** | 0 | 1 | 1 | 0% |
| **M (Metrology)** | 0 | 1 | 1 | 0% |
| **TOTAL** | **3** | **8** | **11** | **27%** |

**Phase 1 Target:** ≥5 experiments completed (3 critical + 2 optional)
**Current Status:** 3/5 critical experiments completed, on track for Phase 1 closure

---

## Workstream Organization

### S-Workstream: Shadows Core

**Focus:** Validate classical shadows v0-v1 on simulator and IBM hardware

| Experiment ID | Status | System | SSR | Priority | Documentation |
|---------------|--------|--------|-----|----------|---------------|
| [SMOKE-SIM](#smoke-sim) | ✅ Complete | 3-5q GHZ | 17.37× | CRITICAL | [Docs](S/SMOKE-SIM/) |
| [SMOKE-HW](#smoke-hw) | ✅ Complete | 3q GHZ | ~1.0× | CRITICAL | [Docs](S/SMOKE-HW/) |
| [S-T01](#s-t01) | 📋 Planned | 4-5q GHZ | ≥1.1× | CRITICAL | [Docs](S/S-T01/) |
| [S-T02](#s-t02) | 📋 Planned | 4-5q GHZ | ≥1.1× | CRITICAL | [Docs](S/S-T02/) |
| [S-BELL](#s-bell) | 📋 Planned | 4-8q Bell | ≥1.2× | MEDIUM | [Docs](S/S-BELL/) |
| [S-CLIFF](#s-cliff) | 📋 Planned | 5q Clifford | ≥1.5× | MEDIUM | [Docs](S/S-CLIFF/) |
| [S-ISING](#s-ising) | 📋 Planned | 6q TFIM | ≥1.3× | MEDIUM | [Docs](S/S-ISING/) |

**Phase 1 Exit Criterion:** S-T01 OR S-T02 achieves SSR ≥ 1.1× on IBM hardware

### C-Workstream: Chemistry

**Focus:** Shadow-based molecular Hamiltonian estimation for VQE

| Experiment ID | Status | Molecule | Qubits | Terms | Documentation |
|---------------|--------|----------|--------|-------|---------------|
| [C-T01](#c-t01) | ✅ Complete | H₂@STO-3G | 4 | 12 | [Docs](C/C-T01/) |

**Phase 1 Exit Criterion:** ✅ First chemistry data drop generated (C-T01)

**Phase 2 Pipeline:**
- C-T02: LiH@minimal (6q, 20 terms)
- C-T03: BeH₂@minimal (8q, 30-40 terms)

### O-Workstream: Optimization

**Focus:** Shot-frugal QAOA via shadow-based cost estimation

| Experiment ID | Status | Problem | Qubits | Layers | Documentation |
|---------------|--------|---------|--------|--------|---------------|
| [O-T01](#o-t01) | 📋 Planned | MAX-CUT | 5 | p=1-2 | [Docs](O/O-T01/) |

**Phase 1 Exit Criterion:** First optimization data drop (O-T01)

### B-Workstream: Benchmarking

**Focus:** Shadow-based device characterization (RB/XEB/fidelity)

| Experiment ID | Status | Protocol | Qubits | Metrics | Documentation |
|---------------|--------|----------|--------|---------|---------------|
| [B-T01](#b-t01) | 📋 Planned | RB/XEB | 1-3 | Fidelity, purity | [Docs](B/B-T01/) |

**Phase 1 Exit Criterion:** First benchmarking data drop (B-T01, optional)

### M-Workstream: Metrology

**Focus:** Shadow-based readout for quantum sensing applications

| Experiment ID | Status | State | Qubits | Application | Documentation |
|---------------|--------|-------|--------|-------------|---------------|
| [M-T01](#m-t01) | 📋 Planned | GHZ | 3-4 | Phase sensing | [Docs](M/M-T01/) |

**Phase 1 Exit Criterion:** First metrology data drop (M-T01, optional/exploratory)

---

## Completed Experiments

### SMOKE-SIM: Simulator Smoke Test {#smoke-sim}

**Status:** ✅ Completed (Nov 3, 2025)
**Backend:** aer_simulator
**System:** 3-, 4-, 5-qubit GHZ states
**Shadow Version:** v0 (baseline)

**Key Results:**
- **SSR:** 17.37× on 3-qubit (exceeds 1.2× target)
- **CI Coverage:** 100% for 3- and 4-qubit
- **Execution Time:** < 30 seconds
- **Provenance:** Multiple manifests generated

**Success Criteria:** ✅ ALL PASSED
- SSR ≥ 1.2×: 17.37× (14.4× above target)
- CI Coverage ≥ 90%: 100% (3-4q)
- Manifest generation: Complete

**Documentation:** [S/SMOKE-SIM/](S/SMOKE-SIM/)
**Manifests:** `data/manifests/` (multiple IDs from Oct-Nov 2025)

---

### SMOKE-HW: Hardware Smoke Test {#smoke-hw}

**Status:** ✅ Completed (Nov 3, 2025)
**Backend:** ibm_fez (156-qubit), ibm_torino (133-qubit, Oct 22)
**System:** 3-qubit GHZ state
**Shadow Version:** v0 (baseline, no mitigation)

**Key Results:**
- **Execution Time:** 7.82 seconds (ibm_fez)
- **Observables:** ZII, ZZI, ZIZ estimated
- **Hardware Quality:** Excellent (T1=63-209 μs, T2=49-199 μs, readout=0.77-2.22%)
- **SSR:** ~1.0× (preliminary, insufficient data for rigorous calculation)

**Success Criteria:** ✅ PASSED (hardware integration)
- Hardware execution: ✅ Success
- Manifest capture: ✅ Complete (IBM calibration snapshot)
- Runtime compliance: ✅ < 10 minutes
- SSR ≥ 1.1×: ⚠️ Inconclusive (need S-T01 extended validation)

**Documentation:** [S/SMOKE-HW/](S/SMOKE-HW/)
**Manifests:** `226a2dfc-922f-434c-b44d-f9411ef1167a.json`, `538ec4c1-4530-4db6-9694-8970ee4cb5a7.json`, etc.

---

### C-T01: H₂ Chemistry Experiment {#c-t01}

**Status:** ✅ Completed (Nov 3, 2025)
**Manifest ID:** `2a89df46-3c81-4638-9ff4-2f60ecf3325d`
**Backend:** ibm_fez
**Molecule:** H₂@STO-3G (4 qubits)
**Shadow Version:** v1 (noise-aware + MEM)

**Key Results:**
- **Execution Time:** 17.49 seconds
- **Hamiltonian Terms:** 12 Pauli observables estimated
- **Total Energy:** -1.516816 Hartree
- **Shadow Size:** 300
- **MEM Calibration:** 128 shots × 16 basis states
- **Preliminary SSR:** ~4.0× (needs baseline validation)

**Observable Quality:**
- Z-basis correlations (ZZ): Excellent (CI width 0.007-0.021)
- Single-qubit Z: Moderate (CI width 0.12-0.16)
- X/Y-basis terms: Near-zero (hardware noise degradation)

**Success Criteria:** ✅ PASSED (Phase 1 data drop)
- Chemistry data drop: ✅ Generated (manifest + shot data + MEM)
- Hamiltonian estimation: ✅ All 12 terms
- Shadow-based readout: ✅ v1 + MEM validated
- Energy accuracy: ⚠️ Pending real H₂ Hamiltonian
- SSR ≥ 1.1×: ⚠️ Pending baseline comparison

**Documentation:** [C/C-T01/](C/C-T01/)
**Manifest:** `data/manifests/2a89df46-3c81-4638-9ff4-2f60ecf3325d.json` (37 KB)
**Shot Data:** `data/shots/2a89df46-3c81-4638-9ff4-2f60ecf3325d.parquet`
**Full Report:** See `H2_EXPERIMENT_REPORT.md` in project root

---

## Planned Experiments

### S-T01: Extended GHZ Validation {#s-t01}

**Status:** 📋 Planned (Target: Nov 2025)
**System:** 4-5 qubit GHZ (connectivity-aware)
**Trials:** ≥10 independent runs
**Shadow Size:** 500 per trial
**Backend:** ibm:ibm_fez (primary)

**Objectives:**
- Demonstrate SSR ≥ 1.1× with statistical significance
- Characterize run-to-run variance (target σ_SSR < 0.3)
- Validate CI coverage ≥ 80% on hardware
- Establish baseline for S-T02 (v1 comparison)

**Success Criteria:**
- SSR (mean) ≥ 1.1× across ≥10 trials
- CI coverage ≥ 80%
- ⚠️ BLOCKS Phase 1 completion if not achieved

**Documentation:** [S/S-T01/](S/S-T01/)

---

### S-T02: Noise-Aware GHZ with MEM {#s-t02}

**Status:** 📋 Planned (Target: Nov 2025)
**System:** 4-5 qubit GHZ (same as S-T01)
**Shadow Version:** v1 (noise-aware + MEM)
**Comparison:** v0 (S-T01) vs. v1 (S-T02)

**Objectives:**
- Validate v1 noise-aware inverse channel + MEM
- Quantify variance reduction: target 20-30% vs. v0
- Demonstrate SSR improvement (v1 ≥ v0 + 0.2×)
- Validate mitigation stack for Phase 2 use

**Success Criteria:**
- Variance reduction ≥ 20% vs. S-T01
- SSR ≥ 1.1× (can rescue Phase 1 if S-T01 fails)
- CI coverage ≥ 85% (tighter CIs expected)

**Documentation:** [S/S-T02/](S/S-T02/)

---

### S-BELL: Parallel Bell Pairs {#s-bell}

**Status:** 📋 Planned (Target: Nov 2025, optional)
**System:** 2-4 disjoint Bell pairs (4-8 qubits total)
**Observables:** ZZ, XX, CHSH per pair
**Shadow Size:** 300-500

**Objectives:**
- Multi-subsystem observable estimation
- CHSH > 2 demonstration (quantum entanglement)
- SSR ≥ 1.2× vs. per-pair measurement

**Priority:** MEDIUM (Phase 1 optional, valuable for Phase 2)
**Documentation:** [S/S-BELL/](S/S-BELL/)

---

### S-CLIFF: Random Clifford Benchmarking {#s-cliff}

**Status:** 📋 Planned (Target: Nov 2025, optional)
**System:** 5-qubit random Clifford circuits (depth-limited)
**Observables:** ≥50 Pauli strings
**Shadow Size:** 500-1000

**Objectives:**
- Validate shadows on non-GHZ states
- Many-observable regime (≥50 Paulis)
- Compare to direct fidelity estimation (DFE)
- SSR ≥ 1.5× vs. DFE for many observables

**Priority:** MEDIUM (Phase 1 optional)
**Documentation:** [S/S-CLIFF/](S/S-CLIFF/)

---

### S-ISING: Ising Chain Trotter {#s-ising}

**Status:** 📋 Planned (Target: Nov 2025, optional)
**System:** 6-qubit transverse-field Ising model (1D chain)
**Observables:** Energy (12 terms), magnetization (6 terms), correlators (5 terms)
**Shadow Size:** 500-1000

**Objectives:**
- Hamiltonian simulation application (Trotter circuits)
- Energy + auxiliary observables from single dataset
- SSR ≥ 1.3× vs. grouped measurement
- Chemistry preparation (similar structure to fermionic Hamiltonians)

**Priority:** MEDIUM (Phase 1 optional, valuable for Phase 2 chemistry)
**Documentation:** [S/S-ISING/](S/S-ISING/)

---

### O-T01: QAOA MAX-CUT {#o-t01}

**Status:** 📋 Planned (Target: Nov 2025)
**Problem:** MAX-CUT on 5-node ring graph
**Layers:** p=1-2
**Observables:** Edge ZZ terms (cost function)

**Objectives:**
- Shot-frugal QAOA optimization
- Reduce shots per iteration (1000 → 300 via shadows)
- Demonstrate optimizer step reduction (↓ 20-25%)
- Maintain solution quality ≥ 0.90 (approximation ratio)

**Success Criteria:**
- Optimization data drop generated
- Optimizer steps ↓ ≥ 20%
- SSR ≥ 1.2×

**Priority:** HIGH (Phase 1 optimization workstream data drop)
**Documentation:** [O/O-T01/](O/O-T01/)

---

### B-T01: RB/XEB Benchmarking {#b-t01}

**Status:** 📋 Planned (Target: Nov 2025)
**Protocols:** Randomized Benchmarking (RB), Cross-Entropy Benchmarking (XEB)
**System:** 1-3 qubit RB, depth-limited XEB
**Metrics:** Fidelity, purity, entropy

**Objectives:**
- Shadow-based device characterization
- Estimate fidelity + purity + entropy from single shadow dataset
- Sample efficiency ≥ 2× vs. direct fidelity estimation
- Compare to IBM calibration data

**Success Criteria:**
- Benchmarking data drop generated
- Sample efficiency ≥ 2×
- Manifest integration (log benchmarking results)

**Priority:** MEDIUM (Phase 1 optional)
**Documentation:** [B/B-T01/](B/B-T01/)

---

### M-T01: GHZ Phase Sensing {#m-t01}

**Status:** 📋 Planned (Target: Nov 2025, exploratory)
**System:** GHZ(3-4) as phase sensor
**Application:** Z-phase parameter estimation
**Observables:** Optimal linear combination of Z/ZZ terms

**Objectives:**
- Shadow-based readout for quantum sensing
- CI widths reflect sensing precision
- Explore ZNE for readout bias correction
- CI coverage ≥ 80% (simulator), ≥ 70% (hardware)

**Success Criteria:**
- Metrology data drop generated (exploratory)
- CI coverage ≥ 80% on simulator

**Priority:** LOW (Phase 1 exploratory, not blocking)
**Documentation:** [M/M-T01/](M/M-T01/)

---

## Data Locations

### Manifests

**Path:** `C:\Users\User\Desktop\Projects\QuartumSE\data\manifests\`

**Naming Convention:** `{experiment_id}.json` or `{workstream}-{exp_id}-trial-{N}-{uuid}.json`

**Current Count:** 30+ manifests (as of Nov 3, 2025)

**Example Manifests:**
- SMOKE-SIM: `05735bbf-1c30-4e00-98af-cb1ad03a6a58.json` (Oct 21, 3q)
- SMOKE-HW: `226a2dfc-922f-434c-b44d-f9411ef1167a.json` (Nov 3, ibm_fez)
- C-T01: `2a89df46-3c81-4638-9ff4-2f60ecf3325d.json` (Nov 3, H₂ chemistry)

**Schema:** Provenance Manifest v1 (see `quartumse/reporting/manifest.py`)

### Shot Data

**Path:** `C:\Users\User\Desktop\Projects\QuartumSE\data\shots\`

**Format:** Parquet files (columnar format for efficient replay)

**Schema:**
- Shadow snapshots: Measurement bases + outcomes
- Replayable: Estimate NEW observables without re-running quantum circuits

**Example:** `2a89df46-3c81-4638-9ff4-2f60ecf3325d.parquet` (C-T01 H₂ experiment)

### Confusion Matrices (MEM Calibration)

**Path:** `C:\Users\User\Desktop\Projects\QuartumSE\data\mem\`

**Format:** NumPy .npz archives

**Reuse:** Valid for ~24 hours or until backend re-calibration

**Example:** `2a89df46-3c81-4638-9ff4-2f60ecf3325d.npz` (C-T01 4-qubit confusion matrix)

---

## Cross-Links and Navigation

### Strategic Documentation
- [Phase 1 Research Plan](../phase1-research-plan.md) - Comprehensive Phase 1 overview
- [Project Roadmap](../../strategy/roadmap.md) - Multi-phase project plan
- [Phase 1 Task Checklist](../../strategy/phase1_task_checklist.md) - Detailed task tracking

### Reports and Analysis
- [Strategic Analysis](../../../STRATEGIC_ANALYSIS.md) - Current status and next steps
- [H₂ Experiment Report](../../../H2_EXPERIMENT_REPORT.md) - Detailed C-T01 analysis

### Technical Documentation
- [Experiment Tracker](../experiment-tracker.md) - Lightweight experiment log
- [Literature References](../literature.md) - Key papers and citations

---

## Quick Stats

**Phase 1 (as of Nov 3, 2025):**
- ✅ 3 experiments completed
- 📋 8 experiments planned
- 🔬 2 workstreams active (S, C)
- 💾 30+ manifests generated
- 🖥️ 2 IBM backends tested (ibm_fez, ibm_torino)
- ⚡ Fastest execution: 7.82s (SMOKE-HW)
- 🎯 Best SSR: 17.37× (SMOKE-SIM, 3-qubit)

**Next Milestones:**
- S-T01/S-T02: Demonstrate SSR ≥ 1.1× on IBM hardware (CRITICAL)
- O-T01: Optimization workstream data drop (HIGH)
- Phase 1 Gate Review: Target end of November 2025

---

**Document Version:** 1.0
**Last Updated:** November 3, 2025
**Maintained By:** Research Team
**Feedback:** Open issue in GitHub or contact research lead
