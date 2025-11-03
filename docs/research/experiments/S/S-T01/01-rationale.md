# S-T01: Extended GHZ Validation - Rationale

**Experiment ID:** S-T01
**Workstream:** S (Shadows)
**Status:** Planned (Target: Nov 2025)
**Phase:** Phase 1 Foundation & R&D

## Overview

S-T01 extends the GHZ smoke tests (SMOKE-SIM, SMOKE-HW) to provide statistically rigorous validation of classical shadows on IBM quantum hardware. This experiment runs ≥10 independent trials with connectivity-aware circuit layouts to demonstrate **SSR ≥ 1.1×** and **CI coverage ≥ 80%** under realistic noise conditions - both critical Phase 1 exit criteria.

## Scientific Rationale

### Why This Experiment?

1. **Statistical Significance:** Single hardware trials (SMOKE-HW) insufficient for Phase 1 gate review. Need ≥10 trials to compute SSR with confidence intervals.

2. **Phase 1 Exit Criterion:** Roadmap requires "SSR ≥ 1.1× on IBM hardware" - S-T01 provides the evidence.

3. **Noise Characterization:** Multiple trials quantify run-to-run variance from calibration drift, queue-dependent errors, and stochastic noise.

4. **Connectivity-Aware Validation:** Test on 4-5 qubit GHZ with hardware topology constraints (not just 3-qubit linear).

5. **Baseline for v1 Comparison:** S-T01 (v0 baseline) + S-T02 (v1 noise-aware) pair enables direct mitigation effectiveness measurement.

## Connection to Larger Research Plan

**Phase 1 Critical Path:**
```
SMOKE-HW ──> S-T01 (≥10 trials, connectivity-aware) ──> Phase 1 Gate Review
              │                                                │
              ├─> SSR ≥ 1.1× validation                       │
              ├─> CI coverage ≥ 80% validation                │
              └─> Enables S-T02 (v1 comparison baseline)       └─> Phase 2 Entry
```

**Unblocks:**
- Phase 1 completion (provides SSR evidence)
- S-T02 noise-aware comparison (needs S-T01 baseline)
- Cross-workstream confidence (if shadows work for GHZ, chemistry/QAOA credible)

## Expected Outcomes and Success Criteria

### Primary Success Criteria

| Criterion | Target | Rationale |
|-----------|--------|-----------|
| **SSR (mean)** | ≥ 1.1× | Phase 1 exit requirement |
| **SSR Stability** | σ_SSR < 0.3 | Consistent performance |
| **CI Coverage** | ≥ 80% | Statistical validity |
| **Trial Count** | ≥ 10 | Statistical power |
| **System Size** | 4-5 qubits | Connectivity-aware scaling |

### Observable Targets

- **4-qubit GHZ:** Estimate 7 observables (4Z + 3ZZ), SSR ≥ 1.1× per trial
- **5-qubit GHZ:** Estimate 9 observables (5Z + 4ZZ), SSR ≥ 1.0× (relaxed for larger system)

## Relevant Literature

- **Huang et al. (2020):** Theoretical sample complexity for Pauli observables
- **Chen et al. (2021):** Noise robustness of classical shadows on NISQ hardware
- **IBM Quantum Roadmap (2024):** Error rates and calibration procedures for ibm_fez/torino

## Next Steps After Completion

1. **S-T02 Noise-Aware:** Run v1 + MEM on same backend, compare SSR improvement
2. **Phase 1 Gate Review:** Submit S-T01 results as SSR ≥ 1.1× evidence
3. **Extended Workstreams:** Launch O-T01, B-T01, M-T01 with validated shadow methodology

## Part of Phase 1 Research Plan

S-T01 is the **Phase 1 exit gate experiment** for shadows workstream. Without S-T01 SSR ≥ 1.1× demonstration, Phase 1 cannot close.

**Dependencies:** SMOKE-HW (completed Nov 3, 2025)
**Blocks:** Phase 1 gate review, S-T02 execution
**Timeline:** Target completion by Nov 15, 2025
