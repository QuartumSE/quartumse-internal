# Hardware Smoke Test - Setup & Methods

**Experiment ID:** SMOKE-HW
**Workstream:** S (Shadows)
**Executable:** `C:\Users\User\Desktop\Projects\QuartumSE\experiments\shadows\S_T01_ghz_baseline.py`

## Circuit Description

### 3-Qubit GHZ State

Identical to SMOKE-SIM for direct comparison:

```
|GHZ(3)⟩ = (|000⟩ + |111⟩) / √2
```

**Circuit:**
```
     ┌───┐
q_0: ┤ H ├──■────■──
     └───┘┌─┴─┐  │
q_1: ─────┤ X ├──┼──
          └───┘┌─┴─┐
q_2: ──────────┤ X ├
               └───┘
```

**Depth:** 3
**Gates:** 1 H + 2 CNOT
**Qubit Requirement:** 3 connected qubits (linear or triangle topology)

### Observable Set

Same as SMOKE-SIM:
- **Z Observables:** ZII, IZI, IIZ (expected: 0.0)
- **ZZ Observables:** ZZI, ZIZ (expected: 1.0)

Total: 5 Pauli strings

## Backend Configuration

### IBM Quantum Hardware

**Selected Backend:** ibm_fez (Nov 3, 2025)
- **Qubits:** 156 (superconducting transmon)
- **Topology:** Heavy-hex lattice
- **Queue Status:** 77 pending jobs (low)
- **Calibration:** 2025-11-03T13:17:32Z (fresh, < 1 hour)

**Alternative Backends:**
- ibm_torino (133q, 485 pending) - used in Oct 22 smoke test
- ibm_marrakesh (156q, 298 pending)
- ibm_brisbane (127q, 3175 pending) - avoid due to queue

### Qubit Selection

Use first 3 connected qubits (qubits 0-1-2 if linear connectivity available):

**Quality Metrics (ibm_fez qubits 0-2):**
| Qubit | T1 (μs) | T2 (μs) | Readout Error | Gate Error (SX) |
|-------|---------|---------|---------------|-----------------|
| 0 | 63.6 | 49.7 | 0.98% | ~0.04% |
| 1 | 174.8 | 199.1 | 2.22% | ~0.03% |
| 2 | 208.9 | 178.7 | 0.77% | ~0.04% |

**Two-Qubit Gates:**
- CZ(0,1): 1.08%
- CZ(1,2): 1.08% (typical)

**Assessment:** Excellent qubit quality, suitable for smoke test.

## Classical Shadows Configuration

### v0 Baseline (No Mitigation)

```python
shadow_config = ShadowConfig(
    shadow_size=100,              # Small budget for smoke test
    random_seed=42,               # Match SMOKE-SIM
    confidence_level=0.95,
    version=ShadowVersion.V0_BASELINE,
    apply_inverse_channel=False   # No noise correction
)
```

**Rationale for Small Shadow Budget:**
- 100 snapshots minimizes queue time (< 10 min target)
- Sufficient for qualitative validation (not precision)
- Reduces cost if issues arise

### Comparison to SMOKE-SIM

| Parameter | SMOKE-SIM | SMOKE-HW |
|-----------|-----------|----------|
| Backend | aer_simulator | ibm:ibm_fez |
| Shadow Size | 500 | 100 |
| Baseline Shots | 1000 | 1000 (computed for SSR) |
| Mitigation | None | None |
| Random Seed | 42 | 42 |

**Key Difference:** Reduced shadow budget (500 → 100) to minimize hardware runtime.

## Mitigation Strategy

**None for This Experiment**

Smoke test uses v0 baseline to characterize raw hardware noise. Mitigation introduced in S-T02:
- **MEM** (Measurement Error Mitigation): Confusion matrix calibration
- **ZNE** (Zero-Noise Extrapolation): Planned for Phase 2
- **Inverse Channel**: v1 noise-aware shadows in S-T02

## Hardware Execution Workflow

### Step 1: Backend Selection

```bash
# Check backend status
quartumse runtime-status --json \
  --backend ibm:ibm_fez \
  --instance ibm-q/open/main
```

Output includes:
- Queue depth (pending jobs)
- Runtime quota remaining
- Calibration timestamp

**Decision:** Proceed if queue < 200 jobs and calibration < 24 hours old.

### Step 2: Execute Smoke Test

```bash
cd C:\Users\User\Desktop\Projects\QuartumSE

python experiments/shadows/S_T01_ghz_baseline.py \
  --backend ibm:ibm_fez \
  --variant st01 \
  --shadow-size 100 \
  --seed 42 \
  --data-dir ./data
```

**Expected Execution:**
1. **Job Submission:** Circuit transpiled and submitted to ibm_fez
2. **Queue Wait:** 0-30 minutes depending on queue depth
3. **Execution:** ~7-15 seconds for 100 shadow snapshots
4. **Retrieval:** Results fetched and processed
5. **Manifest Save:** Provenance captured with IBM calibration data

### Step 3: Monitor Execution

```bash
# In separate terminal, tail logs if available
# Or use IBM Quantum dashboard to monitor job status
```

## Backend Provenance Capture

### IBM Calibration Snapshot

Manifest includes:
- **Calibration Timestamp:** When backend was last calibrated
- **Properties Hash:** SHA-256 of calibration data for versioning
- **T1/T2 Times:** Per-qubit coherence times
- **Gate Errors:** Single-qubit (SX, X, RZ) and two-qubit (CZ) error rates
- **Readout Errors:** Per-qubit measurement fidelity
- **Topology:** Qubit connectivity graph

Example manifest field:
```json
{
  "backend_snapshot": {
    "name": "ibm_fez",
    "num_qubits": 156,
    "calibration_timestamp": "2025-11-03T13:17:32Z",
    "properties_hash": "a1b2c3...",
    "qubits_used": [0, 1, 2],
    "t1_times": [63.6, 174.8, 208.9],
    "t2_times": [49.7, 199.1, 178.7],
    "readout_errors": [0.0098, 0.0222, 0.0077],
    "gate_errors": {
      "sx_0": 0.000364,
      "cx_0_1": 0.01083,
      ...
    }
  }
}
```

### Runtime Tracking

Manifest captures:
- **Submission Time:** When job entered IBM queue
- **Execution Start:** When quantum processor began executing
- **Execution Duration:** Wall-clock time on hardware
- **Retrieval Time:** When results returned to client

**Smoke Test Metrics (Nov 3, 2025, ibm_fez):**
- Total execution: 7.82 seconds
- Queue wait: < 5 minutes (low queue depth)

## Data Storage

Same structure as SMOKE-SIM:
- **Manifest:** `data/manifests/{experiment_id}.json`
- **Shot Data:** `data/shots/{experiment_id}.parquet`
- **Console Logs:** Captured in terminal output

## Validation Checks

Automated validation in script:
1. **Execution Success:** Job completes without IBM errors
2. **Result Retrieval:** Counts dict populated with 2^3 = 8 bitstrings
3. **Observable Estimation:** All 5 observables have expectation values and CIs
4. **Manifest Completeness:** Backend snapshot non-null

**Expected Warnings:**
- Observables may fall outside CIs due to hardware noise
- SSR may be < 1.0× if noise dominates
- Runtime may exceed estimate if queue saturated

## Comparison to Simulator

### Expected Degradation

| Metric | SMOKE-SIM | SMOKE-HW (Expected) |
|--------|-----------|---------------------|
| ZZI Estimate | 1.0000 | 0.85-0.95 (noise) |
| ZIZ Estimate | 1.0000 | 0.85-0.95 (noise) |
| CI Coverage | 100% | 60-80% (wider CIs) |
| SSR | 17.37× | 1.1-2.0× (realistic) |
| Execution Time | 8s | 8-15s (overhead) |

**Noise Sources:**
- **Gate Errors:** ~1% for CNOTs, ~0.04% for single-qubit
- **Readout Errors:** 0.77-2.22% across qubits 0-2
- **Decoherence:** T1=63-209 μs, T2=49-199 μs

**Impact Estimate:**
- ZZ expectation reduced by 5-15% due to CNOT errors and T2 dephasing
- Single-qubit Z observables less affected (no entanglement degradation)

## Key Code Differences from SMOKE-SIM

### Backend Descriptor

```python
# SMOKE-SIM
backend_descriptor = "aer_simulator"

# SMOKE-HW
backend_descriptor = "ibm:ibm_fez"
```

### Shadow Size

```python
# SMOKE-SIM
shadow_size = 500

# SMOKE-HW
shadow_size = 100  # Reduced for speed
```

### Expected Execution Time

SMOKE-SIM: < 1 second (local)
SMOKE-HW: 5-30 minutes (queue + execution + retrieval)

## Next Experiments

Upon successful completion:
1. **S-T01:** Increase shadow_size to 200-500, run ≥10 trials
2. **S-T02:** Add MEM, compare v0 vs. v1 on same ibm_fez backend
3. **C-T01:** Apply validated hardware access to H₂ chemistry experiment

## Link to Executable Notebook

Interactive notebook: `notebooks/experiments/shadows/smoke_test_hardware.ipynb` [TBD]

For now, use standalone script: `experiments/shadows/S_T01_ghz_baseline.py --backend ibm:ibm_fez`
