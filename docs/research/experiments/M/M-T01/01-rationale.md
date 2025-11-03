# M-T01: GHZ Phase Sensing - Rationale

**Experiment ID:** M-T01
**Workstream:** M (Metrology)
**Status:** Planned (Phase 1)
**Target:** Nov 2025

## Overview

M-T01 demonstrates classical shadows for quantum sensing/metrology applications. Uses GHZ(3-4) states as variational sensor probes to estimate encoded Z-phase parameter, testing shadow-based readout for metrology tasks.

## Scientific Rationale

1. **Quantum Metrology Application:** GHZ states provide Heisenberg-limited phase sensing
2. **Shadow-Based Readout:** Estimate phase from optimal observables using shadows
3. **Uncertainty Quantification:** CI widths reflect sensing precision
4. **ZNE Integration:** Test zero-noise extrapolation (ZNE) for readout bias correction

### Why Shadows for Metrology?

**Challenge:** Quantum sensors require precise expectation value estimation
**Opportunity:** Shadows provide:
- Multi-observable estimation (optimally-weighted phase estimator)
- Tight confidence intervals (uncertainty quantification)
- Shot-efficient readout (more sensing iterations per shot budget)

## Expected Outcomes

- **System:** GHZ(3-4) with Z-phase encoding
- **Observables:** Optimal linear combination of Z/ZZ terms for phase estimation
- **CI Coverage:** ≥ 80% on simulator, ≥ 70% on hardware (with noise)
- **ZNE Integration:** Demonstrate readout bias correction (Phase 2 preview)

## Relevant Literature

- **Giovannetti et al. (2004):** Quantum metrology - Heisenberg limit
- **Pezzè & Smerzi (2014):** Entanglement-enhanced sensing with GHZ states
- **Aaronson et al. (2018):** Shadow tomography for quantum sensing

## Part of Phase 1 Research Plan

**Purpose:** Extends shadows to metrology workstream
**Timeline:** Nov 2025
**Priority:** LOW (Phase 1 optional, exploratory for Phase 2)
