# S-T01: Extended GHZ Validation - Setup & Methods

**Experiment ID:** S-T01
**Status:** [PLANNED]
**Executable:** `C:\Users\User\Desktop\Projects\QuartumSE\experiments\shadows\S_T01_ghz_baseline.py`

## Circuit Description

### Connectivity-Aware GHZ (4-5 Qubits)

**4-Qubit GHZ** (Primary Target):
```
Target Qubits: Select based on ibm_fez topology (linear or star)
Depth: 4 (1H + 3CX)
Observables: 7 (4×Z + 3×ZZ)
```

**5-Qubit GHZ** (Stretch Goal):
```
Target Qubits: Select 5 connected qubits with best T1/T2/readout
Depth: 5 (1H + 4CX)
Observables: 9 (5×Z + 4×ZZ)
```

## Backend Configuration

- **Primary:** ibm:ibm_fez (156q, typical queue < 200)
- **Backup:** ibm:ibm_marrakesh (156q)
- **Calibration:** Refresh if > 12 hours old

## Classical Shadows Configuration

### v0 Baseline (No Mitigation)

```python
shadow_config = ShadowConfig(
    shadow_size=500,              # 5× SMOKE-HW budget
    random_seed=[42, 123, 456, ...],  # Different per trial
    confidence_level=0.95,
    version=ShadowVersion.V0_BASELINE,
    apply_inverse_channel=False
)
```

**Trial Structure:**
- **Trials:** ≥10 independent runs
- **Seeds:** Unique per trial (42, 123, 456, 789, 1011, 1213, 1415, 1617, 1819, 2021)
- **Shadow Size:** 500 per trial

## Baseline Comparison

**Direct Measurement:**
- 1000 shots per observable (7-9 observables)
- Run once alongside S-T01 trials
- Use for SSR calculation: SSR = (baseline_shots × baseline_error) / (shadow_shots × shadow_error)

## Execution Workflow

```bash
# Execute ≥10 trials with different seeds
for seed in 42 123 456 789 1011 1213 1415 1617 1819 2021; do
  python experiments/shadows/S_T01_ghz_baseline.py \
    --backend ibm:ibm_fez \
    --variant st01 \
    --shadow-size 500 \
    --seed $seed \
    --data-dir ./data
done

# Aggregate results
python experiments/shadows/analyze_ghz_trials.py \
  --experiment-id s-t01 \
  --trials 10
```

## Data Storage

- **Manifests:** `data/manifests/s-t01-trial-{01-10}-{experiment_id}.json`
- **Shot Data:** `data/shots/s-t01-trial-{01-10}-{experiment_id}.parquet`
- **Aggregated Results:** `results/s-t01-summary.json`

## Validation Checks

1. **SSR per Trial:** Compute for each trial independently
2. **SSR Aggregate:** Mean ± std across all trials
3. **CI Coverage:** Fraction of observables within 95% CI
4. **Pass/Fail:** SSR_mean ≥ 1.1× AND CI_coverage ≥ 80%

## Expected Results

**4-Qubit GHZ:**
- SSR (per trial): 1.1-1.5×
- SSR (mean ± std): 1.3 ± 0.2×
- CI Coverage: 80-90%

**5-Qubit GHZ:**
- SSR (per trial): 1.0-1.3×
- SSR (mean ± std): 1.15 ± 0.25×
- CI Coverage: 75-85%

## Link to Analysis Notebook

`notebooks/experiments/shadows/s-t01-analysis.ipynb` [TBD]

## Next Experiments

- **S-T02:** v1 noise-aware with MEM (uses S-T01 as baseline)
- **S-BELL:** Parallel Bell pairs (uses S-T01 methodology)
