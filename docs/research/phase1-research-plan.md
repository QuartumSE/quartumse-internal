# Phase 1 Research Plan: Foundation & R&D (Nov 2025)

**Phase Duration:** Now → November 30, 2025
**Status:** In Progress (Smoke Tests Complete, Extended Validation Pending)
**Last Updated:** November 3, 2025

---

## Executive Summary

Phase 1 establishes QuartumSE's foundational research program, delivering validated classical shadows implementations (v0-v1), cross-workstream starter experiments, and comprehensive provenance infrastructure. The phase targets **SSR ≥ 1.2× on simulator** and **SSR ≥ 1.1× on IBM hardware** to demonstrate shot-efficiency advantages before opening Early Access in Phase 4.

**Key Milestones:**
- ✅ Core SDK infrastructure (estimator, shadows v0/v1, reporting)
- ✅ Simulator validation (SSR 17.37× on 3-qubit GHZ)
- ✅ Hardware integration (ibm_fez, 7.82s execution)
- ✅ Chemistry data drop (C-T01 H₂ experiment)
- ⏳ Extended hardware validation (S-T01/S-T02, target SSR ≥ 1.1×)
- ⏳ Cross-workstream starters (O-T01, B-T01, M-T01)

---

## Workstream Organization

Phase 1 research is organized into 5 parallel workstreams, each with specific experiments and exit criteria:

### Workstream S (Shadows)
**Goal:** Validate classical shadows v0-v1 on simulator and hardware

| Experiment | Status | Description | Priority | SSR Target |
|------------|--------|-------------|----------|------------|
| SMOKE-SIM | ✅ Complete | 3-5q GHZ on aer_simulator | CRITICAL | 17.37× achieved |
| SMOKE-HW | ✅ Complete | 3q GHZ on ibm_fez | CRITICAL | ~1.0× (prelim) |
| S-T01 | 📋 Planned | Extended GHZ (≥10 trials, 4-5q) | CRITICAL | ≥ 1.1× |
| S-T02 | 📋 Planned | Noise-aware GHZ with MEM (v1) | CRITICAL | ≥ 1.1× |
| S-BELL | 📋 Planned | Parallel Bell pairs (4-8q) | MEDIUM | ≥ 1.2× |
| S-CLIFF | 📋 Planned | Random Clifford (5q, ≥50 Paulis) | MEDIUM | ≥ 1.5× |
| S-ISING | 📋 Planned | Ising chain Trotter (6q TFIM) | MEDIUM | ≥ 1.3× |

**Exit Criteria:**
- ✅ SSR ≥ 1.2× on simulator (achieved: 17.37×)
- ⏳ SSR ≥ 1.1× on IBM hardware (pending S-T01/S-T02)
- ⏳ CI coverage ≥ 80% (pending extended validation)

### Workstream C (Chemistry)
**Goal:** Demonstrate shadow-based Hamiltonian estimation for molecular systems

| Experiment | Status | Description | Priority | Molecules |
|------------|--------|-------------|----------|-----------|
| C-T01 | ✅ Complete | H₂@STO-3G (4q, 12 terms) | CRITICAL | H₂ |

**Exit Criteria:**
- ✅ First chemistry data drop generated (C-T01 manifest + shot data)
- ⏳ Energy accuracy 0.02-0.05 Ha (pending real Hamiltonian)
- ⏳ SSR ≥ 1.1× vs. grouped Pauli (pending baseline)

**Phase 2 Pipeline:**
- C-T02: LiH@minimal (6q, 20 terms)
- C-T03: BeH₂@minimal (8q, 30-40 terms)

### Workstream O (Optimization)
**Goal:** Validate shot-frugal QAOA using shadow-based cost estimation

| Experiment | Status | Description | Priority | Graph |
|------------|--------|-------------|----------|-------|
| O-T01 | 📋 Planned | QAOA MAX-CUT (5-node ring, p=1-2) | HIGH | Ring-5 |

**Exit Criteria:**
- First optimization data drop (manifest + convergence data)
- Optimizer steps ↓ ≥ 20% vs. standard QAOA
- Solution quality ≥ 0.90 (approximation ratio)

### Workstream B (Benchmarking)
**Goal:** Apply shadows to device characterization (RB/XEB)

| Experiment | Status | Description | Priority | Metrics |
|------------|--------|-------------|----------|---------|
| B-T01 | 📋 Planned | RB/XEB (1-3q RB, depth-limited XEB) | MEDIUM | Fidelity, purity |

**Exit Criteria:**
- First benchmarking data drop
- Sample efficiency ≥ 2× vs. direct fidelity estimation

### Workstream M (Metrology)
**Goal:** Explore shadows for quantum sensing applications

| Experiment | Status | Description | Priority | Application |
|------------|--------|-------------|----------|-------------|
| M-T01 | 📋 Planned | GHZ phase sensing (3-4q, Z-phase) | LOW | Phase estimation |

**Exit Criteria:**
- First metrology data drop (exploratory)
- CI coverage ≥ 80% on simulator

---

## Experiment Tree (Dependencies)

```
                                SMOKE-SIM (v0 simulator)
                                     ✅
                                     │
                                     ▼
                                SMOKE-HW (v0 hardware)
                                     ✅
                                     │
                     ┌───────────────┴────────────────┐
                     ▼                                ▼
                 S-T01 (Extended)               Cross-Workstream
            (≥10 trials, 4-5q)                  Integration
                  📋                                  │
                  │                        ┌──────────┼──────────┐
                  ▼                        ▼          ▼          ▼
             S-T02 (v1 + MEM)         C-T01      O-T01      B-T01
         (Compare v0 vs v1)             ✅         📋         📋
                  📋                     │
                  │                      │
        ┌─────────┴──────────┐          ▼
        ▼                    ▼      Phase 2
   S-BELL                S-CLIFF    C-T02 (LiH)
 (Parallel pairs)    (Random Clifford)  S-T03 (Fermionic)
       📋                   📋

    S-ISING
 (Ising Trotter)
       📋
```

**Legend:**
- ✅ Complete
- 📋 Planned
- ⏳ In Progress

---

## Timeline and Execution Schedule

### Week 1 (Nov 3-9, 2025)

**Completed:**
- ✅ SMOKE-SIM: Simulator validation (SSR 17.37×)
- ✅ SMOKE-HW: Hardware integration (ibm_fez)
- ✅ C-T01: H₂ chemistry data drop

**This Week:**
- [ ] S-T01: Execute ≥10 trials on ibm_fez
- [ ] S-T02: Run v1 + MEM comparison
- [ ] C-T01 Re-Run: Real H₂ Hamiltonian + optimized ansatz

### Week 2 (Nov 10-16, 2025)

- [ ] O-T01: QAOA MAX-CUT execution
- [ ] B-T01: RB/XEB benchmarking
- [ ] S-BELL: Parallel Bell pairs (if time permits)

### Week 3 (Nov 17-23, 2025)

- [ ] M-T01: GHZ phase sensing (exploratory)
- [ ] S-CLIFF: Random Clifford (optional)
- [ ] S-ISING: Ising Trotter (optional)

### Week 4 (Nov 24-30, 2025)

- [ ] Data aggregation and analysis
- [ ] Phase 1 completion report
- [ ] Patent theme shortlist finalization
- [ ] Phase 1 Gate Review preparation

---

## Exit Criteria Mapping

### Critical (Must Pass for Phase 1 Completion)

| Criterion | Source Experiment | Target | Status |
|-----------|-------------------|--------|--------|
| **SSR ≥ 1.2× (sim)** | SMOKE-SIM | 1.2× | ✅ 17.37× |
| **SSR ≥ 1.1× (IBM)** | S-T01, S-T02 | 1.1× | ⏳ Pending |
| **CI Coverage ≥ 80%** | S-T01, S-T02 | 80% | ⏳ Pending |
| **Chemistry Data Drop** | C-T01 | Generated | ✅ Complete |
| **Optimization Data Drop** | O-T01 | Generated | 📋 Planned |
| **End-to-End IBM Run** | SMOKE-HW | 1+ backend | ✅ ibm_fez |
| **Manifest Provenance** | All experiments | Complete | ✅ Validated |

### Optional (Valuable but Not Blocking)

| Criterion | Source Experiment | Target | Status |
|-----------|-------------------|--------|--------|
| **Benchmarking Data Drop** | B-T01 | Generated | 📋 Planned |
| **Metrology Data Drop** | M-T01 | Generated | 📋 Planned |
| **Multi-Observable Demos** | S-BELL, S-CLIFF | ≥50 observables | 📋 Planned |
| **Ising Simulation** | S-ISING | Energy variance | 📋 Planned |

---

## Roadmap Milestone Connections

### Phase 1 → Phase 2 Gate

**Required Evidence for Phase 2 Entry:**

1. ✅ **Simulator Validation:** SMOKE-SIM (17.37×) exceeds threshold
2. ⏳ **Hardware Validation:** S-T01/S-T02 must demonstrate SSR ≥ 1.1×
3. ✅ **Chemistry Validation:** C-T01 provides first cross-workstream evidence
4. 📋 **Optimization Validation:** O-T01 planned (nice-to-have)
5. ✅ **Provenance System:** Manifest generation validated across experiments
6. 📋 **Patent Themes:** Shortlist (VACS, Shadow-VQE, Shadow-Benchmarking) in progress

**Gate Review Decision:**
- **PASS:** If S-T01 OR S-T02 achieves SSR ≥ 1.1× + C-T01 completed
- **CONDITIONAL PASS:** If SSR = 1.0-1.1× but CI coverage ≥ 80% (can improve in Phase 2)
- **FAIL:** If SSR < 1.0× AND CI coverage < 80% (requires rethinking)

### Phase 2 Roadmap (Dec 2025)

**Enabled by Phase 1:**
- S-T03 (Fermionic Shadows v2): Depends on C-T01 validation
- S-T04 (Adaptive Shadows v3): Depends on S-T01/S-T02 performance data
- C-T02 (LiH): Depends on C-T01 methodology
- IBM Campaign #1: Depends on operational workflows (S-T01 multi-trial)

---

## Cross-Experiment Integration Points

### Shared Infrastructure

**Calibration Workflow:**
- MEM confusion matrices reusable across experiments
- Calibration cadence: Refresh if > 12 hours old or topology changes
- Storage: `validation_data/calibrations/{backend}/q{indices}/confusion_matrix.npz`

**Observable Estimation:**
- Same `ShadowEstimator` API across all workstreams
- Observable class: Unified Pauli string representation
- Bootstrap CI: 1000 samples standard across experiments

**Manifest Schema:**
- Provenance Manifest v1: Consistent across S/C/O/B/M
- Required fields: circuit, backend, shadow_config, observables, timestamps
- Checksums: SHA-256 for circuit hash, confusion matrix, shot data

### Methodological Synergies

**S ↔ C (Shadows + Chemistry):**
- C-T01 uses S-validated shadows v1 + MEM
- Observable structure: Chemistry Hamiltonians are multi-term Paulis (like S-T01 GHZ)
- **Lesson:** Z-basis terms perform better than X/Y (inform C-T02 Hamiltonian design)

**S ↔ O (Shadows + Optimization):**
- O-T01 uses S-validated shot-frugal estimation for QAOA cost function
- Iterative setting: Each optimizer step is a mini-experiment
- **Lesson:** Need fast shadows (300-500) to enable many optimizer iterations

**S ↔ B (Shadows + Benchmarking):**
- B-T01 estimates fidelity/purity from S-validated shadow infrastructure
- **Lesson:** Multi-observable reuse (fidelity + purity + entropy from same dataset)

**Cross-Workstream Insight:**
If shadows work for GHZ (S-T01), they should work for:
- Chemistry Hamiltonians (C-T01) ← Z-heavy observables
- QAOA cost functions (O-T01) ← ZZ-based objectives
- Device benchmarking (B-T01) ← State properties from shadows

---

## Patent Strategy Integration

### Phase 1 Patent Themes

**1. Variance-Aware Adaptive Classical Shadows (VACS)**
- **Evidence:** S-T01/S-T02 variance characterization, observable-dependent performance
- **Claim:** Adaptive shadow allocation based on observable complexity and device calibration
- **Status:** Requires S-T04 (v3) implementation (Phase 2)

**2. Shadow-VQE Readout Integration**
- **Evidence:** C-T01 demonstrates multi-term Hamiltonian estimation from single dataset
- **Claim:** Shot-frugal VQE via reusable shadow datasets at each optimizer iteration
- **Status:** C-T01 provides readout stage; full VQE loop in Phase 2 (C-T02)

**3. Shadow-Benchmarking Workflow**
- **Evidence:** B-T01 fidelity/purity/entropy from single shadow dataset
- **Claim:** Unified device characterization from shadows (vs. separate protocols)
- **Status:** Requires B-T01 completion + B-T02 (Phase 2) for comprehensive workflow

### Patent Filing Timeline

- **Nov 2025:** Collect Phase 1 experimental evidence (S-T01, C-T01, O-T01)
- **Dec 2025:** Draft provisional patent applications
- **Jan 2026:** File provisional patents (Shadow-VQE, VACS)
- **Mar 2026:** Convert to non-provisional after Phase 3 validation

---

## Publication Strategy

### Target Venues

**arXiv Preprints (Jan 2026):**
1. "Classical Shadows on IBM Quantum Hardware: Performance and Mitigation Strategies"
   - Data: SMOKE-SIM, SMOKE-HW, S-T01, S-T02
   - Focus: Hardware validation, SSR measurement, v0 vs. v1 comparison

2. "Shadow-VQE: Shot-Efficient Variational Quantum Eigensolver for Molecular Hamiltonians"
   - Data: C-T01, C-T02 (Phase 2)
   - Focus: Chemistry application, multi-observable reuse, baseline comparison

**Journal Submissions (Mar 2026):**
- PRX Quantum or npj Quantum Information
- Papers submitted after Phase 3 internal validation

**Conference Presentations:**
- APS March Meeting 2026 (Abstract deadline: Nov 2025)
- ACS Fall 2026 (Chemistry applications)

---

## Risk Management

### High-Risk Items

**Risk:** S-T01 fails to achieve SSR ≥ 1.1× on IBM hardware
- **Impact:** Blocks Phase 1 → Phase 2 progression
- **Mitigation:** S-T02 (v1 + MEM) may rescue; increase shadow_size to 1000; try better backend (ibm_marrakesh)
- **Fallback:** Adjust Phase 1 exit criterion to SSR ≥ 1.0× if CI coverage ≥ 90%

**Risk:** ibm_fez queue saturates, delays experiments
- **Impact:** Timeline slip (1-2 weeks)
- **Mitigation:** Monitor queue with `quartumse runtime-status`; use ibm_marrakesh as backup
- **Fallback:** Execute S-BELL/S-CLIFF/S-ISING as simulator-only (reduce to optional)

### Medium-Risk Items

**Risk:** C-T01 baseline measurement shows SSR < 1.1×
- **Impact:** Chemistry workstream SSR claim weakened
- **Mitigation:** Increase shadow_size for C-T02; use fermionic shadows (v2) in Phase 2
- **Fallback:** Focus on multi-observable reuse advantage (vs. absolute SSR)

**Risk:** O-T01/B-T01/M-T01 delayed due to resource constraints
- **Impact:** Phase 1 optional experiments incomplete
- **Mitigation:** These are "nice-to-have" for Phase 1; can defer to Phase 2
- **Fallback:** Submit Phase 1 gate review with S+C evidence only

---

## Success Metrics Dashboard

### Quantitative Targets

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **SSR (Simulator)** | ≥ 1.2× | 17.37× | ✅ PASS |
| **SSR (Hardware)** | ≥ 1.1× | ~1.0× (prelim) | ⏳ S-T01/S-T02 |
| **CI Coverage** | ≥ 80% | 100% (sim) | ⏳ Hardware |
| **Experiments Completed** | ≥ 3 | 3 (SMOKE×2, C-T01) | ✅ Met |
| **Workstreams Active** | ≥ 2 | 2 (S, C) | ✅ Met |
| **Manifests Generated** | ≥ 5 | 30+ | ✅ Exceeded |
| **Hardware Backends** | ≥ 1 | 2 (fez, torino) | ✅ Exceeded |

### Qualitative Targets

- ✅ **End-to-End Workflow:** Validated from notebook → manifest → report
- ✅ **Provenance System:** Complete circuit/backend/calibration capture
- ✅ **Reproducibility:** Seed-based exact replication demonstrated
- ⏳ **Multi-Backend:** ibm_fez validated, ibm_marrakesh/torino tested
- ⏳ **Cross-Workstream:** S+C complete, O+B+M planned

---

## Operational Learnings

### Backend Selection Criteria

**Optimal Backend (as of Nov 3, 2025):**
- **ibm_fez** (156q, 77 pending jobs) ← BEST CHOICE
- Queue depth < 200 jobs
- Calibration < 24 hours old
- Qubits 0-3 readout error < 2.5%, T1 > 60 μs

**Backup Options:**
- ibm_marrakesh (156q, 298 pending)
- ibm_torino (133q, 485 pending)

**Avoid:**
- ibm_brisbane (3175 pending) ← Severely congested

### Execution Best Practices

1. **Pre-Flight Checks:**
   - Run `quartumse runtime-status` to check queue and calibration
   - Verify target qubits have good T1/T2 and low readout error
   - Confirm MEM calibration not stale (< 24 hours)

2. **Shot Budgeting:**
   - 100 shadows: Smoke tests only
   - 300 shadows: Chemistry/Optimization (acceptable CI width)
   - 500 shadows: Extended validation (S-T01, good statistical power)
   - 1000 shadows: Large observables (S-CLIFF ≥50 Paulis)

3. **Calibration Reuse:**
   - MEM confusion matrices valid for ~24 hours
   - Refresh if backend re-calibrated or qubit mapping changes
   - Store with checksum for provenance

4. **Manifest Naming:**
   - Pattern: `{workstream}-{experiment_id}-trial-{N}-{uuid}.json`
   - Example: `s-t01-trial-03-2a89df46-3c81-4638-9ff4-2f60ecf3325d.json`
   - Enables easy aggregation and analysis

---

## Next Steps (Immediate)

### Week of Nov 3-9, 2025

1. **S-T01 Execution (CRITICAL)**
   - Run ≥10 trials with seeds 42, 123, 456, 789, 1011, 1213, 1415, 1617, 1819, 2021
   - Shadow size: 500 per trial
   - Backend: ibm_fez (monitor queue depth)
   - **Goal:** Demonstrate SSR ≥ 1.1× with statistical significance

2. **S-T02 Execution (CRITICAL)**
   - Run v1 + MEM on same ibm_fez backend
   - ≥3 trials for comparison to S-T01
   - **Goal:** Show 20-30% variance reduction vs. v0

3. **C-T01 Validation (HIGH)**
   - Load real H₂@STO-3G Hamiltonian from qiskit-nature
   - Optimize ansatz parameters via simulator VQE
   - Re-run on ibm_fez with real Hamiltonian
   - Execute grouped Pauli baseline for rigorous SSR

4. **O-T01 Preparation (MEDIUM)**
   - Finalize QAOA circuit for 5-node ring MAX-CUT
   - Test on simulator first
   - Schedule ibm_fez execution

### Week of Nov 10-16, 2025

5. **Phase 1 Data Aggregation**
   - Collect all manifests and shot data
   - Compute aggregate SSR statistics across experiments
   - Prepare Phase 1 completion report

6. **Patent Theme Shortlist**
   - Draft VACS patent outline (pending S-T01 data)
   - Draft Shadow-VQE patent outline (using C-T01 evidence)
   - Consult IP counsel for filing strategy

---

## Document Maintenance

**Version:** 1.0
**Last Updated:** November 3, 2025
**Next Review:** November 10, 2025 (after S-T01 completion)
**Maintained By:** Research Lead
**Cross-References:**
- `docs/strategy/roadmap.md` - Overall project roadmap
- `docs/strategy/phase1_task_checklist.md` - Detailed task tracking
- `docs/research/experiments/` - Individual experiment documentation
- `STRATEGIC_ANALYSIS.md` - Current status and next actions
