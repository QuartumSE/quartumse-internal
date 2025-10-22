# Preliminary Hardware Benchmark (Smoke Test)

**Purpose:** Verify end-to-end connectivity to `ibm_torino`, QuartumSE estimator setup, measurement path,
manifest saving, and basic CI computation *before* running the larger experiments.

## Circuit
- 2-qubit Bell state |Φ⁺⟩ = (|00⟩ + |11⟩)/√2

## Observables
- ZZ and XX correlations (ideal: +1.0)

## Procedure
1. Resolve backend `ibm:ibm_torino` (requires `QISKIT_IBM_TOKEN` in env).
2. Prepare Bell circuit.
3. Run:
   - Direct basis measurements for ZZ and XX (250 shots each).
   - Shadows v0 (500 shots total).
   - Shadows v1+MEM (calibration: 4×128 = 512 shots, shadows: 200 shots).
4. Print summary, save manifest/shot data if available.

## Pass/Fail
- Connectivity OK (backend resolved and job completes).
- Correlations reasonably high: ZZ, XX > 0.8 with MEM.
- Files written to `validation_data/`.
