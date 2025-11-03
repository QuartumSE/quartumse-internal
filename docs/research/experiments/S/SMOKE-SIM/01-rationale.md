# Simulator Smoke Test - Rationale

**Experiment ID:** SMOKE-SIM
**Workstream:** S (Shadows)
**Status:** Completed (Nov 3, 2025)
**Phase:** Phase 1 Foundation & R&D

## Overview

The Simulator Smoke Test is the foundational validation experiment for QuartumSE's classical shadows v0 baseline implementation. This experiment establishes baseline performance metrics on ideal simulator backends before attempting hardware execution.

## Scientific Rationale

### Why This Experiment?

1. **Validation of Core Implementation**: Verify that the classical shadows v0 (random local Clifford) implementation correctly estimates observables for known quantum states.

2. **Baseline Performance Metrics**: Establish Shot-Savings Ratio (SSR) and Confidence Interval (CI) coverage metrics in an ideal (noise-free) environment to set expectations for hardware runs.

3. **GHZ State Selection**: GHZ states are maximally entangled and highly sensitive to errors, making them excellent test cases for measurement protocols. Their analytical expectation values are well-known, enabling precise validation.

4. **Risk Mitigation**: Testing on simulators first allows rapid iteration without consuming precious quantum hardware credits or queue time.

## Connection to Larger Research Plan

This experiment directly addresses Phase 1 exit criteria:
- **SSR ≥ 1.2× on simulator**: Validates shot efficiency of classical shadows approach
- **CI coverage ≥ 80%**: Ensures statistical validity of uncertainty quantification
- **End-to-end pipeline**: Tests manifest generation, provenance tracking, and reporting infrastructure

The simulator results establish upper bounds for what hardware can achieve and inform mitigation strategy design for Phase 1's noise-aware experiments (S-T02).

## Relevant Literature

1. **Huang, H.-Y., Kueng, R., & Preskill, J. (2020).** "Predicting many properties of a quantum system from very few measurements." *Nature Physics*, 16(10), 1050-1057.
   - Original classical shadows paper establishing theoretical foundations
   - Proves exponential sample complexity advantages for certain observables

2. **Hadfield, C., Bravyi, S., Raymond, R., & Mezzacapo, A. (2022).** "Measurements of quantum Hamiltonians with locally-biased classical shadows." *Communications in Mathematical Physics*, 391(3), 951-967.
   - Demonstrates practical advantages for molecular Hamiltonian estimation
   - Informs our Chemistry workstream (C-T01) design

3. **Chen, S., Yu, W., Zeng, P., & Flammia, S. T. (2021).** "Robust shadow estimation." *PRX Quantum*, 2(3), 030348.
   - Provides theoretical basis for noise-aware shadows (v1) development in S-T02

## Expected Outcomes and Success Criteria

### Primary Success Criteria

1. **SSR ≥ 1.2× on 3-qubit GHZ**: Demonstrates shot savings compared to direct Pauli measurement baseline
2. **CI Coverage ≥ 90%**: 95% confidence intervals contain true expectation values at least 90% of the time
3. **Scaling Validation**: Consistent performance across 3-, 4-, and 5-qubit GHZ states

### Secondary Success Criteria

1. **Manifest Generation**: Complete provenance manifest with circuit hash, seed, and observable definitions
2. **Execution Speed**: Sub-minute total runtime for all tests
3. **Reproducibility**: Exact result replication from saved seeds and manifests

### Quantitative Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| SSR (3-qubit) | ≥ 1.2× | Phase 1 exit criterion |
| SSR (4-qubit) | ≥ 1.2× | Scaling validation |
| SSR (5-qubit) | ≥ 1.2× | Scaling validation |
| CI Coverage | ≥ 90% | Statistical confidence threshold |
| Observable Count | 9 (3q), 12 (4q), 15 (5q) | All Z/ZZ combinations |
| Execution Time | < 60s total | Efficiency validation |

### Known Limitations

1. **Ideal Simulator**: No noise modeling, represents upper bound of performance
2. **Limited Observables**: Only Z-basis observables (X/Y basis requires additional development)
3. **Small Scale**: ≤5 qubits due to simulator memory constraints
4. **v0 Baseline Only**: Noise-aware features (v1) tested separately in S-T02

## Next Steps After Completion

Upon successful completion:
1. Proceed to Hardware Smoke Test (SMOKE-HW) on IBM backend
2. Use SSR and CI coverage baselines to inform hardware expectations
3. Develop noise-aware v1 implementation (S-T02) based on any shortfalls
4. Extend to Chemistry (C-T01) and other workstreams with confidence in core infrastructure

## Part of Phase 1 Research Plan

This experiment is the first step in the Shadows workstream validation chain:

```
SMOKE-SIM → SMOKE-HW → S-T01 → S-T02 → [C-T01, O-T01, B-T01, M-T01]
  (this)     (hardware)  (extended)  (noise-aware)  (cross-workstream)
```

Without SMOKE-SIM validation, all downstream experiments would lack a validated foundation.
