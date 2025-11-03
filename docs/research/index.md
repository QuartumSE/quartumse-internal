# Research Overview

The QuartumSE research programme coordinates experiment design, execution, and analysis across the project. Use this section to stay aligned on what is running now, which studies are coming next, and where to find background reading.

---

## 🎯 Phase 1 Research Program

**[View Phase 1 Research Plan](phase1-research-plan.md)** - Comprehensive overview of Phase 1 experiments, timelines, exit criteria, and workstream integration.

**[View Experiment Index](experiments/index.md)** - Master index of all experiments with status dashboard and quick navigation.

### Progress Dashboard

**Status:** Phase 1 Foundation & R&D (Nov 2025)
**Experiments:** 3 completed ✅ | 8 planned 📋 | 11 total
**Coverage:** 27% complete | All 5 workstreams active

---

## 📊 Completed Experiments

| ID | Name | Status | Key Result | Date |
|----|------|--------|------------|------|
| [SMOKE-SIM](experiments/S/SMOKE-SIM/) | Simulator Smoke Test | ✅ | SSR = 17.37× | Nov 3, 2025 |
| [SMOKE-HW](experiments/S/SMOKE-HW/) | Hardware Smoke Test | ✅ | ibm_fez validated | Nov 3, 2025 |
| [C-T01](experiments/C/C-T01/) | H₂ Chemistry | ✅ | Phase 1 data drop | Nov 3, 2025 |

**Quick Links:**
- [SMOKE-SIM Results](experiments/S/SMOKE-SIM/03-results-analysis.md) - 17.37× shot savings ratio
- [SMOKE-HW Hardware Analysis](experiments/S/SMOKE-HW/03-results-analysis.md) - ibm_fez backend validation
- [C-T01 H₂ Analysis](experiments/C/C-T01/03-results-analysis.md) - 12-term Hamiltonian, 300 shadows

---

## 📋 Planned Experiments

### Critical Priority (Phase 1 Blockers)
- **[S-T01](experiments/S/S-T01/)** - Extended GHZ Validation (SSR ≥ 1.1× target)
- **[S-T02](experiments/S/S-T02/)** - Noise-Aware GHZ with MEM (v0 vs v1)

### High Priority (Phase 1 Targets)
- **[O-T01](experiments/O/O-T01/)** - QAOA MAX-CUT (optimization workstream)

### Medium Priority (Phase 1 Breadth)
- **[S-BELL](experiments/S/S-BELL/)** - Parallel Bell Pairs (multi-subsystem)
- **[S-CLIFF](experiments/S/S-CLIFF/)** - Random Clifford (general states)
- **[S-ISING](experiments/S/S-ISING/)** - Ising Chain Trotter (Hamiltonian sim)
- **[B-T01](experiments/B/B-T01/)** - RB/XEB Benchmarking (device characterization)

### Low Priority (Phase 1 Exploratory)
- **[M-T01](experiments/M/M-T01/)** - GHZ Phase Sensing (metrology)

**View All:** [Complete Experiment Index](experiments/index.md)

---

## Experiment Roadmap

- Review the [QuartumSE roadmap](../strategy/roadmap.md) for phase-by-phase milestones.
- Track execution progress with the [experiment tracker](experiment-tracker.md) and detailed [strategy artifacts](../strategy/phase1_task_checklist.md).

## Experiment Operations

- Consult the [S-T01 GHZ guide](../how-to/run-st01-ghz.md) for the baseline validation path.
- Automate campaigns via the [pipeline how-to](../how-to/run-automated-pipeline.md) and [IBM Runtime runbook](../ops/runtime_runbook.md).

## Theory & Data Models

- Dive into the [Shadows theory primer](../explanation/shadows-theory.md) and the [manifest schema](../explanation/manifest-schema.md) that underpins experiment provenance.
- Compare simulator and hardware reference datasets with the [Phase 1 reference runs playbook](../strategy/phase1_reference_runs.md).

## Literature Library

- Start with the curated [literature list](literature.md) for publications that inform QuartumSE.
- Cross-reference findings with the [Project Bible](../strategy/project_bible.md) to understand how research insights feed into product decisions.

## Collaborate

- Share open questions or propose new studies through the [community hub](../community/community-hub.md).
- Highlight notable results by contributing summaries to the [partnerships and use cases board](../community/partnerships.md).
