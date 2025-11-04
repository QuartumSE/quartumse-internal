# O-T01: QAOA MAX-CUT with Shot-Frugal Cost Estimation - Results & Analysis

**Experiment ID:** O-T01
**Status:** [PLANNED - Template for Future Results]

## Execution Summary [TBD]

[To be populated after experiment execution]

**Configuration:**
- Backend: [TBD - ibm_fez or ibm_marrakesh]
- Trials Completed: [TBD - target ≥3]
- Ansatz Depth (p): [TBD - p=1 and/or p=2]
- Shadow Size per Iteration: 300
- Graph: 5-node ring (MAX-CUT)
- Optimizer: [TBD - COBYLA or SLSQP]
- Execution Dates: [TBD]

## Optimization Convergence Data [TBD]

[To be populated after experiment execution]

**Per-Trial Convergence:**
| Trial | Seed | p | Iterations | Final Cost | Approx Ratio | Total Shots | CI Width |
|-------|------|---|------------|------------|--------------|-------------|----------|
| 1 | 42 | 1 | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| 2 | 123 | 1 | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |
| 3 | 456 | 1 | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |

**Optional p=2 Extension:**
| Trial | Seed | p | Iterations | Final Cost | Approx Ratio | Total Shots | CI Width |
|-------|------|---|------------|------------|--------------|-------------|----------|
| 4 | 789 | 2 | [TBD] | [TBD] | [TBD] | [TBD] | [TBD] |

## Cost Function Estimation Accuracy [TBD]

[To be populated after analysis]

**Per-Iteration Shadow CI Quality:**
- Confidence interval width (per observable): [TBD - target < 0.2]
- Coverage: [TBD - target ≥ 80%]
- Oscillations in cost estimate: [TBD - acceptable range ±0.1]

## Approximation Ratio Analysis [TBD]

**Individual Trial Results:**
| Trial | p | Final Approx Ratio | Classical Optimal | Solution Quality |
|-------|---|-------------------|-------------------|------------------|
| 1 | 1 | [TBD] | 2.5 (MAX edges) | [TBD] |
| 2 | 1 | [TBD] | 2.5 | [TBD] |
| 3 | 1 | [TBD] | 2.5 | [TBD] |

**Aggregate Statistics (p=1):**
- Approx Ratio (mean ± std): [TBD mean] ± [TBD std]
- Min/Max: [TBD min] / [TBD max]
- Pass threshold (≥0.90): [TBD PASS/FAIL]

## Convergence Efficiency Comparison [TBD]

**Shadow-Based vs. Standard QAOA:**

| Metric | Standard QAOA | Shadow (O-T01) | Improvement |
|--------|---------------|----------------|-------------|
| Shots per iteration | 1000 | 300 | 70% ↓ |
| Iterations to convergence | [TBD baseline] | [TBD shadow] | [TBD]% |
| Total shots | [TBD baseline] | [TBD shadow] | [TBD]% |
| Step reduction target | N/A | ≥20% | [TBD PASS/FAIL] |

[Note: Standard QAOA baseline to be executed separately or sourced from literature]

## Shadow Estimation Quality [TBD]

**Per-Iteration Analysis:**

- **Cost Function Noise:** Standard deviation of cost estimates across trials [TBD]
- **Shadow CI Coverage:** Fraction of iterations where true cost within 95% CI [TBD - target ≥80%]
- **Optimization Impact:** Does high-noise iteration (wide CI) correlate with slow convergence? [TBD]

**Observable-by-Observable:**

| Edge (Observable) | Mean ZZ Estimate | CI Width | Trials Converged |
|------------------|-----------------|----------|------------------|
| Z₀Z₁ | [TBD] | [TBD] | [TBD] |
| Z₁Z₂ | [TBD] | [TBD] | [TBD] |
| Z₂Z₃ | [TBD] | [TBD] | [TBD] |
| Z₃Z₄ | [TBD] | [TBD] | [TBD] |
| Z₄Z₀ | [TBD] | [TBD] | [TBD] |

## Comparison to Phase 1 Goals [TBD]

| Criterion | Target | Result | Status |
|-----------|--------|--------|--------|
| Approx Ratio ≥ 0.90 | ✓ | [TBD] | [TBD PASS/FAIL] |
| Step Reduction ≥ 20% | ✓ | [TBD]% | [TBD PASS/FAIL] |
| ≥3 Trials | ✓ | [TBD] | [TBD PASS/FAIL] |
| Manifest Generated | ✓ | [TBD] | [TBD PASS/FAIL] |

## Ansatz Scaling (p=1 vs p=2) [TBD]

[If p=2 trials completed]

| Metric | p=1 | p=2 | Scaling Trend |
|--------|-----|-----|----------------|
| Final Approx Ratio | [TBD] | [TBD] | [Better/Worse/Similar] |
| Iterations to Convergence | [TBD] | [TBD] | [More/Fewer] |
| Total Shots (for p-level improvement) | [TBD] | [TBD] | [Efficient/Inefficient] |
| Parameter Tuning Difficulty | [TBD] | [TBD] | [Easier/Harder] |

## Hardware vs. Simulator Results [TBD]

[If simulator verification completed]

**Simulator Verification (ibm_qasm_simulator):**
- Perfect noise-free execution to compare against hardware
- Approximation ratio (simulator): [TBD]
- Iterations to convergence (simulator): [TBD]

**Hardware Degradation:**
- Approx ratio loss (simulator → hardware): [TBD]%
- Extra iterations required: [TBD]
- Root cause (noise, readout error, etc.): [TBD]

## Key Findings [TBD]

[To be populated after analysis]

**Expected findings:**
1. Shot-frugal cost estimation enables ≥20% reduction in optimizer iterations
2. Approximation ratio ≥0.90 maintained despite lower shot counts
3. Shadow-based cost estimates stable enough for COBYLA/SLSQP convergence
4. p=2 ansatz shows improvement over p=1 (if executed)
5. Manifest and convergence logging work as designed for Phase 1 integration

## Limitations and Caveats [TBD]

Expected limitations:
- Small problem size (5 nodes): Ring MAX-CUT easier than larger graphs; scaling unclear
- Simulator vs. hardware noise: QAOA particularly sensitive to gate errors; larger systems may degrade faster
- Limited trial count (3): Statistical significance limited; Phase 2 should increase
- Baseline comparison: May source standard QAOA baseline from external literature rather than executing locally
- Shadow budget: 300 fixed; adaptive allocation (VACS) reserved for Phase 2

## Data Files [TBD]

Manifests: `data/manifests/o-t01-trial-*.json`
Convergence Logs: `data/logs/o-t01-trial-*-convergence.json`
Final Results: `data/results/o-t01-trial-*-final-solution.json`
Aggregated Summary: `results/o-t01-summary.json`

## Next Steps

- If PASSED (approx_ratio ≥0.90 AND step_reduction ≥20%):
  - Proceed to Phase 1 gate review with O-T01 as optimization evidence
  - Plan O-T02 (larger graphs, p=2-3)
  - Draft Shadow-VQE patent claims

- If PARTIAL PASS (approx_ratio ≥0.90 BUT step_reduction <20%):
  - Investigate convergence stalling (may need larger shadow_size)
  - Try different optimizer (e.g., SLSQP vs COBYLA)
  - Check if standard QAOA baseline overstated

- If FAILED (approx_ratio <0.90):
  - Debug optimization (are circuit params in good range?)
  - Verify shadow quality (increase shadow_size to 500)
  - Try simulator-only run to isolate hardware noise issues

---

**Document Version:** 1.0 (Template)
**To Be Updated:** After experiment execution
**Next Review:** Upon O-T01 completion
