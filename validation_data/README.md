# Validation Data Directory

This directory stores experimental data from **validation experiments and smoke tests** for QuartumSE Phase 1 hardware validation.

## Purpose

Separate storage for validation experiments (`experiments/validation/`, `experiments/shadows/preliminary_test/`) to keep test data isolated from production experiments stored in the main `data/` directory.

## Directory Structure

```
validation_data/
├── manifests/          # Provenance manifests (JSON)
├── shots/              # Raw measurement data (Parquet)
├── reports/            # Generated HTML/PDF reports
├── calibrations/       # MEM confusion matrices (optional)
└── README.md
```

## Usage

**Experiments that write here:**
- `experiments/shadows/preliminary_test/run_smoke_test.py` - Bell state smoke test
- `experiments/validation/hardware_validation.py` - Phase 1 GHZ validation
- `experiments/shadows/*/run_*.py` - All shadow experiment scripts
- `notebooks/preliminary_smoke_test.ipynb` - Interactive smoke test

**Example script usage:**
```python
from quartumse import ShadowEstimator

estimator = ShadowEstimator(
    backend="ibm:ibm_torino",
    data_dir="validation_data"  # <-- Uses this directory
)
```

## Data Schema

Identical to the main `data/` directory. See [`../data/README.md`](../data/README.md) for full schema documentation.

## Storage Estimates

For Phase 1 validation experiments (6 experiments × ~2000 shots avg):
- **Manifests**: ~60 KB (6 × ~10 KB)
- **Shot data**: ~1.2 MB (6 × ~200 KB)
- **Reports**: ~300 KB (6 × ~50 KB)
- **Total**: ~1.6 MB

## File Retention

**Short-term storage:**
- Keep for duration of Phase 1 validation
- Archive successful runs to `experiments/validation/archived_runs/`
- Delete failed/debugging runs after confirmation

**Long-term storage:**
- Move successful validation results to main `data/` directory
- Keep final Phase 1 validation manifest for publication

## Git Tracking

This directory is **ignored by git** (see `.gitignore`) to prevent committing:
- Large Parquet files
- Potentially sensitive backend calibration data
- Temporary test results

Only this README is version-controlled.

---

**Tip:** To quickly clear all validation data:
```bash
rm -rf validation_data/{manifests,shots,reports}/*
```

**Tip:** To view all validation experiments:
```bash
ls -lh validation_data/manifests/
```
