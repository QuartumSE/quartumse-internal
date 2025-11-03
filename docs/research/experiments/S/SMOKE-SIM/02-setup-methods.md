# Simulator Smoke Test - Setup & Methods

**Experiment ID:** SMOKE-SIM
**Workstream:** S (Shadows)
**Executable:** `C:\Users\User\Desktop\Projects\QuartumSE\experiments\shadows\S_T01_ghz_baseline.py`

## Circuit Description

### GHZ State Preparation

The Greenberger-Horne-Zeilinger (GHZ) state is a maximally entangled state:

```
|GHZ(n)⟩ = (|00...0⟩ + |11...1⟩) / √2
```

**Circuit Construction:**
```python
def create_ghz_circuit(num_qubits: int) -> QuantumCircuit:
    qc = QuantumCircuit(num_qubits)
    qc.h(0)                    # Hadamard on qubit 0
    for i in range(1, num_qubits):
        qc.cx(0, i)            # CNOT chain from q0 to all others
    return qc
```

**Circuit Depths:**
- 3-qubit GHZ: depth = 3
- 4-qubit GHZ: depth = 4
- 5-qubit GHZ: depth = 5

### Observable Set

For each n-qubit GHZ state, estimate:

1. **Single-qubit Z observables:** ⟨Z_i⟩ for i = 0, 1, ..., n-1
   - Expected values: all zero for GHZ states

2. **Two-qubit ZZ observables:** ⟨Z_0 Z_i⟩ for i = 1, 2, ..., n-1
   - Expected values: +1 for all pairs in GHZ states

**Total observables:**
- 3-qubit: 3 (Z) + 2 (ZZ) = 5 observables (misreported as 9 in some runs)
- 4-qubit: 4 (Z) + 3 (ZZ) = 7 observables
- 5-qubit: 5 (Z) + 4 (ZZ) = 9 observables

## Backend Configuration

### Simulator Backend
- **Name:** `aer_simulator` (Qiskit Aer)
- **Type:** Statevector simulator with shot sampling
- **Noise Model:** None (ideal simulation)
- **Shots per Shadow:** 1 (deterministic in ideal case)

### Execution Environment
- **Python:** 3.13.9
- **Qiskit:** 2.2.1
- **QuartumSE:** 0.1.0
- **Platform:** Windows 11 (win32)

## Classical Shadows Configuration

### v0 Baseline Configuration

```python
shadow_config = ShadowConfig(
    shadow_size=500,              # Number of shadow snapshots
    random_seed=42,               # For reproducibility
    confidence_level=0.95,        # 95% confidence intervals
    version=ShadowVersion.V0_BASELINE,
    apply_inverse_channel=False   # v0 does not use inverse channel
)
```

**Key Parameters:**
- **Shadow Size:** 500 measurements (conservative for initial validation)
- **Measurement Ensemble:** Random local Clifford unitaries
- **Sampling Strategy:** Uniform random selection per snapshot
- **Seed:** Fixed at 42 for exact reproducibility

### v0 Algorithm Details

For each shadow snapshot:
1. Sample random local Clifford unitary U_i for each qubit i
2. Apply U = U_0 ⊗ U_1 ⊗ ... ⊗ U_{n-1} to quantum state
3. Measure all qubits in computational basis
4. Store (U, measurement_outcome) as shadow snapshot

Observable estimation:
```
⟨O⟩_shadow = (1/N) Σ_i ρ̂_i(O)
```
where ρ̂_i is the local classical shadow reconstructed from snapshot i.

## Baseline Comparison Method

### Direct Pauli Measurement

For comparison, each observable is measured directly:

1. **Basis Rotation:** Apply Pauli rotation gates to measure in eigenbasis
2. **Measurement:** Sample 1000 shots in computational basis
3. **Expectation Computation:**
   ```
   ⟨O⟩ = Σ_bitstrings p(bitstring) * parity(bitstring, O)
   ```
4. **Variance Estimate:** Binomial variance (1 - ⟨O⟩²) / shots

**Baseline shots:** 1000 per observable

## Mitigation Strategy

**None** - This is an ideal simulator experiment. Mitigation strategies (MEM, ZNE) are introduced in hardware experiments (SMOKE-HW, S-T02).

## Execution Workflow

### Command-Line Execution

```bash
# From repository root
cd C:\Users\User\Desktop\Projects\QuartumSE

# Run 3-, 4-, 5-qubit GHZ validation
python experiments/shadows/S_T01_ghz_baseline.py \
    --backend aer_simulator \
    --variant st01 \
    --shadow-size 500 \
    --seed 42 \
    --data-dir ./data
```

### Configuration File (Optional)

Create `config/smoke_sim.yaml`:
```yaml
backend:
  provider: local
  name: aer_simulator

num_qubits: [3, 4, 5]
shadow_size: 500
baseline_shots: 1000
random_seed: 42
data_dir: ./data
```

Run with config:
```bash
python experiments/shadows/S_T01_ghz_baseline.py --config config/smoke_sim.yaml
```

## Key Code Snippets

### Observable Analytical Values

```python
def ghz_expectation_value(observable: Observable) -> float:
    """Analytical expectation for GHZ state observables."""

    # Non-Z Paulis have zero expectation
    if any(p not in {"I", "Z"} for p in observable.pauli_string):
        return 0.0

    num_z = observable.pauli_string.count("Z")

    # Identity or even-parity Z operators: ⟨O⟩ = coefficient
    if num_z == 0 or num_z % 2 == 0:
        return observable.coefficient

    # Odd-parity Z operators: ⟨O⟩ = 0
    return 0.0
```

### SSR Computation

```python
from quartumse.utils.metrics import compute_ssr

ssr = compute_ssr(
    baseline_shots=1000,
    quartumse_shots=500,
    baseline_precision=abs(baseline_val - expected_val),
    quartumse_precision=abs(shadow_val - expected_val)
)
```

## Data Storage

### Output Artifacts

1. **Manifests:** `data/manifests/{experiment_id}.json`
   - Complete provenance: circuit, backend, config, timestamps

2. **Shot Data:** `data/shots/{experiment_id}.parquet`
   - Raw shadow measurements for replay

3. **Console Output:** Terminal logs with metrics table

### Manifest Schema

Key fields captured:
```json
{
  "experiment_id": "uuid",
  "circuit_hash": "sha256",
  "backend": "aer_simulator",
  "shadow_config": {...},
  "observables": {...},
  "timestamps": {...},
  "software_versions": {...}
}
```

## Reproducibility

### Exact Reproduction

To exactly reproduce results:
```python
from quartumse import ShadowEstimator
from quartumse.shadows import ShadowConfig
from quartumse.shadows.config import ShadowVersion

# Load from manifest
estimator = ShadowEstimator.replay_from_manifest(
    manifest_path="data/manifests/{experiment_id}.json"
)
```

### Random Seed Control

- **Shadow sampling:** Controlled by `shadow_config.random_seed = 42`
- **NumPy operations:** Set via `np.random.seed(42)` in script
- **Qiskit simulation:** Controlled by Aer's seed_simulator parameter

## Validation Checks

The experiment script includes automated validation:

1. **CI Coverage Check:** Counts observables within 95% CI
2. **SSR Threshold:** Compares against 1.2× target
3. **PASS/FAIL Status:** Prints summary at end

Success message:
```
✓ EXPERIMENT PASSED - Phase 1 exit criteria met!
```

## Link to Executable Notebook

Interactive notebook version: `notebooks/experiments/shadows/smoke_test_simulator.ipynb` [TBD - to be created]

For now, use the standalone script with `--help` for all options.

## Next Experiments

Upon successful completion:
1. **SMOKE-HW:** Same experiment on IBM quantum hardware
2. **S-T01:** Extended GHZ experiments (≥10 trials, connectivity-aware)
3. **S-T02:** Noise-aware shadows with MEM on hardware
