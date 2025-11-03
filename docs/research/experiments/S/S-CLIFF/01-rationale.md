# S-CLIFF: Random Clifford Benchmarking - Rationale

**Experiment ID:** S-CLIFF
**Workstream:** S (Shadows)
**Status:** Planned (Phase 1)
**Target:** Nov 2025

## Overview

S-CLIFF tests classical shadows on random Clifford circuits (5 qubits, depth-limited) to validate performance on non-stabilizer states. Compares shadow-based estimation vs. direct fidelity estimation (DFE) for ≥50 Pauli observables.

## Scientific Rationale

1. **Non-GHZ States:** Test shadows beyond simple entangled states
2. **Many Observables:** Estimate ≥50 Paulis simultaneously (high-value demonstration)
3. **DFE Comparison:** Quantify shadows vs. standard benchmarking approach
4. **Phase 2 Prep:** Random states are precursor to chemistry/optimization problems

## Expected Outcomes

- **Circuit:** Random Clifford, 5 qubits, depth ≤ 10
- **Observables:** ≥50 Pauli strings (full stabilizer group sampling)
- **Shadow Budget:** 500-1000
- **SSR vs. DFE:** ≥ 2× for many-observable regime

## Relevant Literature

- **Huang et al. (2021):** Derandomization for Pauli observable estimation
- **Emerson et al. (2005):** Randomized benchmarking protocols

## Part of Phase 1 Research Plan

**Purpose:** Validates shadows for general quantum states (not just GHZ)
**Timeline:** Nov 2025
**Priority:** Medium (Phase 1 optional)
