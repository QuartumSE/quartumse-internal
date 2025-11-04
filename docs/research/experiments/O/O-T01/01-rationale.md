# O-T01: QAOA MAX-CUT with Shot-Frugal Cost Estimation - Rationale

**Experiment ID:** O-T01
**Workstream:** O (Optimization)
**Status:** Planned (Target: Nov 10-16, 2025)
**Phase:** Phase 1 Foundation & R&D

## Overview

O-T01 demonstrates shot-frugal QAOA optimization using classical shadows for cost function estimation on a 5-node ring graph with MAX-CUT objective. This experiment validates that shadow-based cost estimation enables **≥20% reduction in optimizer steps** compared to standard measurement-based QAOA while maintaining solution quality ≥0.90 approximation ratio. This is the Phase 1 starter experiment for the optimization workstream, demonstrating cross-workstream integration of shadows methodology.

## Scientific Rationale

### Why This Experiment?

1. **Shadow-Optimization Synergy:** O-T01 is the first experiment integrating validated shadows (from S-T01/S-T02) into an optimization loop. Each optimizer iteration becomes a mini-shadow-estimation task, demonstrating practical shot efficiency gains.

2. **Phase 1 Exit Criterion:** The research roadmap requires "first optimization data drop (manifest + convergence data)" as a Phase 1 exit criterion. O-T01 provides this evidence.

3. **Cross-Workstream Validation:** If shadows work for GHZ states (S-T01), chemistry Hamiltonians (C-T01), and QAOA cost functions (O-T01), the methodology gains broad credibility across application domains.

4. **Shot-Frugal Optimization:** QAOA traditionally requires high shot counts per cost function evaluation. Shadow-based estimation reduces shots from 1000-10000 per evaluation to 300-500, enabling more optimizer iterations within same total shot budget.

5. **Convergence Analysis:** Multiple trials with different random initializations quantify optimizer convergence patterns: fewer iterations to good solutions with shot-frugal approach.

6. **Patent Strategy:** O-T01 data informs "Variance-Aware Adaptive Classical Shadows" (VACS) patent: demonstrates need for adaptive shadow allocation based on optimizer iteration (early iterations need less accuracy than final iterations).

### Why QAOA MAX-CUT on 5-Node Ring?

**Graph Choice:**
- **5-node ring:** Sweet spot for Phase 1 (≥4q circuits, ≥10 ZZ observables, connectivity-constrained)
- **Ring topology:** Natural on linear IBM backends, enables 5-qubit GHZ-like correlations
- **MAX-CUT objective:** Binary problem (cut edge or not) with clear approximation ratio target

**Problem Size Justification:**
- **Too small (<4q):** Insufficient to demonstrate shot efficiency advantages
- **Optimal (4-5q):** Visible convergence improvements, manageable simulator verification
- **Too large (>6q):** Risk of long optimization times, noisy gradients mask shadow benefits

### Why p=1-2 Ansatz Depth?

- **p=1:** Minimal circuit depth (6 CX gates), fast execution, obvious baseline
- **p=2:** Moderate depth (12 CX gates), better approximation ratio, shows scaling
- **p>2:** Reserved for Phase 2 after methodology validated at p=1-2

### Expected Improvements from Shadows

**Standard QAOA Cost Function:**
- Shots per evaluation: 1000-5000 (measure all ZZ observables to sufficient precision)
- Evaluations to convergence: 50-100 (standard optimizer, high-dimensional landscape)
- **Total shots: 50,000-500,000**

**Shadow-Based QAOA Cost Function:**
- Shots per evaluation: 300-500 (shadows give good estimates with lower shot counts)
- Evaluations to convergence: 40-80 (fewer iterations due to stable cost estimates)
- **Total shots: 12,000-40,000** (3-12× reduction)
- **Phase 1 Target: ≥20% step reduction** (realistic conservative estimate)

## Connection to Larger Research Plan

**Optimization Workstream Path:**
```
S-T01/S-T02 (Validated shadows)
     │
     ├──> C-T01 (Chemistry application)
     │
     └──> O-T01 (Optimization application)
           │
           ├─> Demonstrates shot-frugal cost function
           ├─> ≥20% optimizer step reduction target
           └─> Enables Phase 2 extensions (O-T02: Larger graphs, O-T03: VQE integration)
```

**Unblocks:**
- Phase 1 completion (provides first optimization data drop)
- O-T02 (larger graphs, QAOA p>2)
- Shadow-VQE patent evidence (cost function reuse per optimizer step)
- Cross-workstream confidence (shadows apply beyond GHZ/chemistry)

**Phase 1 → Phase 2 Transition:**
O-T01 success demonstrates shadows useful for iterative algorithms (optimization, variational methods). This is critical because:
- S-T01/S-T02 validate shadows for static state estimation
- C-T01 validates shadows for Hamiltonian estimation
- O-T01 validates shadows for **dynamic iterative loops** (most complex use case)

## Expected Outcomes and Success Criteria

### Primary Success Criteria

| Criterion | Target | Rationale |
|-----------|--------|-----------|
| **Optimizer Steps Reduction** | ≥ 20% | Phase 1 shot-efficiency goal |
| **Solution Quality (Approx. Ratio)** | ≥ 0.90 | Maintain solution fidelity |
| **Manifest Generated** | Complete | Provenance tracking for Phase 1 |
| **Convergence Data** | Logged per iteration | Enable convergence analysis |
| **Trials** | ≥3 | Statistical confidence (with different random seeds) |

### Observable Targets

**5-Node Ring MAX-CUT:**
- **Decision variables:** 5 binary (edge cut or not)
- **Cost function observables:** 5 ZZ terms (one per ring edge) + offset
- **Expected approximation ratio (p=1):** 0.88-0.92 (classical algorithms achieve ~0.87)
- **Shadow budget:** 300 per iteration, ≥40-60 iterations → 12,000-18,000 total shots

## Phase 1 Optimization Data Drop

O-T01 is the **first optimization data drop** for the research program. Success criteria include:

1. ✅ Manifest generated with circuit, backend, shadow_config, cost_observables
2. ✅ Shot data recorded per optimizer iteration (convergence trajectory)
3. ✅ Comparison baseline: p=1 standard QAOA on same hardware backend
4. ✅ Final solution quality ≥ 0.90 approximation ratio
5. ✅ Step reduction ≥ 20% vs. baseline (fewer iterations to convergence)

## Relevant Literature

- **Farhi et al. (2014):** Original QAOA protocol
- **Cerezo et al. (2021):** Variational quantum algorithms survey
- **Huang et al. (2020):** Classical shadows theory and sample complexity
- **Chen et al. (2021):** Shot-efficient cost estimation strategies
- **Goemans & Williamson (1995):** Classical MAX-CUT approximation ratio (0.878)

## Next Steps After Completion

1. **Analysis & Reporting:** Aggregate convergence data, compute step reduction metric
2. **Phase 1 Gate Review:** Include O-T01 as cross-workstream validation evidence
3. **O-T02 Planning:** Prepare larger graph (7-8 node graph, p=2-3) for Phase 2
4. **Shadow-VQE Patent:** Draft claims using O-T01 + C-T01 evidence (cost function reuse)
5. **Publication:** Include O-T01 convergence data in Phase 1 technical report

## Part of Phase 1 Research Plan

O-T01 is the **Phase 1 optimization starter experiment**. Without O-T01 data, Phase 1 cannot demonstrate cross-workstream validation (shadows work for S+C but not O would be concerning).

**Dependencies:** S-T01 or S-T02 (validated shadow methodology)
**Blocks:** Phase 1 gate review (supports PASS decision with C-T01 evidence)
**Timeline:** Target completion by Nov 16, 2025
**Priority:** HIGH (optimization data drop required for Phase 1 completion)

---

**Document Version:** 1.0
**Status:** Planned
**Next Review:** Upon O-T01 execution completion
