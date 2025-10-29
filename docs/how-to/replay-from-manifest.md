# Replay from Manifest

QuartumSE's "measure once, ask later" capability lets you compute new observable estimates from saved measurement data without re-executing on quantum hardware.

## Overview

**Why replay?**
- **Zero hardware cost** - No additional quantum shots needed
- **Instant results** - Compute new observables in seconds
- **Reproducibility** - Same data, different analysis
- **Exploration** - Test hypotheses without waiting for hardware queue

**What's replayable:**
- Shadow measurement outcomes (bitstrings + bases)
- MEM confusion matrices (for v1 noise-aware shadows)
- Backend calibration snapshots
- Circuit fingerprints and random seeds

---

## Quick Start

### Basic Replay (Python API)

```python
from quartumse import ShadowEstimator
from quartumse.shadows.core import Observable

# Original experiment saved manifest to: data/manifests/a3f2b1c4...json

# Create estimator (backend not used during replay)
estimator = ShadowEstimator(backend="aer_simulator")

# Define NEW observables (different from original run)
new_observables = [
    Observable("XX", coefficient=1.0),
    Observable("YY", coefficient=1.0),
    Observable("ZZ", coefficient=1.0),
]

# Replay from saved manifest
result = estimator.replay_from_manifest(
    manifest_path="data/manifests/a3f2b1c4-5678-90ab-cdef-1234567890ab.json",
    observables=new_observables
)

# Access results (same structure as estimate())
for obs_str, data in result.observables.items():
    exp_val = data['expectation_value']
    variance = data['variance']
    ci = data['ci_95']
    ci_width = data['ci_width']

    print(f"{obs_str}:")
    print(f"  Value: {exp_val:.4f} ± {np.sqrt(variance):.4f}")
    print(f"  95% CI: [{ci[0]:.3f}, {ci[1]:.3f}] (width: {ci_width:.3f})")
```

**Output:**
```
1.0*XX:
  Value: 0.9844 ± 0.0312
  95% CI: [0.923, 1.046] (width: 0.123)
1.0*YY:
  Value: 0.9922 ± 0.0289
  95% CI: [0.936, 1.048] (width: 0.113)
1.0*ZZ:
  Value: 1.0039 ± 0.0156
  95% CI: [0.973, 1.035] (width: 0.061)
```

---

## Finding Manifests

### List saved experiments

**Unix/macOS:**
```bash
ls -lt data/manifests/ | head -10
```

**Windows:**
```powershell
Get-ChildItem data/manifests/ | Sort-Object LastWriteTime -Descending | Select-Object -First 10
```

### Inspect manifest metadata

```python
import json

manifest_path = "data/manifests/a3f2b1c4-5678-90ab-cdef-1234567890ab.json"

with open(manifest_path, 'r') as f:
    manifest = json.load(f)

print(f"Experiment ID: {manifest['experiment_id']}")
print(f"Created: {manifest['created_at']}")
print(f"Backend: {manifest['backend']['backend_name']}")
print(f"Shadow size: {manifest['shadows']['shadow_size']}")
print(f"Circuit qubits: {manifest['circuit']['num_qubits']}")
print(f"Original observables: {[obs['pauli'] for obs in manifest['observables']]}")
```

**Output:**
```
Experiment ID: a3f2b1c4-5678-90ab-cdef-1234567890ab
Created: 2025-10-29T14:32:15.789012
Backend: aer_simulator
Shadow size: 256
Circuit qubits: 3
Original observables: ['ZII', 'ZZI', 'ZZZ']
```

---

## Complete Replay Example

### Step 1: Run Original Experiment

```python
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from quartumse import ShadowEstimator
from quartumse.shadows import ShadowConfig
from quartumse.shadows.core import Observable

# Create GHZ state
circuit = QuantumCircuit(3)
circuit.h(0)
circuit.cx(0, 1)
circuit.cx(0, 2)

# Original observables (Z-type stabilizers)
original_obs = [
    Observable("ZII"),
    Observable("ZZI"),
    Observable("ZZZ"),
]

# Run experiment with manifest saving
config = ShadowConfig(shadow_size=256, random_seed=42)
estimator = ShadowEstimator(backend=AerSimulator(), shadow_config=config)

result = estimator.estimate(
    circuit=circuit,
    observables=original_obs,
    save_manifest=True  # Important!
)

print(f"Manifest saved: {result.manifest_path}")
print(f"Shot data saved: {result.shot_data_path}")
```

### Step 2: Replay with New Observables (Days/Weeks Later)

```python
# No hardware needed! Can run offline with saved data

from quartumse import ShadowEstimator
from quartumse.shadows.core import Observable

# Define new observables (X/Y type for comparison)
new_observables = [
    Observable("XII"),  # X on qubit 0
    Observable("XXI"),  # X on qubits 0-1
    Observable("XXX"),  # X on all qubits
]

# Replay (backend argument ignored during replay)
estimator = ShadowEstimator(backend="aer_simulator")

replayed = estimator.replay_from_manifest(
    manifest_path="data/manifests/a3f2b1c4-5678-90ab-cdef-1234567890ab.json",
    observables=new_observables
)

# Compare with analytical expectations for GHZ
ghz_x_expectations = {
    "1.0*XII": 0.0,   # Single X → 0
    "1.0*XXI": 0.0,   # Two X's → 0
    "1.0*XXX": 1.0,   # All X's → 1
}

print("\nReplayed Results:")
print(f"{'Observable':<15} {'Estimated':<12} {'Expected':<12} {'Error'}")
print("-" * 55)

for obs_str, data in replayed.observables.items():
    exp_val = data['expectation_value']
    expected = ghz_x_expectations[obs_str]
    error = abs(exp_val - expected)

    print(f"{obs_str:<15} {exp_val:>11.4f} {expected:>11.4f} {error:>9.4f}")
```

**Output:**
```
Replayed Results:
Observable      Estimated    Expected    Error
-------------------------------------------------------
1.0*XII             0.0156      0.0000    0.0156
1.0*XXI            -0.0234      0.0000    0.0234
1.0*XXX             0.9922      1.0000    0.0078
```

---

## Replay with Noise-Aware Shadows (v1 + MEM)

For experiments using MEM, the replay automatically loads the confusion matrix from the manifest.

```python
from quartumse import ShadowEstimator
from quartumse.shadows import ShadowConfig
from quartumse.shadows.config import ShadowVersion
from quartumse.shadows.core import Observable
from quartumse.reporting.manifest import MitigationConfig

# Original experiment (v1 with MEM)
config_v1 = ShadowConfig(
    version=ShadowVersion.V1_NOISE_AWARE,
    shadow_size=256,
    random_seed=42,
    apply_inverse_channel=True
)

mit_config = MitigationConfig(
    techniques=[],  # Populated automatically
    parameters={"mem_shots": 512}
)

estimator_v1 = ShadowEstimator(
    backend="aer_simulator",
    shadow_config=config_v1,
    mitigation_config=mit_config
)

# Run and save
result_v1 = estimator_v1.estimate(circuit, observables=original_obs, save_manifest=True)

# --- Later: Replay with MEM applied ---

# Replay loads confusion matrix path from manifest
replayed_v1 = estimator_v1.replay_from_manifest(
    manifest_path=result_v1.manifest_path,
    observables=new_observables
)

# Noise correction automatically applied during replay!
print(f"Confusion matrix loaded from: {result_v1.mitigation_confusion_matrix_path}")
```

**Note:** The confusion matrix file must still exist at the path recorded in the manifest. If files have been moved, replay will fail with a `FileNotFoundError`.

---

## Advanced: Programmatic Replay Loop

Batch-process multiple manifests to compare different observables:

```python
from pathlib import Path
from quartumse import ShadowEstimator
from quartumse.shadows.core import Observable

# Define observable set to test across all experiments
test_observables = [
    Observable("XXX"),
    Observable("YYY"),
    Observable("ZZZ"),
]

estimator = ShadowEstimator(backend="aer_simulator")
results_table = []

# Replay all manifests in directory
manifest_dir = Path("data/manifests")
for manifest_path in sorted(manifest_dir.glob("*.json")):
    try:
        replayed = estimator.replay_from_manifest(
            manifest_path=str(manifest_path),
            observables=test_observables
        )

        # Extract experiment metadata
        import json
        with open(manifest_path) as f:
            manifest = json.load(f)

        exp_id = manifest['experiment_id']
        backend = manifest['backend']['backend_name']
        shadow_size = manifest['shadows']['shadow_size']

        # Store results
        for obs_str, data in replayed.observables.items():
            results_table.append({
                'experiment_id': exp_id,
                'backend': backend,
                'shadow_size': shadow_size,
                'observable': obs_str,
                'expectation': data['expectation_value'],
                'ci_width': data['ci_width'],
            })

        print(f"✓ Replayed: {manifest_path.name}")

    except Exception as e:
        print(f"✗ Failed: {manifest_path.name} - {e}")

# Convert to DataFrame for analysis
import pandas as pd
df = pd.DataFrame(results_table)
print("\nReplayed Results Summary:")
print(df.groupby(['observable', 'backend'])['expectation'].agg(['mean', 'std', 'count']))
```

---

## Replay Validation

Verify that replay produces identical results to original run:

```python
# Original run
result_original = estimator.estimate(circuit, observables=original_obs, save_manifest=True)

# Replay with SAME observables
result_replay = estimator.replay_from_manifest(
    manifest_path=result_original.manifest_path,
    observables=original_obs  # Same as original
)

# Compare
print("\nReplay Validation:")
print(f"{'Observable':<15} {'Original':<12} {'Replayed':<12} {'Match'}")
print("-" * 55)

for obs_str in result_original.observables.keys():
    orig_val = result_original.observables[obs_str]['expectation_value']
    replay_val = result_replay.observables[obs_str]['expectation_value']
    match = "✓" if abs(orig_val - replay_val) < 1e-10 else "✗"

    print(f"{obs_str:<15} {orig_val:>11.6f} {replay_val:>11.6f} {match:>7}")
```

**Expected output:**
```
Replay Validation:
Observable      Original    Replayed    Match
-------------------------------------------------------
1.0*ZII           0.003906    0.003906      ✓
1.0*ZZI           0.996094    0.996094      ✓
1.0*ZZZ          -0.007812   -0.007812      ✓
```

---

## Troubleshooting

**"Manifest file not found"**
- Check path is correct (absolute or relative to current directory)
- Verify manifest was saved during original run (`save_manifest=True`)
- Use `Path(manifest_path).resolve()` to see absolute path

**"Shot data file not found"**
- Manifest contains path to Parquet file with measurement outcomes
- Ensure shot data file hasn't been deleted or moved
- Check `manifest['shot_data_path']` for expected location

**"Confusion matrix file not found"**
- For v1 noise-aware shadows with MEM
- Check `manifest['mitigation']['confusion_matrix_path']`
- Ensure MEM calibration file still exists at recorded path
- Re-run MEM calibration if needed (see [MEM v1 Guide](run-mem-v1.md))

**"Different results between original and replay"**
- Should be bit-identical if observables are the same
- Check random seed is recorded in manifest
- Verify no floating-point precision issues (compare within tolerance)

**"Replay slower than expected"**
- Replay should complete in <1 second for typical shadow sizes
- Check Parquet file isn't corrupted (try loading with pandas)
- Verify no network I/O (all files should be local)

---

## Related

- [Run S-T01 GHZ](run-st01-ghz.md) - Generate manifests worth replaying
- [Generate Report](generate-report.md) - Create HTML reports from replayed results
- [Manifest Schema](../explanation/manifest-schema.md) - Full manifest specification
