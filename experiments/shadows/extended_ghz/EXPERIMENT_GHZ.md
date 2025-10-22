# Extended GHZ Experiment (4–5 qubits)

**Goal:** Prepare a 4–5 qubit GHZ state and estimate multi-qubit parity observables to compute GHZ fidelity.
Compare direct grouped measurements vs. classical shadows (v0 and v1+MEM).

## Circuit
- GHZ-N: H on q0, then CNOT chain q0→q1→...→qN-1

## Observables
- All pairwise ZZ correlations, the full X...X parity, and selected Y...Y/X...Y terms for robustness.

## Metrics & Criteria
- Fidelity ≥ 0.5 with MEM (entanglement witness); raw (no MEM) may fall below 0.5.
- MAE of parity observables < 0.1.
- SSR > 1 to reach same fidelity error vs. direct measurement.
- CI coverage ~95% where applicable.

## Suggested Shots
- Direct grouped: ~5 bases × 600 shots each
- Shadows v0: ~3000
- Shadows v1+MEM: calibration 2^N×256, measurement remainder
