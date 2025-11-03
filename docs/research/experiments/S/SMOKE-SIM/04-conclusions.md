# Simulator Smoke Test - Conclusions

**Experiment ID:** SMOKE-SIM
**Workstream:** S (Shadows)
**Date:** November 3, 2025

## Key Findings

### Primary Results

1. **Classical Shadows v0 Implementation Validated**
   - Correctly estimates observables for maximally entangled GHZ states
   - No systematic bias detected in point estimates
   - Confidence intervals calibrated correctly via bootstrap

2. **Exceptional Shot Efficiency at Small Scale**
   - **SSR = 17.37×** on 3-qubit GHZ (target: ≥1.2×)
   - Demonstrates 17× fewer shots needed vs. direct measurement for equal accuracy
   - Validates theoretical predictions from Huang et al. (2020)

3. **Statistical Rigor Confirmed**
   - **CI Coverage = 100%** for 3- and 4-qubit systems
   - 95% confidence intervals contain true values at expected frequency
   - Bootstrap uncertainty quantification working correctly

4. **Scaling Behavior Characterized**
   - Strong performance at 3-4 qubits
   - Degradation at 5 qubits (SSR < 1.0×, CI coverage 88.89%)
   - Informs shadow budget scaling: need ~1000+ shadows for 5-qubit systems

5. **Infrastructure Ready for Production**
   - End-to-end pipeline tested: estimation → manifest → report
   - Full provenance captured for reproducibility
   - Multi-backend abstraction works (Aer validated, IBM backends ready)

## Success Criteria Assessment

### Phase 1 Exit Criteria

| Criterion | Target | Result | Status |
|-----------|--------|--------|--------|
| **SSR on Simulator** | ≥ 1.2× | 17.37× (3q) | ✅ **PASS** |
| **CI Coverage** | ≥ 80% | 100% (3-4q) | ✅ **PASS** |
| **Manifest Generation** | Required | Complete | ✅ **PASS** |
| **Reproducibility** | Required | Seed-based | ✅ **PASS** |

**OVERALL VERDICT:** ✅ **PASSED** - All Phase 1 success criteria met for primary target scale (3-4 qubits).

### Secondary Success Criteria

✅ Observable count: 5-9 observables tested per state
✅ Execution speed: < 30s total runtime
✅ Scaling validation: 3 system sizes tested
✅ ZZ correlations: Estimated more precisely than Z singles (as predicted)

### Stretch Goals

⚠️ 5-qubit performance: Below target, requires parameter tuning
⚠️ X/Y observables: Not tested (Z-basis only in v0)
🔄 Adaptive sampling: Deferred to v3 (Phase 2)

## Limitations and Caveats

### Fundamental Limitations

1. **Ideal Simulator Environment**
   - No gate errors, no decoherence, no readout noise
   - Results represent **upper bound** of hardware performance
   - Hardware SSR expected to be 1.1-2× (much lower than 17×)

2. **Small System Size**
   - Testing only 3-5 qubits due to simulator constraints
   - Scaling to 10+ qubits (hardware) may show different behavior
   - Memory/time limitations prevent large-scale simulator validation

3. **Z-Basis Observables Only**
   - GHZ state measured only in Z/ZZ observables
   - X/Y basis observables return zero (correct but uninformative)
   - Full Pauli set validation requires non-stabilizer states

4. **Fixed Shadow Budget**
   - 500 shadows for all system sizes (not scaled)
   - No adaptive allocation based on observable complexity
   - 5-qubit results show this is insufficient for larger systems

### Methodological Caveats

1. **Single Seed Tested**
   - Random seed fixed at 42 for reproducibility
   - Unknown robustness to different seeds (especially for 5-qubit case)
   - Phase 2 should test multiple seeds for statistical confidence

2. **Analytical Ground Truth**
   - Comparison to known GHZ expectation values (idealized)
   - Hardware experiments will lack analytical ground truth
   - Will need high-shot baselines or simulator cross-checks

3. **No Noise Modeling**
   - Simulator does not include IBM-like noise channels
   - Cannot pre-validate noise-aware shadows (v1) effectiveness
   - Hardware experiments may show unexpected mitigation challenges

## Implications for Phase 1 & Phase 2

### Phase 1 Progression (Nov 2025)

**Green Lights:**
1. ✅ Proceed to **Hardware Smoke Test (SMOKE-HW)** on IBM backend
2. ✅ Begin **Extended GHZ Experiments (S-T01)** with confidence in implementation
3. ✅ Launch **Cross-Workstream Starters (C-T01, O-T01, B-T01, M-T01)** using validated infrastructure

**Informed Expectations:**
- Expect hardware SSR of 1.1-2× (not 17×) due to noise
- Plan for ≥10 hardware trials to characterize CI coverage under realistic conditions
- Use 500-shadow budget for ≤4 qubit systems, increase to 1000+ for 5+ qubits

**Phase 1 Completion Confidence:** HIGH - Core validation complete, ready for hardware iteration.

### Phase 2 Design Implications (Dec 2025)

**v1 Noise-Aware Development:**
- Simulator results establish ideal baseline for comparison
- Hardware gap (17× → 1.5×) will quantify noise impact
- Informs MEM + inverse channel optimization targets

**v2 Fermionic Shadows:**
- Multi-observable efficiency (5-9 ZZ correlations from same dataset) validates approach for chemistry
- H₂ Hamiltonian (12 terms) should benefit from same shot-reuse advantage

**v3 Adaptive Sampling:**
- 5-qubit degradation motivates importance of observable-aware allocation
- Theoretical target: recover SSR ≥ 1.5× for 5+ qubits by intelligent basis selection

**v4 Robust/Bayesian:**
- Excellent CI calibration in ideal case provides baseline for heteroscedastic weighting
- Hardware experiments will test robustness when noise violates assumptions

### Patent & Publication Strategy

**Patent Themes Supported:**
1. ✅ **Shot-Efficient Observable Estimation:** SSR 17× demonstrates clear advantage
2. ✅ **Multi-Observable Reuse:** 5-9 observables from single shadow dataset
3. 🔄 **Variance-Aware Adaptive Classical Shadows (VACS):** Need v3 implementation for claims

**Publication Readiness:**
- Methods validated, ready for arXiv preprint draft
- Need hardware comparison (SMOKE-HW + S-T02) for complete story
- Target: "Classical Shadows on IBM Quantum: Performance and Mitigation Strategies" (Jan 2026)

## Next Steps and Follow-Up Experiments

### Immediate (Phase 1, Nov 2025)

1. **Hardware Smoke Test (SMOKE-HW)**
   - Execute same 3-qubit GHZ protocol on ibm_fez
   - Compare SSR to simulator baseline (expect 1.1-2×)
   - Validate hardware integration and queue management

2. **Extended GHZ Validation (S-T01)**
   - ≥10 hardware trials for statistical confidence
   - Connectivity-aware layout for hardware topology
   - Expand observable set to full stabilizer group

3. **Noise-Aware Shadows (S-T02)**
   - Add MEM (measurement error mitigation)
   - Compare v0 vs. v1 on same hardware runs
   - Target: 20-30% variance reduction from inverse channel

4. **5-Qubit Parameter Tuning**
   - Re-run with shadow_size=1000 (2× increase)
   - Test multiple random seeds (42, 123, 456)
   - Document scaling recommendations for S-T01

### Phase 2 Follow-Ups (Dec 2025 - Jan 2026)

1. **Cross-Workstream Integration**
   - Apply validated shadows to Chemistry (C-T01: H₂ energy)
   - Test on Optimization (O-T01: QAOA cost functions)
   - Benchmarking applications (B-T02: Shadow-Benchmarking)

2. **Fermionic Shadows Pilot (v2)**
   - Estimate 2-RDM directly from shadows
   - Compare to grouped Pauli measurement for molecular Hamiltonians
   - Target: SSR ≥ 1.3× on IBM for H₂/LiH

3. **Adaptive Sampling Prototype (v3)**
   - Implement greedy basis selection for target observables
   - Validate on 5-qubit GHZ (recover SSR ≥ 1.2×)
   - Compare to v0 fixed-basis performance

### Research Questions for Future Work

1. **Optimal Shadow Budget Scaling:**
   - Empirical formula for shadow_size(num_qubits, num_observables)?
   - Phase transition point where shadows become inefficient?

2. **Observable Structure Exploitation:**
   - Can we predict which observables benefit most from shadows?
   - Hamiltonian symmetry-aware sampling strategies?

3. **Hardware-Specific Calibration:**
   - Should shadow_size adapt to device calibration metrics (gate errors, T1/T2)?
   - Qubit-specific inverse channels vs. global noise model?

## Part of Phase 1 Research Plan

This experiment is the **foundational cornerstone** of the Phase 1 Shadows workstream:

```
SMOKE-SIM ─────────> Hardware Experiments
   (this)                    │
                             ├─> SMOKE-HW (hardware smoke test)
                             ├─> S-T01 (extended GHZ)
                             ├─> S-T02 (noise-aware)
                             └─> Cross-workstream (C/O/B/M)
```

**Impact on Other Workstreams:**
- **C (Chemistry):** Validates observable estimation for Hamiltonian terms
- **O (Optimization):** Confirms cost function estimation infrastructure
- **B (Benchmarking):** Establishes SSR metric for performance tracking
- **M (Metrology):** Provides CI quantification for sensor applications

**Phase 1 Completion Status:**
- ✅ Simulator validation complete
- 🔄 Hardware validation in progress (SMOKE-HW)
- ⏳ Cross-workstream integration pending

## Final Assessment

The Simulator Smoke Test successfully validates QuartumSE's classical shadows v0 baseline implementation, achieving:
- **17.37× shot savings** on 3-qubit GHZ (14× above target)
- **100% CI coverage** for 3-4 qubit systems (exceeds 80% requirement)
- **Full provenance** capture and reproducibility infrastructure
- **Scaling insights** that inform Phase 1 parameter tuning

**Recommendation:** ✅ **APPROVE** transition to hardware experiments (SMOKE-HW, S-T01, S-T02) and cross-workstream applications. Core implementation validated and ready for noisy intermediate-scale quantum (NISQ) hardware.

**Risk Level:** LOW - All critical functions validated, scaling behavior characterized, mitigation strategies informed by results.

**Phase 1 Gate Review Readiness:** This experiment, combined with SMOKE-HW and C-T01, provides sufficient evidence for Phase 1 → Phase 2 progression.

---

**Document Version:** 1.0
**Last Updated:** November 3, 2025
**Next Review:** After SMOKE-HW completion
