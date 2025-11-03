# S-ISING: Ising Chain Trotter - Rationale

**Experiment ID:** S-ISING
**Workstream:** S (Shadows)
**Status:** Planned (Phase 1)
**Target:** Nov 2025

## Overview

S-ISING applies shadows to Trotterized Ising Hamiltonian evolution (6-qubit transverse-field Ising model). Estimates energy, magnetization, and correlators from single shadow dataset, demonstrating shadows for time-evolution simulations.

## Scientific Rationale

1. **Hamiltonian Simulation:** Ising model is canonical quantum simulation target
2. **Energy + Auxiliary Observables:** Estimate energy, magnetization, ZZ correlators simultaneously
3. **Trotter Circuit:** First-order Trotter (depth-limited) tests shadows on structured circuits
4. **Phase 2 Chemistry Prep:** Ising model shares structure with fermionic Hamiltonians

## Expected Outcomes

- **System:** 6-qubit 1D Ising chain
- **Observables:** Energy (6 ZZ + 6 X terms), magnetization (6 Z), correlators (5 ZZ adjacent)
- **Shadow Budget:** 500-1000
- **SSR Target:** ≥ 1.3× vs. grouped measurement

## Relevant Literature

- **Lloyd (1996):** Universal quantum simulator - Ising models
- **Trotter (1959):** Product formula for time evolution

## Part of Phase 1 Research Plan

**Purpose:** Validates shadows for Hamiltonian simulation (bridge to chemistry)
**Timeline:** Nov 2025
**Priority:** Medium (Phase 1 valuable for Phase 2 design)
