# QuartumSE Data Storage Conventions

This document explains the data directory structure and when to use each directory.
By default, `ShadowEstimator` writes manifests and Parquet files under `./data`
unless you override `data_dir`.

## Directory Overview

```
QuartumSE/
├── data/                  # Production experiment data
├── validation_data/       # Phase 1 validation & smoke tests
├── demo_data/             # Notebook demos & tutorials
├── notebook_data/         # Interactive notebook experimentation
└── experiments/validation/archived_runs/  # Archived validation results
```

## When to Use Each Directory

### `data/` - Production Experiments

**Use for:**
- Final, production-quality experiments
- Data intended for publication or reports
- Long-term archival
- Experiments in workstreams C/O/B/M (Chemistry, Optimization, Benchmarking, Metrology)

**Examples:**
```python
estimator = ShadowEstimator(backend="ibm:ibm_torino", data_dir="data")
```

**Retention:** Keep indefinitely, archive carefully

---

### `validation_data/` - Phase 1 Validation & Testing

**Use for:**
- Hardware validation experiments (S-T01, S-T02, etc.)
- Smoke tests on IBM hardware
- SSR verification experiments
- Phase 1 exit criteria validation
- Shadow experiment scripts (`experiments/shadows/*/run_*.py`)

**Scripts/notebooks that use this:**
- `experiments/shadows/preliminary_test/run_smoke_test.py`
- `experiments/validation/hardware_validation.py`
- `experiments/shadows/extended_ghz/run_ghz_extended.py`
- `experiments/shadows/parallel_bell_pairs/run_bell_pairs.py`
- Hardware sections of `notebooks/comprehensive_test_suite.ipynb`

**Examples:**
```python
estimator = ShadowEstimator(backend="ibm:ibm_torino", data_dir="validation_data")
```

**Retention:**
- Keep during Phase 1 validation period
- Archive successful runs to `experiments/validation/archived_runs/`
- Move final validation results to `data/` for publication

---

### `demo_data/` - Demos & Tutorials

**Use for:**
- Notebook demonstrations
- Quickstart examples
- Tutorial walkthroughs
- Non-critical testing

**Notebooks that use this:**
- `notebooks/quickstart_shot_persistence.ipynb`
- `notebooks/comprehensive_test_suite.ipynb`
- `notebooks/noise_aware_shadows_demo.ipynb`

**Examples:**
```python
estimator = ShadowEstimator(backend=AerSimulator(), data_dir="demo_data")
```

**Retention:** Ephemeral - safe to delete at any time

---

### `notebook_data/` - Interactive Notebooks

**Use for:**
- Jupyter notebook experimentation
- Development and debugging
- Exploratory data analysis
- One-off interactive tests

**Examples:**
```python
estimator = ShadowEstimator(backend="ibm:ibm_torino", data_dir="notebook_data")
```

**Retention:** Ephemeral - safe to delete at any time

---

## Directory Structure

All data directories follow the same subdirectory structure:

```
{data_dir}/
├── manifests/          # Provenance manifests (JSON)
│   └── {experiment_id}.json
├── shots/              # Raw measurement data (Parquet)
│   └── {experiment_id}.parquet
├── reports/            # Generated reports (HTML/PDF)
│   └── {experiment_id}_report.html
└── calibrations/       # MEM confusion matrices (optional)
    └── {experiment_id}_confusion.json
```

See [`data/README.md`](https://github.com/quartumse/quartumse/blob/master/data/README.md) in the repository for detailed schema documentation.

---

## Git Tracking

All data directories are **git-ignored** except for:
- ✅ `README.md` files (documentation)
- ✅ `.gitkeep` files (preserve empty directories)
- ❌ JSON manifests (ignored)
- ❌ Parquet shot data (ignored)
- ❌ HTML/PDF reports (ignored)

**Reason:** Experimental data files are large and change frequently. Only code and documentation are version-controlled.

---

## Quick Commands

### Create all directories:
```bash
mkdir -p data/{manifests,shots,reports,calibrations}
mkdir -p validation_data/{manifests,shots,reports,calibrations}
mkdir -p demo_data
mkdir -p notebook_data
```

### Clean validation data:
```bash
rm -rf validation_data/{manifests,shots,reports,calibrations}/*
```

### Clean demo/notebook data:
```bash
rm -rf demo_data/* notebook_data/*
```

### List all experiments by directory:
```bash
ls -lh data/manifests/           # Production
ls -lh validation_data/manifests/ # Validation
ls -lh demo_data/manifests/      # Demos
```

### Check total data usage:
```bash
du -sh data/ validation_data/ demo_data/ notebook_data/
```

---

## Storage Estimates

### Phase 1 (6 validation experiments):
- **validation_data/**: ~1.6 MB
- **data/**: ~0 MB (not used yet)

### Phase 2+ (Production workloads):
- **data/**: ~50-100 MB per workstream (C/O/B/M)
- **validation_data/**: Archived after Phase 1

### Per Experiment:
- Manifest: ~10 KB
- Shot data (500 shots, 3 qubits): ~50-100 KB
- Report: ~50 KB
- **Total per experiment**: ~100-200 KB

---

## Best Practices

1. **Always specify `data_dir`** explicitly in scripts:
   ```python
   # Good
   estimator = ShadowEstimator(..., data_dir="validation_data")

   # Bad (default may change)
   estimator = ShadowEstimator(...)
   ```

2. **Use appropriate directory for purpose**:
   - Production → `data/`
   - Validation/testing → `validation_data/`
   - Demos → `demo_data/`
   - Notebooks → `notebook_data/`

3. **Archive validation results** after Phase 1:
   ```bash
   cp validation_data/manifests/final_validation.json \
      experiments/validation/archived_runs/results_final.txt
   ```

4. **Clean temporary directories regularly**:
   ```bash
   # Weekly cleanup
   rm -rf demo_data/* notebook_data/*
   ```

5. **Check storage usage** before long experiment runs:
   ```bash
   df -h .  # Check available disk space
   du -sh validation_data/  # Check current usage
   ```

---

## FAQ

**Q: Which directory should I use for the preliminary smoke test?**
A: `validation_data/` - it's part of Phase 1 validation.

**Q: Can I move experiments between directories?**
A: Yes! Manifests and shot data are self-contained. Just copy/move the files:
```bash
mv validation_data/manifests/{id}.json data/manifests/
mv validation_data/shots/{id}.parquet data/shots/
```

**Q: What if I accidentally delete a data directory?**
A: All directories auto-create subdirectories when needed. Just re-run your experiment or manually recreate:
```bash
mkdir -p validation_data/{manifests,shots,reports,calibrations}
```

**Q: How do I back up my validation data?**
A: Copy the entire directory:
```bash
cp -r validation_data/ validation_data_backup_$(date +%Y%m%d)
```

**Q: Why are Parquet files ignored by git?**
A: They're binary files that can be large (MBs) and change frequently. Git is optimized for text files (code, docs).

---

**Last Updated:** 2025-10-22
**QuartumSE Version:** 0.1.0
