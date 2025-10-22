# Random Clifford State (5 qubits)

**Goal:** Prepare a random 5-qubit Clifford state. Estimate 50+ Pauli observables (incl. stabilizers) and
compute direct-fidelity-estimation (DFE) from stabilizer expectations. Compare grouped direct vs. shadows.

## Metrics & Criteria
- SSR > 2× for multi-observable estimation vs. grouped direct (same total shots).
- CI coverage ~95% across the observable set.
- Fidelity within ±0.05 absolute of ideal (simulated) value.
