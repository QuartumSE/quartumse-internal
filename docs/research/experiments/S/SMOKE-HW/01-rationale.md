# Hardware Smoke Test - Rationale

**Experiment ID:** SMOKE-HW
**Workstream:** S (Shadows)
**Status:** Completed (Nov 3, 2025)
**Phase:** Phase 1 Foundation & R&D

## Overview

The Hardware Smoke Test validates QuartumSE's classical shadows implementation on real IBM quantum hardware for the first time. Following successful simulator validation (SMOKE-SIM with SSR=17.37×), this experiment transitions to noisy intermediate-scale quantum (NISQ) devices to verify hardware integration, characterize performance degradation under realistic noise, and validate provenance capture from IBM Quantum runtime.

## Scientific Rationale

### Why This Experiment?

1. **Hardware Integration Validation**: Verify that QuartumSE's backend abstraction correctly interfaces with IBM Quantum Runtime, handling job submission, queue management, and result retrieval.

2. **Noise Characterization**: Establish baseline performance metrics under realistic hardware noise (gate errors, decoherence, readout errors) to set expectations for extended validation campaigns.

3. **Provenance Under Real Conditions**: Test that calibration data capture, backend snapshots, and manifest generation work correctly with live quantum processors (vs. idealized simulators).

4. **Queue & Resource Management**: Validate runtime budget tracking, backend selection logic, and operational procedures before committing to expensive multi-experiment campaigns.

5. **Risk Mitigation for Phase 1**: Quick validation run (100 shots, 3-qubit GHZ) minimizes cost and queue time while confirming readiness for extended experiments (S-T01, S-T02).

## Connection to Larger Research Plan

This experiment is a **critical gate** for Phase 1 progression:

- **Prerequisite for S-T01/S-T02:** Extended GHZ and noise-aware experiments require validated hardware access
- **Informs Mitigation Strategy:** Hardware noise characterization guides MEM and ZNE parameter tuning
- **Unblocks Cross-Workstream:** Chemistry (C-T01), Optimization (O-T01), and other workstreams depend on proven hardware pipeline
- **Phase 1 Exit Criterion:** "End-to-end run on at least one IBM backend" - this experiment satisfies that requirement

**Relationship to SMOKE-SIM:**
- SMOKE-SIM: Ideal performance (SSR=17.37×)
- SMOKE-HW: Realistic performance (expected SSR=1.1-2×)
- Gap analysis informs v1 noise-aware shadows development

## Relevant Literature

1. **IBM Quantum Backend Properties** (IBM Quantum Documentation, 2024)
   - Calibration data interpretation (T1, T2, gate/readout errors)
   - Backend selection best practices for free-tier access
   - Queue management and runtime optimization

2. **Huang, H.-Y., et al. (2021).** "Efficient estimation of Pauli observables by derandomization." *Physical Review Letters*, 127(3), 030503.
   - Discusses practical shadow implementation on NISQ hardware
   - Addresses finite-sampling effects and noise robustness

3. **Temme, K., Bravyi, S., & Gambetta, J. M. (2017).** "Error mitigation for short-depth quantum circuits." *Physical Review Letters*, 119(18), 180509.
   - Foundational work on measurement error mitigation (MEM)
   - Informs S-T02 mitigation strategy design

4. **Chen, S., et al. (2021).** "Robust shadow estimation." *PRX Quantum*, 2(3), 030348.
   - Noise-aware shadows theory (v1 implementation for S-T02)
   - Predicts variance reduction from inverse channel correction

## Expected Outcomes and Success Criteria

### Primary Success Criteria

1. **Successful Hardware Execution**: Job completes without errors on IBM backend
2. **Manifest Capture**: Complete provenance including IBM calibration snapshot
3. **Observable Estimation**: Obtain estimates with confidence intervals for 3-qubit GHZ observables
4. **Runtime Compliance**: Stay within 10-minute free-tier window

### Secondary Success Criteria

1. **SSR Characterization**: Quantify performance gap vs. simulator (expect 1.1-2× vs. 17×)
2. **Noise Impact Analysis**: Compare observed vs. expected values to characterize hardware errors
3. **Calibration Metadata**: Capture T1, T2, gate errors, readout errors for future mitigation
4. **Queue Time Tracking**: Document submission-to-completion time for operational planning

### Quantitative Targets

| Metric | Target | Rationale |
|--------|--------|-----------|
| Execution Success | 100% | Must complete without errors |
| Manifest Completeness | All fields | Provenance validation |
| Observable Count | 5 (3-qubit GHZ) | Same as SMOKE-SIM |
| Runtime | < 10 minutes | Free-tier compliance |
| SSR (estimated) | 1.1-2× | Realistic noise-limited target |
| Queue Wait | < 30 minutes | Operational efficiency |

### Known Limitations

1. **Single Backend Test**: Only one IBM backend tested (ibm_fez or ibm_torino), not exhaustive
2. **Small Shot Budget**: 100 shots to minimize queue time (insufficient for high-precision SSR)
3. **No Mitigation**: v0 baseline only, no MEM/ZNE (deferred to S-T02)
4. **Limited Observables**: 3-qubit GHZ Z/ZZ only, not comprehensive state validation
5. **Single Trial**: One execution per backend, no statistical replication

## Next Steps After Completion

Upon successful completion:
1. **S-T01 Extended GHZ**: Scale up to ≥10 trials, larger shadow budgets
2. **S-T02 Noise-Aware**: Add MEM and compare v0 vs. v1 on same backend
3. **Cross-Workstream Launches**: Unblock C-T01, O-T01, B-T01, M-T01 with validated hardware access
4. **Backend Selection Refinement**: Use queue/performance data to optimize future backend choices

Upon failure or unexpected results:
1. Debug hardware integration issues before extended campaigns
2. Adjust shadow budgets or observable selection based on noise levels
3. Consider alternative backends if selected backend underperforms

## Part of Phase 1 Research Plan

This experiment is the **hardware validation gate** in the Phase 1 execution chain:

```
SMOKE-SIM ──✓──> SMOKE-HW ──────> Extended Validation
              (simulator)   (this)             │
                                               ├─> S-T01 (≥10 trials)
                                               ├─> S-T02 (MEM + v1)
                                               └─> C/O/B/M starters
```

**Phase 1 Status:**
- ✅ SMOKE-SIM: Passed (SSR=17.37×)
- 🔄 SMOKE-HW: In progress (this experiment)
- ⏳ S-T01/S-T02: Awaiting SMOKE-HW completion
- ⏳ Cross-workstream: Awaiting SMOKE-HW completion

**Risk Mitigation:** Keeping this experiment small (3 qubits, 100 shots, single trial) minimizes cost if unexpected issues arise, while still providing sufficient validation to proceed with confidence.

## Additional Considerations

### Backend Selection Criteria

For this smoke test, select IBM backend based on:
1. **Low queue depth** (prefer < 100 pending jobs)
2. **Recent calibration** (< 24 hours old)
3. **Good qubit quality** (readout error < 5%, T1 > 50 μs on target qubits)
4. **Free-tier access** (ibm_fez, ibm_marrakesh, ibm_torino, ibm_brisbane)

As of Nov 3, 2025: **ibm_fez** (77 pending jobs) is optimal.

### Operational Learning Goals

Beyond scientific validation, this experiment tests operational workflows:
- `quartumse runtime-status` CLI for queue monitoring
- Backend descriptor parsing (provider:name syntax)
- Calibration reuse vs. refresh logic
- Manifest storage and retrieval patterns
- Webhook notifications for job completion (if configured)

These operational learnings inform Phase 2 hardware campaign planning.
