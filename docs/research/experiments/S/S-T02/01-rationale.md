# S-T02: Noise-Aware GHZ with MEM - Rationale

**Experiment ID:** S-T02
**Workstream:** S (Shadows)
**Status:** Planned (Target: Nov 2025)
**Phase:** Phase 1 Foundation & R&D

## Overview

S-T02 demonstrates noise-aware classical shadows (v1) with measurement error mitigation (MEM) on IBM quantum hardware. This experiment directly compares v0 baseline (S-T01) vs. v1 noise-aware performance to quantify variance reduction and SSR improvement from inverse channel correction.

## Scientific Rationale

### Why This Experiment?

1. **v1 Validation:** First hardware test of noise-aware inverse channel + MEM combination
2. **Mitigation Effectiveness:** Quantify 20-30% variance reduction target from mitigation
3. **SSR Improvement:** Demonstrate that v1 achieves SSR ≥ 1.1× even if v0 (S-T01) fails
4. **Phase 2 Preparation:** Validate mitigation stack before fermionic shadows (S-T03) and adaptive sampling (S-T04)

### Why Noise-Aware Shadows?

**Theory (Chen et al. 2021):**
- Inverse channel corrects for known noise (gate errors, T1/T2 decay)
- Expected variance reduction: 20-30% for typical IBM noise levels
- Enables sample complexity closer to ideal (SMOKE-SIM) performance

## Connection to Larger Research Plan

**Mitigation Chain:**
```
S-T01 (v0 baseline) ──> S-T02 (v1 + MEM) ──> Phase 2 v2/v3/v4
         │                     │                      │
         └─> SSR_v0       └─> SSR_v1          └─> Advanced mitigation
              (lower bound)      (Phase 1 target)        (Phase 2+)
```

**Enables:** S-T03 (fermionic), S-T04 (adaptive), C-T02 (LiH with v1), Phase 2 campaigns

## Expected Outcomes

| Metric | v0 (S-T01) | v1 (S-T02) Target | Improvement |
|--------|------------|-------------------|-------------|
| **SSR** | 1.1-1.3× | 1.3-1.5× | +0.2× |
| **Variance Reduction** | Baseline | 20-30% ↓ | v1 advantage |
| **CI Coverage** | 80% | 85-90% | Tighter CIs |

## Relevant Literature

- **Chen et al. (2021):** "Robust shadow estimation" - inverse channel theory
- **Temme et al. (2017):** Measurement error mitigation (MEM) foundations
- **Kandala et al. (2019):** MEM + ZNE for VQE - mitigation synergy

## Next Steps After Completion

1. **Phase 1 Completion:** v1 validated for cross-workstream use
2. **S-T03 Fermionic:** Apply v1 to 2-RDM estimation
3. **C-T02 LiH:** Use v1 for chemistry scaling experiments

## Part of Phase 1 Research Plan

S-T02 completes the shadows mitigation validation:
- ✅ v0 validated (S-T01)
- 🔄 v1 validation (S-T02 - this experiment)
- ⏳ v2/v3/v4 development (Phase 2)

**Timeline:** Nov 2025
**Priority:** HIGH (Phase 1 exit criterion)
