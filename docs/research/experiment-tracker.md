# Experiment Tracker

Use this tracker to align the community on upcoming, active, and recently completed experiments.

## Active Campaigns

| Experiment | Goal | Status | Links |
|------------|------|--------|-------|
| S-T01 / S-T02 GHZ | Validate classical shadows metrics against Phase 1 exit criteria. | Running | [Tutorial](../how-to/run-st01-ghz.md) · [Reports](../how-to/generate-report.md) |
| MEM v1 calibration | Capture mitigation matrices and evaluate MEM accuracy. | Preparing | [Runbook](../how-to/run-mem-v1.md) · [Manifest schema](../explanation/manifest-schema.md) |
| Automated pipeline | Automate multi-stage experiment execution with provenance capture. | In validation | [Pipeline how-to](../how-to/run-automated-pipeline.md) · [Runtime runbook](../ops/runtime_runbook.md) |

## Upcoming Studies

- **Cross-workstream starter experiments:** Follow the [roadmap milestones](../strategy/roadmap.md#phase-1-foundation) to queue the C/O/B/M baselines.
- **Experiment reproducibility tests:** Coordinate with the [test suite guide](../how-to/run-tests.md) to backfill automation coverage.

## Recently Completed

- **Hardware smoke tests:** See the [strategic review update](../strategy/strategic_review_2025_10_30.md#execution-summary) for the latest hardware findings.
- **Reference datasets:** Compare baseline runs in the [Phase 1 reference runs guide](../strategy/phase1_reference_runs.md).

## Contribution Workflow

1. Draft the study plan in the relevant experiment subdirectory under `experiments/`.
2. Link the proposal to supporting materials in the [literature library](literature.md).
3. Announce the experiment in the [community hub](../community/community-hub.md) to recruit reviewers.
4. After execution, archive manifests, reports, and discussions per the [Phase 1 checklist](../strategy/phase1_task_checklist.md).
