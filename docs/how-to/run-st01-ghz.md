# Run S-T01 GHZ Experiment

The S-T01/S-T02 experiments validate classical shadows on GHZ states, measuring Shot-Savings Ratio (SSR) and confidence interval (CI) coverage against Phase 1 exit criteria.

## Overview

**S-T01** (baseline): Classical shadows v0 without mitigation
**S-T02** (noise-aware): Classical shadows v1 with MEM calibration

Both variants support:
- GHZ states from 2-5 qubits
- Configurable backends (Aer simulator or IBM Quantum hardware)
- Automatic SSR calculation vs direct measurement baseline
- Manifest + shot data persistence for replay

---

## Quick Start

### S-T01 (Baseline) on Simulator

**Unix/macOS:**
```bash
python experiments/shadows/S_T01_ghz_baseline.py --backend aer_simulator --variant st01
```

**Windows:**
```powershell
python experiments/shadows/S_T01_ghz_baseline.py --backend aer_simulator --variant st01
```

**Expected output:**
```
====================================================================================
S-T01 GHZ Validation (classical shadows v0 baseline)
====================================================================================
Backend: aer_simulator
Shadow size: 256 per GHZ state
Baseline shots: 1024 per observable
====================================================================================

Testing GHZ(2)...
Observable            Shadows    Expected    Baseline    CI Width    SSR  In CI
--------------------------------------------------------------------------------
1.0*ZI                 0.0039      0.0000      0.0020      0.1800  1.45  ✓
1.0*IZ                -0.0078      0.0000     -0.0039      0.1756  1.38  ✓
1.0*ZZ                 0.9961      1.0000      0.9941      0.0488  5.32  ✓

============================================================
METRICS for GHZ(2)
============================================================
CI Coverage:         100.00% (target: ≥90%)
SSR (estimated):     2.72× (target: ≥1.2×)
Shadow size:         256
Baseline shots:      1024

[... similar output for GHZ(3), GHZ(4), GHZ(5) ...]

================================================================================
EXPERIMENT SUMMARY
================================================================================

Qubits     CI Coverage    SSR        Status
--------------------------------------------------
2          100.00%        2.72       ✓ PASS
3          100.00%        3.14       ✓ PASS
4          100.00%        2.89       ✓ PASS
5          93.33%         2.45       ✓ PASS

================================================================================
✓ EXPERIMENT PASSED - Phase 1 exit criteria met!
================================================================================
```

**Artifacts saved:**
- Manifests: `data/manifests/<experiment_id>.json`
- Shot data: `data/shots/<experiment_id>.parquet`
- Change the base directory with `--data-dir` (see [Common flags](#common-flags))

---

## S-T02 (Noise-Aware) with MEM

**Unix/macOS:**
```bash
python experiments/shadows/S_T01_ghz_baseline.py --backend aer_simulator --variant st02
```

**Windows:**
```powershell
python experiments/shadows/S_T01_ghz_baseline.py --backend aer_simulator --variant st02
```

**Key differences:**
- Runs MEM calibration before shadow measurements (8 basis states × shots)
- Applies inverse confusion matrix during reconstruction
- Typically shows better SSR on noisy hardware (similar on ideal simulator)

**Expected output (additional MEM info):**
```
====================================================================================
S-T02 GHZ Validation (classical shadows v1 + MEM)
====================================================================================

Testing GHZ(3)...
  Step 1: MEM calibration (8 basis states × 512 shots = 4096 total)
  Step 2: Shadow measurements (256 shots)
  Step 3: Noise correction via confusion matrix

Confusion matrix (3 qubits):
[[0.998 0.002 ... 0.000]
 [0.001 0.996 ... 0.001]
 ...
 [0.000 0.001 ... 0.997]]

Observable            Shadows    Expected    Baseline    CI Width    SSR  In CI
--------------------------------------------------------------------------------
...
```

---

## Running on IBM Quantum Hardware

### Prerequisites

1. **Set IBM credentials:**

**Unix/macOS:**
```bash
export QISKIT_IBM_TOKEN="your_token_here"
# Optional: specify hub/group/project
export QISKIT_IBM_INSTANCE="ibm-q/open/main"
```

**Windows (PowerShell):**
```powershell
$env:QISKIT_IBM_TOKEN="your_token_here"
# Optional: specify hub/group/project
$env:QISKIT_IBM_INSTANCE="ibm-q/open/main"
```

**Windows (Command Prompt):**
```cmd
set QISKIT_IBM_TOKEN=your_token_here
rem Optional: specify hub/group/project
set QISKIT_IBM_INSTANCE=ibm-q/open/main
```

2. **Check remaining quota:**

**All platforms:**
```bash
quartumse runtime-status --backend ibm:ibm_brisbane
```

### Run on Hardware

**Unix/macOS:**
```bash
python experiments/shadows/S_T01_ghz_baseline.py \
  --backend ibm:ibm_brisbane \
  --variant st02
```

**Windows:**
```powershell
python experiments/shadows/S_T01_ghz_baseline.py `
  --backend ibm:ibm_brisbane `
  --variant st02
```

**Note:** Hardware runs may take 10-30 minutes depending on queue depth and shot counts.

---

## Using a Configuration File

Create `config.yaml`:

```yaml
backend:
  provider: ibm
  name: ibm_brisbane

shadow_size: 512
baseline_shots: 2048

# For S-T02 (MEM)
mem_shots: 1024
mem_qubits: [0, 1, 2, 3, 4]
```

**Run with config:**

**Unix/macOS:**
```bash
python experiments/shadows/S_T01_ghz_baseline.py \
  --config config.yaml \
  --variant st02
```

**Windows:**
```powershell
python experiments/shadows/S_T01_ghz_baseline.py `
  --config config.yaml `
  --variant st02
```

**Override backend from command line:**

**Unix/macOS:**
```bash
python experiments/shadows/S_T01_ghz_baseline.py \
  --config config.yaml \
  --backend ibm:ibmq_qasm_simulator \
  --variant st02
```

**Windows:**
```powershell
python experiments/shadows/S_T01_ghz_baseline.py `
  --config config.yaml `
  --backend ibm:ibmq_qasm_simulator `
  --variant st02
```

---

## Understanding the Output

### Metrics Explained

**CI Coverage**
- Percentage of observables where true value falls within 95% confidence interval
- **Target:** ≥90% for Phase 1 validation
- **Typical:** 93-100% on simulator, 85-95% on hardware

**SSR (Shot-Savings Ratio)**
- Ratio of baseline shots to shadow shots needed for equivalent precision
- **Formula:** `SSR = (baseline_shots / shadow_size) × (baseline_error / shadow_error)²`
- **Target:** ≥1.2× for Phase 1 validation
- **Typical:** 2-7× on simulator, 1.1-3× on noisy hardware

**Status**
- ✓ PASS: Both CI coverage ≥90% and SSR ≥1.2×
- ✗ FAIL: One or more criteria not met

### Observable Notation

- `ZI` = Z on qubit 0, Identity on qubit 1
- `ZZ` = Z on both qubits
- `ZZZ` = Z on all three qubits

For GHZ states:
- Even number of Z operators: expectation = +1
- Odd number of Z operators: expectation = 0

---

## Troubleshooting

**"Unable to resolve IBM backend"**
- Ensure `QISKIT_IBM_TOKEN` is set
- Check backend name is correct (use `quartumse runtime-status` to list)
- Verify credentials have access to the specified backend

**"ModuleNotFoundError: qiskit_ibm_runtime"**
- Install runtime dependencies: `pip install quartumse[mitigation]`

**"Insufficient runtime quota"**
- Check remaining quota: `quartumse runtime-status`
- Wait for monthly reset or use simulator
- Reduce shot counts in config file

**Poor SSR on hardware (<1.2×)**
- Expected for very noisy backends
- Try S-T02 variant with MEM (typically improves SSR by 20-40%)
- Use backends with lower readout error rates

**Manifest not found during replay**
- Check `data/manifests/` directory exists
- Verify experiment completed successfully (look for "✓ EXPERIMENT PASSED")
- Use full path to manifest file

---

## Next Steps

- **Replay experiments:** See [Replay from Manifest](replay-from-manifest.md)
- **Generate reports:** See [Generate Report](generate-report.md)
- **Run custom experiments:** Modify script or use notebooks
- **Hardware validation:** Follow [IBM Runtime Runbook](../ops/runtime_runbook.md)

---

## Related

- [MEM v1 Guide](run-mem-v1.md) - Details on measurement error mitigation
- [Testing Guide](run-tests.md) - Automated test suite and markers
- [Phase 1 Task Checklist](../strategy/phase1_task_checklist.md) - Exit criteria

## Common flags

The experiment script now shares the same CLI surface as other QuartumSE runs:

| Flag | Purpose | Default |
|------|---------|---------|
| `--backend` | Override the backend descriptor (`aer_simulator`, `ibm:ibm_brisbane`, etc.) | `aer_simulator` |
| `--shadow-size` | Number of classical shadow shots per GHZ size | `500` (configurable via YAML) |
| `--seed` | Random seed used when sampling classical shadows | `42` |
| `--data-dir` | Base directory for manifests, shot archives, and MEM data | `data/` |

All parameters can also be provided through the optional YAML config file. CLI
flags always win over configuration values, making it easy to experiment with
different shot budgets or output locations ad-hoc.
