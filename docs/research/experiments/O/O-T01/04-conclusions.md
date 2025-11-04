# O-T01: QAOA MAX-CUT with Shot-Frugal Cost Estimation - Conclusions

**Experiment ID:** O-T01
**Status:** [PLANNED - Template for Future Conclusions]

## Key Findings [TBD]

[To be populated after experiment execution]

Expected findings:
1. Shot-frugal shadow-based cost estimation achieves ≥20% reduction in optimizer iterations vs. standard QAOA
2. Approximation ratio ≥0.90 demonstrated across ≥3 independent trials (solution quality maintained)
3. Shadow cost function estimates sufficiently stable for COBYLA/SLSQP convergence to local minima
4. Manifest and convergence logging successfully generate provenance data for Phase 1 optimization data drop
5. Cross-workstream synergy confirmed: shadows validated for optimization (S + C + O workstreams)
6. [Optional] p=2 ansatz shows marginal improvement in approximation ratio at cost of extra optimization complexity

## Success Criteria Assessment [TBD]

**Phase 1 Exit Criteria for Optimization Workstream:**

- Approx Ratio ≥ 0.90: [TBD PASS/FAIL]
  - Ensures solution quality meets acceptable threshold for quantum advantage claim
  - If PASS: O-T01 provides valid optimization evidence for Phase 1 gate review

- Step Reduction ≥ 20%: [TBD PASS/FAIL]
  - Demonstrates shot efficiency benefit of shadow-based cost estimation
  - If PASS: Validates Phase 1 optimization workstream target

- Manifest Generated: [TBD PASS/FAIL]
  - Complete provenance tracking (circuit, backend, shadow_config, results)
  - If PASS: Supports Phase 1 exit criterion "optimization data drop"

- ≥3 Trials Completed: [TBD PASS/FAIL]
  - Statistical confidence in convergence behavior
  - If PASS: Demonstrates reproducibility across random seeds

**Overall Assessment:** [TBD PASS/FAIL]
- PASS: All 4 criteria met → O-T01 successfully validates Phase 1 optimization starter experiment
- PARTIAL PASS: 3/4 criteria met → Phase 1 can complete with caveat (acceptable if optimization deemed "nice-to-have")
- FAIL: <3/4 criteria met → Requires Phase 2 to address shortcomings (Phase 1 completion still possible if S-T01/S-T02 + C-T01 pass)

## Implications for Phase 1 & Phase 2

### Phase 1 Completion

**If O-T01 PASSED:**
✅ Optimization workstream validated
✅ Cross-workstream integration demonstrated (S + C + O all successful)
✅ Shadow methodology credibility extended beyond static state estimation
✅ Supports Phase 1 gate review decision (+ S-T01/S-T02 + C-T01 = comprehensive evidence)

**Impact on Phase 1 Gate Review:**
- Phase 1 can close with high confidence in shadow methodology breadth
- Enables Phase 2 expansion to chemistry/optimization/benchmarking applications
- Patent themes (VACS, Shadow-VQE, Shadow-Benchmarking) gain credible experimental evidence

**If O-T01 FAILED or PARTIALLY PASSED:**
⚠️ Optimization may require mitigation (v1 + MEM, larger shadows, adaptive allocation)
⚠️ Phase 1 can still complete if S-T01/S-T02 + C-T01 provide sufficient evidence
⚠️ Phase 2 O-T02/O-T03 timeline may shift to accommodate Phase 1 optimization remediation

### Phase 2 Planning

**O-T01 Results Inform:**

1. **O-T02 Design (Larger Graphs):**
   - If O-T01 approx_ratio is robust (>0.91): Confident in scaling to 7-8 node graphs
   - If O-T01 requires high shadow budgets (>500): Plan O-T02 with v1 + MEM from start
   - If O-T01 shows fast convergence (<40 iterations): O-T02 can increase p (more layers)

2. **Shadow Budget Guidelines (Phase 2):**
   - If shadow_size=300 sufficient: Standardize for chemistry/optimization (C-T02, O-T02)
   - If shadow_size=300 marginal: Increase to 500-1000 for larger problems
   - If shadow_size=300 overkill: Reduce to 150-200 for efficiency (reserve budget for more trials)

3. **Optimizer Selection (Phase 2):**
   - COBYLA vs. SLSQP performance on 5-node ring informs choice for larger graphs
   - If COBYLA converges reliably: Use for O-T02 without retesting
   - If convergence issues present: Evaluate gradient-based methods (SPSA, quantum natural gradient)

4. **Adaptive Shadow Allocation (VACS Patent):**
   - O-T01 convergence data may show: Early iterations tolerate lower accuracy, final iterations need high precision
   - This asymmetry motivates VACS: Allocate fewer shadows early, more shadows late
   - Phase 2 O-T03 (full Shadow-VQE) can test VACS on chemistry Hamiltonians

### Cross-Workstream Insights

**If S-T01 + C-T01 + O-T01 all PASSED:**
✅ Shadows work for static state estimation (S-T01: GHZ)
✅ Shadows work for Hamiltonian estimation (C-T01: H₂)
✅ Shadows work for dynamic optimization loops (O-T01: QAOA)
→ **Confidence Level: HIGH** for Phase 2 expansion and patent filing

**If S-T01 + C-T01 PASSED but O-T01 FAILED:**
⚠️ Shadows reliable for static measurements but may struggle with iterative algorithms
⚠️ Phase 2 Shadow-VQE (iterative Hamiltonian estimation) at risk
→ **Mitigation:** Investigate why O-T01 failed; may need v1 + MEM or adaptive strategies
→ **Path Forward:** Phase 2 can still proceed with confidence for S/C; O workstream requires deeper investigation

## Limitations and Caveats [TBD]

Expected limitations:
- **Small problem size (5-node ring):** MAX-CUT easier than larger graphs or random topologies; scaling behavior unknown
- **Simulator noise absence (if hardware run):** Noise may degrade convergence more severely on larger problems; Phase 2 will test p>2 where noise impact grows
- **Limited trial count (3):** Statistical uncertainty in convergence metrics; Phase 2 should expand to 5+ trials per configuration
- **Fixed shadow budget (300):** No adaptive allocation; Phase 2 VACS will test variable budgets per iteration
- **Single optimizer (COBYLA):** SLSQP, SPSA, or quantum natural gradient may perform better; Phase 2 will compare
- **Ring topology limitation:** Linear/ring graphs often easier for QAOA than random/bipartite graphs; Phase 2 will test harder topologies
- **Baseline sourcing:** Standard QAOA baseline may come from literature rather than direct execution; reduces direct comparison rigor

## Caveats for Patent Strategy

**O-T01 as Evidence for Patents:**

1. **Shadow-VQE Patent (Cost Function Reuse):**
   - O-T01 demonstrates shadow estimates per optimizer iteration (supports reuse claim)
   - CAVEAT: O-T01 is cost function only, not full VQE (uses classical cost optimization)
   - Full Shadow-VQE requires C-T02/C-T03 (chemistry Hamiltonian, variational loop)
   - Status: O-T01 partial evidence; C-T02 completion essential for strong patent claim

2. **VACS Patent (Variance-Aware Adaptive Shadows):**
   - O-T01 convergence data may show iteration-dependent accuracy requirements
   - CAVEAT: O-T01 uses fixed shadow_size=300; VACS requires adaptive allocation testing
   - Full VACS validation requires Phase 2 O-T03 with dynamic shadow allocation
   - Status: O-T01 exploratory; Phase 2 O-T03 essential for robust patent claim

## Next Steps [TBD]

### Immediate (Before Phase 1 Gate Review)

1. **Complete Analysis:**
   - Aggregate convergence data from ≥3 trials
   - Compute step reduction metric (iterations_baseline / iterations_shadow)
   - Verify manifest completeness and checksums

2. **Prepare Summary Report:**
   - Highlight key metrics (approx_ratio, step reduction, total shots)
   - Prepare comparison table (shadow-based vs. standard QAOA)
   - Draft 1-2 page executive summary for Phase 1 gate review

3. **Cross-Check vs. Phase 1 Targets:**
   - Verify approx_ratio ≥ 0.90
   - Verify step reduction ≥ 20% (or document why lower)
   - Confirm ≥3 trials completed
   - Ensure manifest + convergence data stored properly

### Phase 1 Gate Review Input

- Include O-T01 summary in Phase 1 completion report
- Highlight: "Optimization workstream validated; shadows extend to iterative algorithms"
- Decision: Phase 1 PASS if O-T01 + S-T01/S-T02 + C-T01 successful
- Decision: Phase 1 CONDITIONAL PASS if 2/3 workstreams successful (optimization may be deferred)

### Phase 2 Planning (If O-T01 PASSED)

1. **O-T02 - Larger Graphs:**
   - Target: 7-8 node graphs (forest or grid topology), p=2-3 ansatz
   - Schedule: Q1 2026 (after Phase 1 close)
   - Preparatory work: Finalize classical baseline, qubit connectivity mapping

2. **O-T03 - Shadow-VQE (Integration with C-T02):**
   - Combine C-T02 (LiH chemistry) with O-T03 (variational ansatz optimization)
   - Use shadow-based cost function + quantum ansatz gradient estimation
   - Full Shadow-VQE workflow demonstration

3. **VACS Development (Phase 2 Research Track):**
   - Design adaptive shadow allocation strategy
   - Test on O-T03 (full VQE) and S-T04 (fermionic shadows)
   - Target patent filing Q2 2026

## Part of Phase 1 Research Plan

**O-T01 Role in Phase 1:**
- First optimization workstream experiment
- Validates shot-frugal QAOA using shadow-based cost estimation
- Provides optimization evidence for Phase 1 exit criteria ("first optimization data drop")

**Status:** [PLANNED]
**Timeline:** Target Nov 10-16, 2025 (Week 2 of Phase 1)
**Priority:** HIGH (Phase 1 completion, cross-workstream validation)
**Blocking Items:** None (Phase 1 can complete without O-T01 if S/C successful, but O-T01 strongly preferred)

**Success Definition:**
- Approx Ratio ≥ 0.90 ✓
- Step Reduction ≥ 20% ✓
- Manifest Generated ✓
- ≥3 Trials Completed ✓
→ **Phase 1 Optimization Workstream VALIDATED**

## Publication Strategy Integration

**O-T01 Publication Venue:**

**arXiv Preprint (Jan 2026, if Phase 1 successful):**
- Title: "Shot-Efficient Quantum Optimization with Classical Shadows"
- Data: O-T01 convergence data, C-T01 for context (multi-workstream scope)
- Key claim: QAOA achieves ≥20% shot reduction via shadow-based cost estimation
- Figures: Convergence comparison (shadow vs. standard), approximation ratio per trial

**Journal Submission (Mar-Apr 2026):**
- Target: PRX Quantum or npj Quantum Information
- Scope: Phase 1 shadows validation (S-T01) + Phase 1 chemistry (C-T01) + Phase 1 optimization (O-T01)
- Focus: Hardware validation across three application domains

**Conference Abstract (Nov 2025, abstract deadline):**
- APS March Meeting 2026: "Classical Shadows for Quantum Optimization"
- Poster or talk: O-T01 QAOA results + S-T01 benchmarks
- Timing: Submit abstract after O-T01 completes (early Nov 2025)

## Document Maintenance

**Version:** 1.0 (Template)
**To Be Updated:** After O-T01 execution and analysis completion
**Next Review:** Before Phase 1 gate review meeting
**Reviewed By:** Research Lead, Phase 1 Gate Review Committee

---

**Summary for Phase 1 Gate Review:**

O-T01 demonstrates that classical shadows methodology extends beyond static state estimation (S workstream) and molecular simulation (C workstream) to **dynamic iterative optimization loops** (O workstream). Success in O-T01 validates the cross-workstream applicability of shadows and provides evidence for high-confidence Phase 1 completion and Phase 2 expansion.

**Expected Outcome:** If O-T01 achieves ≥20% step reduction with approx_ratio ≥0.90, Phase 1 research program exits with validated shadows methodology across three foundational application domains (shadows, chemistry, optimization), positioning QuartumSE for Phase 2 expansion to advanced techniques (adaptive shadows, fermionic shadows, benchmarking) and patent filing.
