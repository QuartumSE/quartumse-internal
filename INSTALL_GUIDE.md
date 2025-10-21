# QuartumSE Installation & Quickstart Guide

## Prerequisites

- **Python 3.10, 3.11, or 3.12** (3.13 supported with limited features)
- **pip** package manager
- **Git** (for cloning repository)
- **Jupyter** (optional, for running notebooks)

---

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/QuartumSE/quartumse.git
cd quartumse
```

### 2. Install Package in Development Mode

```bash
# Core package (works with Python 3.10-3.13)
pip install -e .

# OR with development tools
pip install -e ".[dev]"

# OR with optional features (Python 3.10-3.12 only)
pip install -e ".[dev,mitigation,chemistry]"
```

**Installation options:**
- **Core only**: Shadows, estimator, provenance, reporting
- **`[dev]`**: Adds pytest, black, ruff, mypy, jupyter
- **`[mitigation]`**: Adds mitiq for error mitigation (Python <3.13)
- **`[chemistry]`**: Adds qiskit-nature for VQE experiments (Python <3.13)

### 3. Verify Installation

```bash
# Check version
quartumse version

# Run test suite (optional)
pytest tests/unit/ -v
```

**Expected output:**
```
QuartumSE v0.1.0
✓ 15/18 core tests passing
```

---

## Running the Quickstart Notebook

### Option A: Jupyter Notebook (Recommended)

```bash
# Install jupyter if not already installed
pip install jupyter

# Start Jupyter
jupyter notebook

# Open: notebooks/quickstart_shot_persistence.ipynb
```

### Option B: Jupyter Lab

```bash
# Install jupyter lab
pip install jupyterlab

# Start Jupyter Lab
jupyter lab

# Navigate to notebooks/quickstart_shot_persistence.ipynb
```

### Option C: VS Code

1. Open VS Code in the `quartumse/` directory
2. Install "Jupyter" extension
3. Open `notebooks/quickstart_shot_persistence.ipynb`
4. Select Python interpreter (should detect your environment)
5. Click "Run All"

---

## What the Notebook Demonstrates

The quickstart notebook shows:

1. **Classical Shadows Estimation**
   - Create a 3-qubit GHZ state
   - Estimate 4 observables using random-local-Clifford shadows
   - Get expectation values with 95% confidence intervals

2. **Shot Data Persistence** (NEW in v0.1.0)
   - Automatic saving of measurement data to Parquet format
   - Provenance manifests with full experiment metadata
   - ~10 KB file for 500 shadows

3. **Reproducibility**
   - Replay experiments from saved shot data
   - Verify exact match with original estimates
   - No backend re-execution required

4. **"Measure Once, Ask Later"**
   - Compute NEW observables from saved shadow data
   - Classical shadows' key advantage: multi-observable reuse
   - Example: Compute III, IZZ, YYY from data originally used for ZZZ, XXX, ZZI, ZII

---

## Expected Results

When you run the notebook, you should see:

```
✓ Estimation complete in ~2s
  Backend: aer_simulator
  Shots used: 500
  Manifest saved: ./notebook_data/manifests/<uuid>.json

Observable Estimates:
=====================================================================
Observable      Expectation     ±95% CI         Variance
=====================================================================
1.0*ZZZ              0.0180     ±0.0340              0.0003
1.0*XXX              0.0320     ±0.0309              0.0002
1.0*ZZI              0.1240     ±0.0578              0.0007
1.0*ZII              0.0300     ±0.0340              0.0003

✓ Shot data persisted to Parquet
  File: <uuid>.parquet
  Size: 10,108 bytes (9.9 KB)

✓ Replay complete (no backend execution required)
✓ All replayed values match exactly

✓ NEW observables computed from saved data
  Observables computed: 3 (III, IZZ, YYY)
  Using same 500 shadows from before
```

---

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'quartumse'`

**Solution:**
```bash
# Make sure you installed in editable mode from repo root
cd /path/to/quartumse
pip install -e .
```

### Python 3.13 Compatibility

**Problem:** `mitiq` or `qiskit-nature` installation fails on Python 3.13

**Solution:** These are optional dependencies. Install core only:
```bash
pip install -e .  # Core features work on 3.13
```

Or use Python 3.10-3.12 for full feature set.

### Jupyter Kernel Issues

**Problem:** Jupyter can't find `quartumse` module

**Solution:**
```bash
# Install ipykernel in your environment
pip install ipykernel

# Register kernel
python -m ipykernel install --user --name quartumse --display-name "Python (quartumse)"

# Select this kernel in Jupyter
```

### Test Failures

**Problem:** Some manifest tests fail

**Known issue:** 3 old manifest tests need fixture updates (non-blocking)
- `test_circuit_fingerprint_creation`
- `test_manifest_creation_and_save`
- `test_manifest_tags`

**Core functionality (shot persistence, shadows) is fully tested and working.**

---

## Directory Structure After Installation

```
quartumse/
├── src/quartumse/          # Main package
│   ├── estimator/          # ShadowEstimator
│   ├── shadows/            # Classical shadows implementations
│   ├── reporting/          # Manifests + shot data persistence
│   ├── mitigation/         # Error mitigation (placeholders)
│   └── connectors/         # Backend connectors (IBM Runtime ready)
├── tests/                  # Test suite
│   └── unit/
│       ├── test_shadows_v0.py      (6/6 passing ✓)
│       └── test_shot_data.py       (6/6 passing ✓)
├── experiments/            # Example experiments
│   └── shadows/
│       └── S_T01_ghz_baseline.py
├── notebooks/              # Jupyter notebooks
│   └── quickstart_shot_persistence.ipynb
├── data/                   # Data directory (created on first run)
│   ├── shots/              # Parquet shot data
│   └── manifests/          # JSON provenance manifests
└── pyproject.toml          # Package configuration
```

---

## What Works in v0.1.0

✅ **Implemented & Tested:**
- Classical Shadows v0 (random local Clifford)
- ShadowEstimator API
- Shot data persistence (Parquet)
- Provenance manifests
- Replay from saved data
- Observable reusability ("measure once, ask later")
- S-T01 GHZ baseline experiment

❌ **Not Yet Implemented (Phase 1 gaps):**
- Noise-aware shadows v1
- Measurement error mitigation (MEM/M3)
- Zero-noise extrapolation (ZNE)
- C/O/B/M experiment suites

## Configuring IBM Quantum access

QuartumSE now ships with an IBM Quantum connector that authenticates through Qiskit Runtime.
Follow these steps before targeting managed IBM backends:

1. **Create an API token** in the IBM Quantum dashboard and export one of
   `QISKIT_IBM_TOKEN` or `QISKIT_RUNTIME_API_TOKEN`.
2. *(Optional)* Set `QISKIT_IBM_CHANNEL` and `QISKIT_IBM_INSTANCE` if you need to
   pin execution to a specific hub/group/project.
3. Run `quartumse run --config <config.yaml>` to validate credentials and preview
   the calibration snapshot that will be embedded in your manifest.
4. Use `python experiments/shadows/S_T01_ghz_baseline.py --backend ibm:ibmq_qasm_simulator`
   to execute the GHZ baseline with the connector-enabled backend descriptor.

If credentials are missing, the connector transparently falls back to the local Aer
simulator while still emitting a provenance snapshot for reproducibility.

---

## Next Steps

1. **Run the quickstart notebook** - See shot persistence in action
2. **Explore `experiments/shadows/S_T01_ghz_baseline.py`** - Command-line example
3. **Check `ROADMAP.md`** - See Phase 1 objectives and timeline
4. **Read `PROJECT_BIBLE.md`** - Understand the vision

---

## Getting Help

- **Issues:** https://github.com/QuartumSE/quartumse/issues
- **Docs:** Coming in Phase 2
- **Examples:** See `experiments/` and `notebooks/`

---

**QuartumSE v0.1.0** - Vendor-neutral quantum measurement optimization
Built with Classical Shadows + Provenance Tracking
