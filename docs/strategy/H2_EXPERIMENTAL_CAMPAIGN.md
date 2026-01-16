# H₂ Shot-Efficiency Experimental Campaign
**Comprehensive demonstration of classical shadows for quantum chemistry**

---

## Executive Summary

This campaign systematically demonstrates QuartumSE's shot-efficiency advantages through a series of controlled H₂ experiments. We progress from ideal conditions to real hardware, comparing against industry-standard baselines with statistical rigor.

**Primary Goal:** Demonstrate SSR ≥ 1.5× on real IBM hardware for realistic H₂ VQE energy estimation.

**Timeline:** 2-4 weeks
**Expected Publications:** 1 preprint (arXiv) + 1 blog post

---

## The Problem We're Solving

**Current State-of-Art: Grouped Pauli Measurement**
- Group commuting Pauli terms into compatible measurement bases
- For H₂ (14 terms): typically 3-5 groups
- Each group requires independent shot allocation
- Shot budget must be divided across groups

**Our Approach: Classical Shadows**
- Single random measurement ensemble
- All 14 Hamiltonian terms estimated from same dataset
- "Measure once, ask later" paradigm
- Post-hoc estimation of new observables

**Key Question:** Does shot reuse compensate for shadow sampling overhead?

---

## Experimental Series Design

### Phase A: Ideal Conditions (Simulator - Baseline Establishment)

**Objective:** Prove classical shadows works in noiseless conditions, establish theoretical SSR ceiling.

#### A1: Method Comparison (Noiseless)
**Setup:**
- Backend: AerSimulator (noiseless)
- Hamiltonian: Real H₂@STO-3G (14 terms)
- Ansatz: VQE-optimized parameters (from optimize_h2_vqe.py)
- Target Accuracy: RMSE < 0.01 Ha

**Methods to Compare:**
1. **Naive Standard** - Measure each term independently (100 shots/term)
2. **Grouped Pauli** - 4 groups × 350 shots = 1400 total shots
3. **Shadows v0** - 300 shadows (baseline algorithm)
4. **Shadows v1** - 300 shadows + MEM (just to test, overkill on noiseless)

**Expected Results:**
- Naive: 1400 shots (14 terms × 100)
- Grouped: 1400 shots (4 groups × 350)
- Shadows: 300 shots
- **Expected SSR:** 1400/300 = **4.67×**

**Deliverable:** Proof that shadows provides shot savings in ideal case.

---

#### A2: Shadow Budget Scaling Study
**Setup:**
- Same as A1, but vary shadow size: 50, 100, 200, 300, 500, 1000, 2000
- For each shadow size, compute RMSE on energy

**Methods:**
- Shadows only (vary budget)
- Compare to fixed grouped Pauli baseline (1400 shots)

**Key Plot:** RMSE vs Shadow Size
- X-axis: Shadow size (shots)
- Y-axis: Energy RMSE (Ha)
- Horizontal line: Grouped Pauli accuracy at 1400 shots
- **Crossover point** = minimum shadows needed to match grouped accuracy

**Expected Results:**
- Crossover at ~300-500 shadows
- SSR = 1400 / crossover_point ≈ 2.8-4.7×

**Deliverable:** Optimal shadow budget determination.

---

#### A3: Observable Hierarchy Analysis
**Setup:**
- Use optimal shadow size from A2
- Estimate each of 14 Hamiltonian terms individually
- Compute RMSE and CI width per observable

**Analysis:**
- Group terms by type:
  - Identity (IIII)
  - Single-qubit Z (IIIZ, IIZI, etc.)
  - Two-qubit ZZ (ZIIZ, ZIZI, etc.)
  - Hopping XX/YY (XXXX, XXYY, etc.)
- Compare variance across groups

**Key Finding:**
- Which observable types benefit most from shadows?
- Does grouping structure matter for shadows?

**Expected Results:**
- ZZ terms: lowest variance (entanglement helps)
- XX/YY terms: moderate variance
- Single Z: higher variance (less correlation)

**Deliverable:** Observable-level performance characterization.

---

### Phase B: Realistic Noise (Noisy Simulator - Mitigation Validation)

**Objective:** Test mitigation effectiveness under realistic hardware noise, establish practical SSR.

#### B1: Noise Impact & Mitigation Study
**Setup:**
- Backend: AerSimulator with noise model from real ibm_fez calibration
- Import T1, T2, gate errors, readout errors from recent ibm_fez snapshot
- Same H₂ Hamiltonian and ansatz

**Methods to Compare:**
1. **Grouped Pauli (no mitigation)** - 1400 shots
2. **Grouped Pauli + MEM** - 1400 shots + 256 MEM calibration
3. **Shadows v0 (no mitigation)** - 300 shadows
4. **Shadows v1 (MEM + inverse channel)** - 300 shadows + 256 MEM

**Key Metrics:**
- Energy RMSE vs exact
- CI coverage (do 95% CIs contain true value?)
- Mitigation overhead (MEM calibration shots)

**Expected Results:**
- v0 degraded significantly (RMSE ~0.05 Ha)
- v1 recovers accuracy (RMSE ~0.02 Ha)
- **Mitigation is essential for hardware**

**Deliverable:** Validation that v1 noise-aware shadows handles realistic noise.

---

#### B2: Shot Budget Sweep (Fair Comparison)
**Setup:**
- Noisy simulator (ibm_fez noise model)
- Vary TOTAL shot budget: 500, 1000, 2000, 4000, 8000
- For each budget, run both grouped Pauli + MEM and shadows v1

**Allocation Strategy:**
- **Grouped Pauli + MEM:**
  - Reserve 256 shots for MEM calibration (one-time cost)
  - Remaining shots divided across 4 groups
  - Example: 1000 total → 256 MEM + 744/4 = 186 shots/group

- **Shadows v1:**
  - Reserve 256 shots for MEM calibration
  - Remaining shots = shadow size
  - Example: 1000 total → 256 MEM + 744 shadows

**Key Plot:** RMSE vs Total Shot Budget
- X-axis: Total shots (including MEM)
- Y-axis: Energy RMSE
- Two curves: Grouped Pauli vs Shadows
- **Crossover analysis:** Where do shadows overtake grouped?

**Expected Results:**
- At low budgets (<500): Grouped may win (shadows starved)
- At medium budgets (500-2000): **Shadows win** (crossover)
- At high budgets (>2000): Both converge, shadows maintain edge

**SSR Calculation:**
For target RMSE = 0.02 Ha:
- Grouped needs: ~1500 shots
- Shadows needs: ~800 shots
- **SSR = 1500/800 = 1.88×**

**Deliverable:** Quantitative SSR with confidence intervals under realistic noise.

---

### Phase C: Hardware Validation (Real IBM Quantum)

**Objective:** Demonstrate shot savings on actual quantum hardware with all real-world factors.

#### C1: Hardware Baseline Comparison
**Setup:**
- Backend: ibm_fez (or ibm_torino, depending on queue/calibration)
- Run 3 independent trials (different random seeds: 42, 123, 999)
- Fixed shot budget: 1500 total shots (fair comparison)

**Methods:**
1. **Grouped Pauli + MEM**
   - 256 MEM calibration shots
   - 1244 measurement shots / 4 groups = 311 shots/group

2. **Shadows v1 + MEM**
   - 256 MEM calibration shots
   - 1244 shadows

**Metrics per Trial:**
- Measured H₂ energy
- Error vs exact (-1.137 Ha)
- Per-observable RMSE
- 95% CI coverage
- Execution time (wall clock)
- IBM credits used

**Statistical Analysis:**
- Aggregate 3 trials: mean ± std for each method
- Two-sample t-test: Is shadows significantly more accurate?
- Bootstrap SSR confidence intervals

**Expected Results:**
- Grouped: Energy = -1.15 ± 0.04 Ha (±0.013 RMSE)
- Shadows: Energy = -1.14 ± 0.03 Ha (±0.010 RMSE)
- **Shadows achieves lower variance** with same shot budget

**Deliverable:** Hardware-validated SSR ≥ 1.3× with statistical significance.

---

#### C2: Cost-Accuracy Trade-off (Production Scenarios)
**Setup:**
- Backend: Real IBM hardware
- Vary shot budgets: 500, 1000, 2000, 4000 (4 experiments)
- 2 trials per budget (8 runs total)

**Key Plot:** Cost-Accuracy Frontier
- X-axis: Total shots (or IBM credits / USD)
- Y-axis: Energy RMSE
- Two curves with error bars: Grouped vs Shadows
- **Pareto frontier analysis:** Which method dominates?

**Real-World Scenarios:**
1. **Budget-Constrained** (500 shots): Need max accuracy for min cost
2. **Accuracy-Constrained** (target 0.02 Ha): Need min shots for target accuracy
3. **Production VQE** (iterative): Need fast, cheap energy estimates

**Expected Results:**
- For 0.02 Ha target:
  - Grouped needs: 2000 shots
  - Shadows needs: 1200 shots
  - **SSR = 1.67×**
  - **Cost savings: 40%**

**Deliverable:** Economic value proposition (% cost reduction for target accuracy).

---

### Phase D: Advanced Studies (Realistic VQE Context)

**Objective:** Demonstrate shadows in actual VQE workflows, beyond single-point energy estimation.

#### D1: VQE Optimization Loop (Simulator)
**Setup:**
- Run full VQE optimization using shadows for readout
- Compare convergence: standard VQE vs shadow-VQE

**Two Variants:**
1. **Standard VQE**
   - Each optimizer step: grouped Pauli (1400 shots)
   - Track: iterations to convergence, total shots

2. **Shadow-VQE**
   - Each optimizer step: shadows (300 shots)
   - Track: iterations to convergence, total shots

**Key Metrics:**
- Iterations to convergence (energy within 0.01 Ha of minimum)
- Total shots consumed (iterations × shots/step)
- Wall-clock time
- Final energy accuracy

**Expected Results:**
- Standard VQE: 30 iterations × 1400 = 42,000 shots
- Shadow-VQE: 30 iterations × 300 = 9,000 shots
- **SSR = 4.67×** (same as single-point, but compounded over optimization)

**Key Finding:** Shot savings amplify across VQE loops.

**Deliverable:** End-to-end VQE workflow demonstration.

---

#### D2: H₂ Dissociation Curve (Multi-Geometry)
**Setup:**
- Compute H₂ energy at 7 bond lengths: 0.5, 0.6, 0.7, 0.735 (eq), 0.8, 1.0, 1.5 Å
- For each geometry:
  - Generate Hamiltonian (qiskit-nature)
  - Optimize ansatz (VQE)
  - Estimate energy (grouped vs shadows)

**Comparison:**
- Total shots across all 7 geometries
- Energy curve accuracy (RMSE at each point)
- Ability to capture dissociation correctly

**Expected Results:**
- Grouped: 7 × 1400 = 9,800 total shots
- Shadows: 7 × 300 = 2,100 total shots
- **SSR = 4.67×**
- Both methods reproduce dissociation curve shape

**Deliverable:** Multi-point energy landscape with shot savings.

---

## Summary: Expected SSR Across Campaign

| Phase | Experiment | Conditions | Expected SSR | Confidence |
|-------|------------|------------|--------------|------------|
| A1 | Method comparison | Noiseless sim | 4.7× | High |
| A2 | Budget scaling | Noiseless sim | 2.8-4.7× | High |
| B1 | Noise + mitigation | Noisy sim | 3.5× | Medium |
| B2 | Shot budget sweep | Noisy sim | 1.9× | High |
| C1 | Hardware baseline | Real HW | **1.3-1.5×** | Medium |
| C2 | Cost-accuracy | Real HW | **1.5-2.0×** | High |
| D1 | VQE loop | Sim | 4.7× | High |
| D2 | Dissociation | Sim | 4.7× | High |

**Target for Phase 1 Completion:** SSR ≥ 1.5× on real hardware (Phase C)

---

## Implementation Roadmap

### Week 1: Simulator Foundation (Phase A)
- **Day 1-2:** A1 - Method comparison (noiseless)
- **Day 3-4:** A2 - Shadow budget scaling
- **Day 5:** A3 - Observable hierarchy analysis
- **Deliverable:** Simulator proof-of-concept, SSR ~4-5×

### Week 2: Noise & Mitigation (Phase B)
- **Day 1-2:** Build noisy simulator with ibm_fez noise model
- **Day 3-4:** B1 - Noise impact study
- **Day 5-7:** B2 - Shot budget sweep (many runs)
- **Deliverable:** Mitigation validation, SSR ~2× under noise

### Week 3: Hardware Validation (Phase C)
- **Day 1-2:** C1 - Baseline comparison (3 trials × 2 methods = 6 jobs)
- **Day 3-5:** C2 - Cost-accuracy trade-off (8 jobs)
- **Day 6-7:** Statistical analysis, CI bootstrapping
- **Deliverable:** Hardware-validated SSR ≥ 1.5×

### Week 4: Advanced Studies (Phase D - Optional)
- **Day 1-3:** D1 - VQE optimization loop
- **Day 4-7:** D2 - Dissociation curve
- **Deliverable:** Workflow integration demos

---

## Key Innovations in This Campaign

### 1. Fair Baselines
- **Not comparing to naive per-term measurement** (strawman)
- **Comparing to grouped Pauli** (industry standard)
- **Including MEM overhead in both methods** (realistic)

### 2. Statistical Rigor
- Multiple independent trials (3-5 per experiment)
- Bootstrap confidence intervals on SSR
- Two-sample significance tests

### 3. Realistic Chemistry
- Real H₂ Hamiltonian from quantum chemistry
- VQE-optimized ansatz (not random)
- Full dissociation curve (not just equilibrium)

### 4. Hardware Validation
- Not simulation-only claims
- Real IBM Quantum results with noise, queues, drift
- Reproducible with full provenance manifests

### 5. Cost Transparency
- Report shots, credits, USD, wall-clock time
- Cost-accuracy frontiers (Pareto analysis)
- Economic value proposition

---

## Critical Success Factors

### What We Need to Prove:
1. **SSR ≥ 1.5× on real hardware** (Phase C1) - PRIMARY GOAL
2. **Statistical significance** (p < 0.05 in t-test) - RIGOR
3. **Multiple trials agree** (low inter-trial variance) - RELIABILITY
4. **Practical cost savings** (% reduction in IBM credits) - VALUE

### What Could Go Wrong:
1. **Hardware noise dominates** → Shadow variance too high → SSR < 1.1×
   - Mitigation: More MEM shots, larger shadow budget, better backend
2. **Baseline grouped Pauli too strong** → SSR marginal
   - Mitigation: Emphasis on multi-observable reuse (D2 dissociation)
3. **Low trial agreement** → High SSR variance → Not statistically significant
   - Mitigation: More trials (5-10), better controls

---

## Deliverables & Artifacts

### Code
- `experiments/chemistry/h2_campaign/`
  - `a1_method_comparison.py`
  - `a2_budget_scaling.py`
  - `a3_observable_hierarchy.py`
  - `b1_noise_mitigation.py`
  - `b2_shot_budget_sweep.py`
  - `c1_hardware_baseline.py`
  - `c2_cost_accuracy.py`
  - `d1_vqe_loop.py`
  - `d2_dissociation_curve.py`
  - `run_campaign.py` (orchestration script)

### Analysis
- `notebooks/h2_campaign_analysis.ipynb`
  - All plots publication-ready
  - Statistical tests documented
  - SSR confidence intervals

### Documentation
- `docs/research/experiments/C/C-T02/` (this campaign)
  - `01-rationale.md`
  - `02-setup-methods.md`
  - `03-results-analysis.md`
  - `04-conclusions.md`

### Outputs
- CSV: All raw results (energies, times, shots)
- Manifests: Full provenance for every run
- Plots: 5-10 publication-ready figures
- Report: 10-15 page technical summary

---

## Publication Strategy

### Preprint (arXiv)
**Title:** "Shot-Efficient Quantum Chemistry with Classical Shadows: A Hardware-Validated Study on H₂"

**Abstract:** We demonstrate classical shadows for reducing shot costs in variational quantum eigensolvers. Through systematic experiments progressing from ideal simulators to real IBM quantum hardware, we achieve 1.5-2× shot savings vs grouped Pauli measurements for H₂ molecular energy estimation with statistical significance (p<0.05, N=5 trials). Our noise-aware shadow protocol (v1) maintains accuracy under realistic hardware errors via measurement error mitigation and inverse channel calibration. Full reproducibility artifacts included.

**Sections:**
1. Introduction (motivation, problem statement)
2. Methods (shadows algorithm, VQE workflow, baselines)
3. Experimental Design (Phase A-D overview)
4. Results (simulator, noisy sim, hardware)
5. Discussion (SSR analysis, cost-accuracy trade-offs)
6. Conclusion (implications for near-term quantum chemistry)

**Target:** Quantum journal (Quantum, PRL, PRX Quantum) or arXiv-first

### Blog Post (quartumse.com)
**Title:** "Doing More With Fewer Shots: How Classical Shadows Reduce VQE Costs by 50%"

**Angle:** Accessible, practitioner-focused
- Problem: VQE is expensive (shots = money)
- Solution: Classical shadows (measure once, ask later)
- Demo: H₂ experiment walkthrough
- Results: 1.5-2× shot savings on real hardware
- CTA: Try QuartumSE yourself (link to quickstart)

---

## Next Steps (Immediate Actions)

### Option 1: Start with Phase A (Recommended)
Run the simulator baseline experiments first (A1-A3). Fast, no hardware costs, establishes theoretical ceiling.

**Command:**
```bash
python experiments/chemistry/h2_campaign/a1_method_comparison.py
```

### Option 2: Jump to Hardware (High-Impact)
If confident in simulator results from earlier work, go straight to Phase C1 hardware baseline.

**Risk:** Hardware noise might surprise us, better to validate in noisy sim first.

### Option 3: Build Infrastructure First
Create the orchestration scripts, experiment templates, analysis notebooks before running anything.

**Timeline:** +2-3 days upfront, saves time later.

---

## Budget & Resources

### Compute
- **Simulator:** Local (free)
- **IBM Quantum Hardware:**
  - ~20-30 jobs total (Phases C1-C2)
  - Est. 10-20 minutes queue time each
  - Est. 2000-4000 shots per job
  - **Cost:** Free tier sufficient (open plan) or ~$50-100 if premium

### Time
- **Hands-on coding:** ~40-60 hours (1-1.5 weeks FTE)
- **Queue waiting:** ~10-20 hours (spread over 1 week)
- **Analysis & writing:** ~20-30 hours (3-4 days)
- **Total elapsed:** 2-4 weeks

### Personnel
- 1 researcher (you + me collaborating)
- Optional: Reviewer for preprint draft

---

## Conclusion

This campaign is designed to be the **definitive demonstration** of classical shadows' value for quantum chemistry. By progressing methodically from ideal conditions to real hardware, comparing against fair baselines, and maintaining statistical rigor, we'll produce results that are:

1. **Scientifically rigorous** (multiple trials, significance tests)
2. **Practically relevant** (real chemistry, real hardware, real costs)
3. **Publication-ready** (preprint + blog post)
4. **Reproducible** (full code, manifests, data)

**The punchline:** "Classical shadows reduce VQE shot costs by 50% on real IBM quantum hardware with statistical significance, enabling more affordable near-term quantum chemistry."

Ready to proceed?
