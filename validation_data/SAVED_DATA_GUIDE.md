# Validation Data: What Gets Saved

This guide explains exactly what data is saved when you run validation experiments, how to access it later, and what you can do with it.

---

## Overview

Every validation experiment saves **three types of data**:

1. **Provenance Manifests** (JSON) - Complete experiment metadata
2. **Shot Data** (Parquet) - Raw quantum measurements for replay
3. **Summary Results** (JSON) - Human-readable results compilation

---

## 1. Provenance Manifests

### What They Contain

**File**: `validation_data/manifests/{experiment_id}.json`

Each manifest is a complete record of the experiment:

```json
{
  "experiment_id": "a3f2b8c9d1e4f5g6...",
  "timestamp": "2025-10-22T14:30:00.123456Z",
  "quartumse_version": "0.1.0",

  "circuit": {
    "num_qubits": 2,
    "depth": 2,
    "gate_counts": {"h": 1, "cx": 1},
    "circuit_hash": "4e13787abc44d957..."
  },

  "backend": {
    "backend_name": "ibm_torino",
    "num_qubits": 133,
    "calibration_timestamp": "2025-10-22T10:00:00Z",
    "t1_times": {"0": 245.3, "1": 198.7, ...},
    "t2_times": {"0": 123.4, "1": 156.2, ...},
    "readout_errors": {"0": 0.012, "1": 0.018, ...},
    "gate_errors": {"cx": 0.0045, "x": 0.0002, ...}
  },

  "shadows": {
    "version": "v1",
    "shadow_size": 200,
    "random_seed": 43,
    "apply_inverse_channel": true
  },

  "mitigation": {
    "techniques": ["MEM"],
    "parameters": {"mem_shots": 128}
  },

  "results": {
    "ZZ": {
      "expectation_value": 0.876,
      "variance": 0.023,
      "ci_95": [0.812, 0.940],
      "ci_width": 0.128
    },
    "XX": { ... }
  },

  "resource_usage": {
    "total_shots": 200,
    "calibration_shots": 512,
    "execution_time_seconds": 45.3
  }
}
```

### Why Manifests Matter

- ✅ **Complete reproducibility** - Every parameter recorded
- ✅ **Backend calibration snapshot** - Know exact hardware state
- ✅ **Results included** - No need to recompute from raw data
- ✅ **Version tracking** - Qiskit, Python, QuartumSE versions recorded

### How to Use

```python
from quartumse.reporting.manifest import ProvenanceManifest

# Load manifest
manifest = ProvenanceManifest.from_json('validation_data/manifests/{id}.json')

# Access any field
print(manifest.schema.backend.backend_name)
print(manifest.schema.shadows.shadow_size)
print(manifest.schema.results_summary)

# Verify reproducibility
manifest.validate(require_shot_file=True)
```

---

## 2. Shot Data (Parquet)

### What They Contain

**File**: `validation_data/shots/{experiment_id}.parquet`

Raw measurement outcomes for every shadow:

| shot_id | measurement_basis | measurement_outcome |
|---------|-------------------|---------------------|
| 0       | XY                | 10                  |
| 1       | ZZ                | 01                  |
| 2       | YX                | 11                  |
| ...     | ...               | ...                 |

- **`shot_id`**: Sequential shadow number (0 to shadow_size-1)
- **`measurement_basis`**: Pauli basis string (e.g., "XY" = X on qubit 0, Y on qubit 1)
- **`measurement_outcome`**: Bitstring result (e.g., "10" = qubit 0 measured 1, qubit 1 measured 0)

### Why Shot Data Matters

- ✅ **"Measure once, ask later"** - Compute new observables without re-running
- ✅ **Diagnostics** - Analyze measurement patterns, detect anomalies
- ✅ **Verification** - Independent recalculation of results
- ✅ **Research** - Study measurement statistics, bias, correlations

### How to Use

```python
import pandas as pd
from quartumse.reporting.shot_data import ShotDataWriter

# Load shot data directly
df = pd.read_parquet('validation_data/shots/{id}.parquet')
print(df.head())

# Or use the writer utility
writer = ShotDataWriter('validation_data')
bases, outcomes, num_qubits = writer.load_shadow_measurements('{experiment_id}')

# Replay with new observables
from quartumse import ShadowEstimator
from quartumse.shadows.core import Observable

estimator = ShadowEstimator(backend='...', data_dir='validation_data')
new_observables = [Observable('YY', 1.0), Observable('ZX', 1.0)]

# No hardware re-execution!
try:
    result = estimator.replay_from_manifest(
        'validation_data/manifests/{id}.json',
        observables=new_observables
    )
except FileNotFoundError as exc:
    print(f"Missing calibration artifact: {exc}")
else:
    print(result.observables['YY']['expectation_value'])
```

---

## 3. Summary Results (JSON)

### What They Contain

**File**: `validation_data/smoke_test_results_{timestamp}.json`

Human-readable compilation of all results from a smoke test run:

```json
{
  "metadata": {
    "test_name": "preliminary_smoke_test",
    "timestamp": "2025-10-22T14:30:00.123456Z",
    "backend": "ibm_torino",
    "observables": ["ZZ", "XX"]
  },

  "direct_measurements": {
    "method": "Direct Pauli measurement",
    "total_shots": 500,
    "results": {
      "ZZ": {
        "expectation": 0.892,
        "shots": 250,
        "counts": {"00": 234, "11": 230, "01": 8, "10": 3}
      },
      "XX": { ... }
    }
  },

  "shadows_v0": {
    "method": "Classical Shadows v0 (baseline)",
    "experiment_id": "...",
    "manifest_path": "validation_data/manifests/...json",
    "shot_data_path": "validation_data/shots/...parquet",
    "results": { ... }
  },

  "shadows_v1": {
    "method": "Classical Shadows v1 (noise-aware with MEM)",
    "results": { ... }
  },

  "comparison": {
    "expected_values": {"ZZ": 1.0, "XX": 1.0},
    "table": [ ... ]
  }
}
```

### Why Summary Results Matter

- ✅ **Quick review** - All methods in one file
- ✅ **Includes direct measurements** - Not stored elsewhere
- ✅ **Timestamped** - Track multiple runs over time
- ✅ **Comparison table** - Side-by-side results
- ✅ **Human-readable** - JSON format for easy inspection

### How to Use

```python
import json

# Load summary
with open('validation_data/smoke_test_results_20251022_143000.json', 'r') as f:
    results = json.load(f)

# Compare methods
direct_zz = results['direct_measurements']['results']['ZZ']['expectation']
v0_zz = results['shadows_v0']['results']['ZZ']['expectation_value']
v1_zz = results['shadows_v1']['results']['ZZ']['expectation_value']

print(f"Direct: {direct_zz:.3f}")
print(f"v0:     {v0_zz:.3f}")
print(f"v1:     {v1_zz:.3f}")

# Access manifest paths for deeper analysis
manifest_path = results['shadows_v1']['manifest_path']
shot_data_path = results['shadows_v1']['shot_data_path']
```

---

## File Organization

```
validation_data/
├── manifests/
│   ├── {v0_experiment_id}.json          # Shadow v0 manifest
│   └── {v1_experiment_id}.json          # Shadow v1 manifest
│
├── shots/
│   ├── {v0_experiment_id}.parquet       # Shadow v0 raw measurements
│   └── {v1_experiment_id}.parquet       # Shadow v1 raw measurements
│
├── smoke_test_results_20251022_143000.json   # Complete summary
└── smoke_test_results_20251022_150000.json   # Another run (if repeated)
```

---

## Storage Estimates

### Per Smoke Test Run:
- **2 manifests**: ~20 KB (10 KB each)
- **2 shot files**: ~100-150 KB (50-75 KB each)
- **1 summary**: ~10 KB
- **Total**: ~130-180 KB

### Multiple Runs:
- Each repeat adds another ~130-180 KB
- Summary files accumulate (10 KB each)
- Manifests/shots overwrite if same experiment_id

### Cleanup:
```bash
# Remove all smoke test summaries
rm validation_data/smoke_test_results_*.json

# Keep only latest run of each type
ls -t validation_data/manifests/ | tail -n +3 | xargs -I {} rm validation_data/manifests/{}
```

---

## Review Workflow

### Immediate Review (During Notebook Run)

The notebook displays:
- ✅ Direct measurement results
- ✅ Shadow v0 results with confidence intervals
- ✅ Shadow v1 results with MEM
- ✅ Comparison table
- ✅ File paths for saved data

### Later Review (Days/Weeks Later)

**Option 1: Load Summary JSON**
```python
import json
with open('validation_data/smoke_test_results_20251022_143000.json', 'r') as f:
    results = json.load(f)

# Everything in one place
print(results['comparison']['table'])
```

**Option 2: Load Manifest for Full Details**
```python
from quartumse.reporting.manifest import ProvenanceManifest

manifest = ProvenanceManifest.from_json('validation_data/manifests/{id}.json')

# Access backend calibration
print(manifest.schema.backend.t1_times)
print(manifest.schema.backend.readout_errors)

# Verify execution time
print(f"Took {manifest.schema.resource_usage.execution_time_seconds}s")
```

**Option 3: Replay with New Observables**
```python
from quartumse import ShadowEstimator
from quartumse.shadows.core import Observable

estimator = ShadowEstimator(backend='...', data_dir='validation_data')

# Compute new observables from saved shots (v0 + v1 noise-aware)
try:
    new_result = estimator.replay_from_manifest(
        'validation_data/manifests/{id}.json',
        observables=[Observable('YY'), Observable('XZ')]
    )
except FileNotFoundError as exc:
    print(f"Missing calibration artifact: {exc}")
else:
    print(new_result.observables['YY']['expectation_value'])
```

> ℹ️ Noise-aware manifests rely on the saved confusion matrix in `validation_data/mem/{experiment_id}.npz`. Keep this file with the manifest and shot data to enable replay.

---

## What You CAN Do Later

✅ **Reload and review** all results
✅ **Compute new observables** from saved shots
✅ **Verify reproducibility** with manifest seeds
✅ **Compare multiple runs** over time
✅ **Extract backend calibration** data
✅ **Generate reports** from manifests
✅ **Analyze shot patterns** in Parquet files

## What You CANNOT Do Later

❌ **Change shadow size** - Would need to re-run on hardware
❌ **Apply different MEM** - Replay reuses the saved confusion matrix; new calibrations require a fresh experiment
❌ **Modify circuit** - Would need new experiment
❌ **Use different backend** - Hardware state was captured

---

## FAQ

**Q: Do I need to save anything manually?**
A: No! Everything is automatically saved when `save_manifest=True` (default).

**Q: Can I delete summary JSON files?**
A: Yes, they're redundant with manifests but convenient for quick review.

**Q: What if I lose the shot data files?**
A: You can't replay, but results are still in manifests.

**Q: How do I share results with collaborators?**
A: Share the summary JSON for quick review, or the full manifest+shots for reproducibility.

**Q: Can I version control this data?**
A: Only summaries (small JSON). Manifests/shots are git-ignored (too large).

**Q: How long should I keep this data?**
A: Manifests indefinitely (small), shots until validated (can archive), summaries for reference.

---

**Last Updated:** 2025-10-22
**QuartumSE Version:** 0.1.0
