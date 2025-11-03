# B-T01: RB/XEB Benchmarking - Rationale

**Experiment ID:** B-T01
**Workstream:** B (Benchmarking)
**Status:** Planned (Phase 1)
**Target:** Nov 2025

## Overview

B-T01 demonstrates classical shadows for quantum benchmarking tasks: randomized benchmarking (RB) and cross-entropy benchmarking (XEB). Compares shadow-based fidelity/entropy estimation vs. standard protocols.

## Scientific Rationale

1. **Benchmarking Application:** RB and XEB are standard NISQ device characterization tools
2. **Shadow-Benchmarking:** Estimate fidelity, purity, entropy from same shadow dataset
3. **Sample Efficiency:** Quantify shot savings vs. direct fidelity estimation
4. **Phase 2 Foundation:** Validates B-T02 (Shadow-Benchmarking full workflow)

### Why Shadows for Benchmarking?

**Advantage:** Traditional benchmarking requires many measurements for:
- Fidelity estimation (state tomography or DFE)
- Purity estimation (shadow norm)
- Entropy estimation (von Neumann entropy)

**Shadows enable:** All three metrics from single dataset

## Expected Outcomes

- **RB:** 1-3 qubit randomized benchmarking, depth-limited sequences
- **XEB:** Depth-limited random circuits, compare to IBM calibration data
- **Sample Efficiency:** ≥ 2× vs. direct methods
- **Manifest Integration:** Log benchmarking results into standard provenance format

## Relevant Literature

- **Emerson et al. (2005):** Randomized benchmarking protocol
- **Arute et al. (2019):** XEB for quantum supremacy (Google Sycamore)
- **Huang et al. (2022):** Shadow-based fidelity estimation

## Part of Phase 1 Research Plan

**Purpose:** Extends shadows to benchmarking workstream
**Timeline:** Nov 2025
**Priority:** MEDIUM (Phase 1 optional, valuable for Phase 2)
