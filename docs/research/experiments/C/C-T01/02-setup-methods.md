# C-T01: H₂ Chemistry Experiment - Setup & Methods

**Experiment ID:** C-T01 / S-CHEM
**Manifest ID:** `2a89df46-3c81-4638-9ff4-2f60ecf3325d`
**Executable:** `C:\Users\User\Desktop\Projects\QuartumSE\experiments\shadows\h2_energy\run_h2_energy.py`

## Circuit Description

### H₂ Molecular Ansatz (4 Qubits)

**Molecular Parameters:**
- **Molecule:** H₂ (hydrogen dimer)
- **Geometry:** R = 0.74 Å (equilibrium bond length)
- **Basis Set:** STO-3G (minimal basis)
- **Active Space:** 2 orbitals × 2 spins = 4 qubits

**Ansatz Circuit:**
```
Circuit Depth: 5
Gates:
  - Hadamard (h): 1
  - CNOT (cx): 3
  - RY rotations: 3
  - RZ rotations: 3

Circuit Hash: 4d5f8436e8e437af
```

**State Preparation:**
Hardware-efficient ansatz (not chemically-inspired):
1. Initial state: |0000⟩
2. Apply Hadamard and rotation layers
3. Entangle with CNOT ladder
4. Final rotations for variational parameters

[NOTE: Circuit parameters not optimized in this run, using placeholder values]

### Hamiltonian Observable Set

**H₂ Hamiltonian (12 Pauli Terms):**

| Observable | Coefficient | Physical Meaning |
|------------|-------------|------------------|
| IIII | -1.05 | Nuclear repulsion + constant |
| ZIII | 0.39 | Orbital 0 occupation |
| IZII | -0.39 | Orbital 1 occupation |
| ZZII | -0.01 | Orbital 0-1 correlation |
| IIZI | 0.39 | Orbital 2 occupation |
| IIIZ | -0.39 | Orbital 3 occupation |
| IIZZ | -0.01 | Orbital 2-3 correlation |
| ZIZI | 0.03 | Cross-orbital correlation |
| IZIZ | 0.03 | Cross-orbital correlation |
| XXXX | 0.06 | Hopping term (4-body) |
| YYXX | -0.02 | Hopping term (4-body) |
| XXYY | -0.02 | Hopping term (4-body) |

[NOTE: These are placeholder coefficients for demonstration. Real H₂@STO-3G coefficients should be loaded from qiskit-nature.]

**Total Energy:**
```
E = Σ coefficient_i × ⟨Pauli_i⟩
```

## Backend Configuration

### IBM Quantum Hardware: ibm_fez

**Device Specifications:**
- **Processor:** 156-qubit superconducting transmon
- **Topology:** Heavy-hex lattice
- **Qubits Used:** 0, 1, 2, 3 (linear connectivity)
- **Calibration:** 2025-11-03T13:17:32Z (< 1 hour before experiment)

**Qubit Quality (Used Qubits):**
| Qubit | T1 (μs) | T2 (μs) | Readout Error | Gate Error (SX) |
|-------|---------|---------|---------------|-----------------|
| 0 | 63.6 | 49.7 | 0.98% | 0.0364% |
| 1 | 174.8 | 199.1 | 2.22% | 0.0364% |
| 2 | 208.9 | 178.7 | 0.77% | 0.0364% |
| 3 | 126.5 | 143.8 | 2.10% | 0.0364% |

**Two-Qubit Gates:**
- Average CZ Error: 1.083%
- Circuit depth 5 → Total gate error budget: ~3-5%

**Assessment:** Excellent qubit quality for 4-qubit chemistry experiment.

## Classical Shadows Configuration

### v1 Noise-Aware Configuration

```python
shadow_config = ShadowConfig(
    shadow_size=300,                          # Conservative for 12 observables
    random_seed=77,                           # Reproducibility
    confidence_level=0.95,                    # 95% CIs
    version=ShadowVersion.V1_NOISE_AWARE,    # Use inverse channel
    apply_inverse_channel=True               # Noise correction enabled
)
```

**Key Parameters:**
- **Shadow Size:** 300 snapshots (25 shots/observable average)
- **Version:** v1 (noise-aware with inverse channel correction)
- **Bootstrap Samples:** 1000 (for CI estimation)
- **Random Seed:** 77 (different from SMOKE-SIM/HW for independence)

### Theoretical Shot Budget

**Naive Approach (Direct Measurement):**
- 12 terms × 100 shots/term = 1,200 shots minimum

**Grouped Pauli Measurement:**
- Typical grouping: 3-5 groups for H₂ Hamiltonian
- 3 groups × 400 shots/group = 1,200 shots

**Classical Shadows (This Experiment):**
- 300 shadows estimate ALL 12 terms
- **Expected SSR:** 1,200 / 300 = 4×

## Mitigation Strategy

### Measurement Error Mitigation (MEM)

**Calibration:**
- **Technique:** Confusion matrix measurement
- **Shots per State:** 128 shots × 2^4 = 2,048 total calibration shots
- **Qubits Calibrated:** [0, 1, 2, 3]
- **Confusion Matrix Path:** `data/mem/2a89df46-3c81-4638-9ff4-2f60ecf3325d.npz`
- **Checksum:** `69dced449ce1479211404c31e77abafa...`

**Procedure:**
1. Prepare computational basis state |b⟩ for b ∈ {0, 1}^4
2. Measure 128 times without rotation
3. Construct 16×16 confusion matrix C[measured|prepared]
4. Invert matrix: C^{-1} corrects readout errors

**Expected Improvement:**
- Readout errors: 0.77-2.22% per qubit
- Uncorrelated assumption → ~5-10% total bitstring error
- MEM expected to reduce readout variance by 20-30%

### v1 Inverse Channel

**Noise Model:**
Locally-biased inverse channel accounts for:
- Single-qubit depolarizing noise
- Readout errors (already corrected by MEM)
- Approximate gate errors via effective noise parameter

**Application:**
Each shadow snapshot ρ̂_i corrected:
```
ρ̂_corrected = Λ^{-1}(ρ̂_measured)
```
where Λ is learned noise channel.

[NOTE: In this run, inverse channel parameters derived from backend calibration data.]

## Execution Workflow

### Step 1: Backend Validation

```bash
quartumse runtime-status --backend ibm:ibm_fez
```

Confirm:
- Queue depth < 200 jobs
- Calibration < 24 hours old
- Target qubits (0-3) have readout error < 3%

### Step 2: MEM Calibration

```bash
# Automatic in run_h2_energy.py
# Generates confusion matrix for qubits 0-3
# Saves to data/mem/{experiment_id}.npz
```

### Step 3: Shadow Measurement

```bash
cd C:\Users\User\Desktop\Projects\QuartumSE

python experiments/shadows/h2_energy/run_h2_energy.py \
    --backend ibm:ibm_fez \
    --shadow-size 300 \
    --seed 77 \
    --data-dir ./data
```

**Execution Flow:**
1. Transpile H₂ ansatz circuit for ibm_fez topology
2. Submit MEM calibration job (2,048 shots)
3. Submit shadow measurement job (300 shots)
4. Retrieve results and apply MEM correction
5. Estimate all 12 Hamiltonian terms with bootstrap CIs
6. Save manifest + shot data

### Step 4: Post-Processing

Automatic:
- Observable expectation values computed
- 95% confidence intervals via bootstrap (1000 samples)
- Total energy = Σ coefficient_i × ⟨Pauli_i⟩
- Manifest saved with full provenance

## Key Code Snippets

### Hamiltonian Definition

```python
from quartumse.shadows.core import Observable

hamiltonian_terms = [
    Observable("IIII", coefficient=-1.05),
    Observable("ZIII", coefficient=0.39),
    Observable("IZII", coefficient=-0.39),
    Observable("ZZII", coefficient=-0.01),
    Observable("IIZI", coefficient=0.39),
    Observable("IIIZ", coefficient=-0.39),
    Observable("IIZZ", coefficient=-0.01),
    Observable("ZIZI", coefficient=0.03),
    Observable("IZIZ", coefficient=0.03),
    Observable("XXXX", coefficient=0.06),
    Observable("YYXX", coefficient=-0.02),
    Observable("XXYY", coefficient=-0.02),
]
```

### Shadow Estimation with MEM

```python
from quartumse import ShadowEstimator
from quartumse.reporting.manifest import MitigationConfig

mitigation_config = MitigationConfig(
    techniques=["MEM"],
    parameters={"mem_shots": 128}
)

estimator = ShadowEstimator(
    backend="ibm:ibm_fez",
    shadow_config=shadow_config,
    mitigation_config=mitigation_config,
    data_dir="./data"
)

result = estimator.estimate(
    circuit=h2_ansatz,
    observables=hamiltonian_terms,
    save_manifest=True
)

total_energy = sum(
    term.coefficient * result.observables[str(term)]["expectation_value"]
    for term in hamiltonian_terms
)
```

### Replay from Manifest

```python
# Estimate NEW observables without re-running on hardware
estimator = ShadowEstimator.replay_from_manifest(
    "data/manifests/2a89df46-3c81-4638-9ff4-2f60ecf3325d.json"
)

new_observables = [
    Observable("ZZZZ"),  # All-Z correlation
    Observable("XXII"),  # X-X hopping
]

new_result = estimator.estimate_from_replay(new_observables)
```

## Data Storage

### Artifacts Generated

1. **Manifest:** `data/manifests/2a89df46-3c81-4638-9ff4-2f60ecf3325d.json`
   - 2,136 lines of JSON
   - Complete circuit QASM3 representation
   - All 12 observable estimates with CIs
   - Backend calibration snapshot
   - Software versions (Qiskit 2.2.1, QuartumSE 0.1.0)

2. **Shot Data:** `data/shots/2a89df46-3c81-4638-9ff4-2f60ecf3325d.parquet`
   - 300 shadow measurement outcomes
   - Basis choices (random Clifford per qubit)
   - Raw bitstrings before MEM correction

3. **Confusion Matrix:** `data/mem/2a89df46-3c81-4638-9ff4-2f60ecf3325d.npz`
   - 16×16 matrix for 4-qubit system
   - Calibration metadata (shots, timestamp)

## Validation Checks

Automated in script:
1. ✓ All 12 observables estimated
2. ✓ Confidence intervals non-degenerate
3. ✓ Identity term (IIII) ≈ coefficient (constant check)
4. ✓ Manifest saved with all required fields
5. ✓ Total energy within physical bounds

## Reproducibility

**Full Reproduction:**
```python
from quartumse import ShadowEstimator

# Exact replication using manifest + shot data
result = ShadowEstimator.replay_from_manifest(
    "data/manifests/2a89df46-3c81-4638-9ff4-2f60ecf3325d.json"
)

# Results identical to original run (deterministic replay)
```

**Random Seed Control:**
- Shadow sampling: seed=77
- Bootstrap: seed=77 + offset
- NumPy RNG: seeded in estimator

## Link to Executable Notebook

Interactive notebook: `notebooks/experiments/chemistry/h2_energy_shadows.ipynb` [TBD]

For now, use standalone script with `--help` for options.

## Next Experiments

1. **C-T01 Re-Run with Real Hamiltonian:** Update coefficients from qiskit-nature
2. **C-T01 Baseline:** Run grouped Pauli measurement for SSR validation
3. **C-T02 (LiH):** Scale to 6-qubit molecule
4. **S-T03 (Fermionic Shadows):** Direct 2-RDM estimation
