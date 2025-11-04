# O-T01: QAOA MAX-CUT with Shot-Frugal Cost Estimation - Setup & Methods

**Experiment ID:** O-T01
**Status:** [PLANNED]
**Executable:** `C:\Users\User\Desktop\Projects\QuartumSE\experiments\optimization\O_T01_qaoa_maxcut.py` [TBD]

## Problem Definition

### MAX-CUT on 5-Node Ring Graph

**Graph Topology:**
```
       0
      / \
     1---4
     |   |
     2---3
```

**Graph Representation:**
- Nodes: 0, 1, 2, 3, 4
- Edges: (0,1), (1,2), (2,3), (3,4), (4,0) [Ring topology]
- Total edges: 5 (MAX-CUT goal: partition into two sets with maximum edge cut count)
- Optimal classical solution: 4 edges (one partition: {0,2}, {1,3,4})
- Classical approximation ratio achievable: 0.878 (Goemans-Williamson)
- Phase 1 target: 0.90+ (realistic with QAOA p=1-2)

### MAX-CUT Cost Hamiltonian

For ring graph, MAX-CUT cost Hamiltonian:

```
H_C = (1/2) * sum_{(i,j) in E} (I - Z_i*Z_j)
```

For 5-node ring:
```
H_C = (1/2) * [(I - Z_0*Z_1) + (I - Z_1*Z_2) + (I - Z_2*Z_3) + (I - Z_3*Z_4) + (I - Z_4*Z_0)]
    = (5/2)*I - (1/2)*(Z_0*Z_1 + Z_1*Z_2 + Z_2*Z_3 + Z_3*Z_4 + Z_4*Z_0)
```

**Key observable:** Cost function value ∝ count of edges in maximum cut
- Minimum energy state: Maximum cut (5 edges)
- Maximum energy state: Minimum cut (0 edges)

## Circuit Description

### QAOA Ansatz (p=1 and p=2 variants)

**General QAOA Circuit (depth = 2p):**
```
Initialize:  |+⟩⊗5 (all qubits in +X eigenstate)

For layer k = 1 to p:
  - Cost layer: Apply e^{-i * γ_k * H_C}
    → Approximated with trotterized gates (exp(-i * γ_k * ZZ terms))
  - Mixer layer: Apply e^{-i * β_k * H_M}
    → Approximated with X rotations (RX(2*β_k) on each qubit)

Measure: All qubits in computational (Z) basis
Estimate: Cost function <H_C> from measurement outcomes
```

### Implementation Details

**p=1 Variant (Minimal):**
```
Qubits: 5 (connectivity: linear chain OK, but ring preferred)
Circuit Depth: 6 (1 H + 5 CX per layer) × 1 layer + 1 H + 5 RX = ~20 gates
Cost layer: Trotterized exp(-i * γ * ZZ_ij) using CX + RZ gates
  - Each ZZ term: 3 gates (CX - RZ(2*γ_ij) - CX)
  - 5 ZZ terms × 3 gates = 15 gates per layer
Mixer layer: RX(2*β) on each qubit = 5 gates
Parameter count: 2 (γ, β)
Optimizer: COBYLA or SLSQP (scipy.optimize)
```

**p=2 Variant (Moderate):**
```
Qubits: 5
Circuit Depth: 12 (double the p=1 depth)
Cost layer 1: 15 gates
Mixer layer 1: 5 gates
Cost layer 2: 15 gates
Mixer layer 2: 5 gates
Parameter count: 4 (γ_1, β_1, γ_2, β_2)
Optimizer: COBYLA or SLSQP
```

## Backend Configuration

- **Primary:** ibm:ibm_fez (156q, typical queue < 200)
- **Backup:** ibm:ibm_marrakesh (156q)
- **Calibration:** Refresh if > 12 hours old
- **Qubit Selection:** Choose 5 connected qubits with best T1/T2/readout metrics
  - Preferred: Qubits 0-4 (linear chain) or topology-optimal selection per calibration

## Classical Shadows Configuration

### Shadow-Based Cost Function Estimation

```python
shadow_config = ShadowConfig(
    shadow_size=300,              # Shots per optimizer iteration
    confidence_level=0.95,
    version=ShadowVersion.V0_BASELINE,  # Or V1_NOISE_AWARE after S-T02 validation
    apply_inverse_channel=False,   # Set True if using v1 + MEM
    observables=['Z0Z1', 'Z1Z2', 'Z2Z3', 'Z3Z4', 'Z4Z0']  # Ring edges
)
```

**Cost Function Computation:**
```python
def evaluate_cost(params, shadow_estimator, graph):
    """
    Evaluate cost function using shadow estimation.

    Args:
        params: QAOA parameters (γ, β) or (γ_1, β_1, γ_2, β_2)
        shadow_estimator: ShadowEstimator configured with shadows v0/v1
        graph: Ring graph (5 nodes, 5 edges)

    Returns:
        cost_value: Estimated <H_C> from shadow measurements
    """
    # Build QAOA circuit with current parameters
    qc = build_qaoa_circuit(graph, params, p=len(params)//2)

    # Execute on backend/simulator, collect shadows
    job = shadow_estimator.estimate(qc, observables)

    # Extract ZZ terms and compute cost
    cost = 0
    for (i,j) in graph.edges:
        zz_expectation = job.results[f'Z{i}Z{j}'].mean
        cost += (1 - zz_expectation) / 2  # Cost = (I - ZZ)/2

    return cost
```

## Execution Workflow

### Single Trial Structure

```bash
# Execute O-T01 trial (seed = 42, p = 1)
python experiments/optimization/O_T01_qaoa_maxcut.py \
  --backend ibm:ibm_fez \
  --graph ring-5 \
  --ansatz-depth 1 \
  --shadow-size 300 \
  --optimizer cobyla \
  --max-iterations 60 \
  --seed 42 \
  --shadow-version v0 \
  --data-dir ./data

# Outputs:
# - Manifest: data/manifests/o-t01-trial-01-{uuid}.json
# - Convergence log: data/logs/o-t01-trial-01-convergence.json
# - Final state: data/results/o-t01-trial-01-final-state.json
```

### Multiple Trial Execution

```bash
# Execute ≥3 trials with different random seeds
for seed in 42 123 456; do
  python experiments/optimization/O_T01_qaoa_maxcut.py \
    --backend ibm:ibm_fez \
    --graph ring-5 \
    --ansatz-depth 1 \
    --shadow-size 300 \
    --optimizer cobyla \
    --max-iterations 60 \
    --seed $seed \
    --shadow-version v0 \
    --data-dir ./data
done

# Aggregate results
python experiments/optimization/analyze_qaoa_convergence.py \
  --experiment-id o-t01 \
  --trials 3 \
  --output results/o-t01-summary.json
```

## Baseline Comparison: Standard QAOA

**Standard QAOA (no shadows) baseline:**
- **Shots per iteration:** 1000 (direct measurement of all 5 ZZ observables)
- **Measurement strategy:** Measure all observables in same computational basis, repeat 1000 times
- **Expected iterations to convergence:** 50-80
- **Total shots (baseline):** 50,000-80,000

**Shadow-Based QAOA (O-T01):**
- **Shots per iteration:** 300 (classical shadows multi-observable estimation)
- **Expected iterations to convergence:** 40-60 (better estimates → faster convergence)
- **Total shots (shadow):** 12,000-18,000
- **Expected reduction:** (12,000-18,000) / (50,000-80,000) = 15-36% shot reduction

**Phase 1 Success Criterion:**
- ≥20% reduction in optimizer steps (iterations or total shots)

## Data Storage and Provenance

### Manifest Schema (Provenance Tracking)

```json
{
  "experiment_id": "o-t01",
  "trial_id": 1,
  "timestamp": "2025-11-15T14:32:00Z",
  "backend": "ibm:ibm_fez",
  "qubits": [0, 1, 2, 3, 4],
  "circuit": {
    "name": "qaoa_maxcut_ring5_p1",
    "depth": 20,
    "gate_count": 40,
    "n_params": 2
  },
  "problem": {
    "graph_type": "ring",
    "n_nodes": 5,
    "n_edges": 5,
    "observables": ["Z0Z1", "Z1Z2", "Z2Z3", "Z3Z4", "Z4Z0"]
  },
  "shadow_config": {
    "shadow_size": 300,
    "version": "v0_baseline",
    "confidence_level": 0.95
  },
  "optimization": {
    "optimizer": "COBYLA",
    "max_iterations": 60,
    "seed": 42,
    "convergence_achieved": true,
    "iterations_to_convergence": 45
  },
  "results": {
    "final_cost": -2.34,
    "approximation_ratio": 0.91,
    "optimal_classical": 2.5,
    "total_shots": 13500
  },
  "calibration": {
    "confusion_matrix_hash": "sha256:abc123...",
    "backend_calibration_time": "2025-11-15T12:00:00Z"
  }
}
```

### Data Files Location

- **Manifests:** `data/manifests/o-t01-trial-{01-03}-{uuid}.json`
- **Convergence Logs:** `data/logs/o-t01-trial-{01-03}-convergence.json` (per-iteration cost values)
- **Final Results:** `data/results/o-t01-trial-{01-03}-final-solution.json` (optimal params, cost, approx ratio)
- **Aggregated Summary:** `results/o-t01-summary.json` (cross-trial statistics)

## Validation Checks

### During Optimization

1. **Shadow Quality Check (per iteration):**
   - Confidence interval width for cost estimate < target threshold (e.g., 0.1)
   - If CI too wide, suggest increasing shadow_size for next iteration

2. **Convergence Monitoring:**
   - Track cost value per iteration
   - Detect if cost plateaus (converged) or oscillates (tuning needed)
   - Log iteration count to convergence

3. **Parameter Bounds:**
   - γ ∈ [0, π] (cost layer rotation angle)
   - β ∈ [0, π] (mixer layer rotation angle)
   - Warn if optimizer proposes params outside bounds

### After Optimization Completes

1. **Solution Quality Assessment:**
   - Compute approximation ratio: (Final Cost) / (Optimal Classical Cost)
   - Pass if approx_ratio ≥ 0.90
   - Fail if approx_ratio < 0.85 (may indicate optimization issue)

2. **Convergence Metric:**
   - Number of iterations to achieve 95% of final cost value
   - Compare shadow-based vs. standard QAOA baseline
   - Target: ≥20% fewer iterations

3. **Manifest Validation:**
   - Verify all required fields present (circuit, backend, shadow_config, observables, results)
   - Check checksums (circuit SHA-256, confusion matrix SHA-256)
   - Confirm timestamps consistent

## Expected Results

### p=1 Variant

**Per-Trial Expected Results:**
- **Final Cost:** -2.2 to -2.5 (depends on ring orientation, classical optimal = -2.5)
- **Approximation Ratio:** 0.88-0.92
- **Iterations to Convergence:** 40-60
- **Total Shots:** 12,000-18,000
- **Shadow CI Width:** ±0.15 per observable (acceptable for optimization)

**Aggregate (≥3 trials):**
- **Approx Ratio Mean ± Std:** 0.90 ± 0.02
- **Step Reduction Mean ± Std:** 25% ± 5% vs. baseline
- **Consistency:** All trials achieve approx_ratio ≥ 0.88 (no outliers)

### p=2 Variant (if time permits)

**Expected Improvements:**
- **Final Cost:** -2.3 to -2.55 (slightly better than p=1)
- **Approximation Ratio:** 0.90-0.94
- **Iterations to Convergence:** 50-80 (more params to tune)
- **Total Shots:** 15,000-24,000 (more iterations, but still <baseline 50,000+)

## Link to Analysis Notebook

`notebooks/experiments/optimization/o-t01-analysis.ipynb` [TBD]

## Comparison to Phase 1 Baseline (Standard QAOA)

| Metric | Standard QAOA | Shadow-Based (O-T01) | Target |
|--------|---------------|----------------------|--------|
| **Shots per iteration** | 1000 | 300 | ↓ |
| **Iterations to convergence** | 60-80 | 40-60 | ↓ |
| **Total shots** | 60,000-80,000 | 12,000-18,000 | <20,000 |
| **Approximation ratio (p=1)** | 0.91-0.94 | 0.88-0.92 | ≥0.90 |
| **Step reduction** | Baseline | ≥20% | ✓ |

## Next Experiments

- **O-T02:** QAOA on larger graph (7-8 nodes, p=2-3, forest/grid topology)
- **O-T03:** Shadow-VQE integration (chemistry Hamiltonian optimization)
- **Phase 2:** Adaptive shadow allocation (VACS) for optimization

---

**Document Version:** 1.0
**Status:** [PLANNED]
**Executable Path:** Pending implementation
**Next Review:** Upon O-T01 setup completion
