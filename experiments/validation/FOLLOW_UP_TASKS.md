# Hardware Validation Follow-up Task Board

These tasks decompose the open follow-up work identified after the fixed-shot hardware validation refactor. Each task is framed so an assignee can execute it without revisiting the prior review context.

## Task 1 — Bind Baseline Runs to the Resolved Backend
- **Objective:** Guarantee the baseline direct-measurement workflow always executes on the same IBM backend resolved for the experiment, preserving hardware noise effects.
- **Deliverables:**
  - Unit/integration test (or dry-run harness) demonstrating baseline circuits submit via the resolved backend handle.
  - Updated documentation in `HARDWARE_VALIDATION_DESIGN.md` noting the backend-binding requirement.
- **Key Steps:**
  1. Audit `run_baseline_measurement` to confirm backend usage throughout transpilation and job submission.
  2. Add guardrails (assertions or logging) that surface if a local simulator or default sampler is used instead of the resolved backend.
  3. Backfill tests or script outputs verifying the backend name in baseline execution logs.
- **Dependencies:** Access to IBM runtime primitives (can be mocked if hardware access is unavailable).

## Task 2 — Expose Estimator Metadata on `EstimationResult`
- **Objective:** Provide experiment metadata (experiment IDs, manifest paths, shot data URIs) directly on `EstimationResult` so downstream scripts avoid fragile attribute checks.
- **Deliverables:**
  - Extended dataclass or return schema within `ShadowEstimator` that includes `experiment_id`, `manifest_path`, and `shot_data_path` fields.
  - Updated serialization logic and documentation reflecting the new metadata contract.
- **Key Steps:**
  1. Inspect the current `EstimationResult` definition in `src/quartumse/...` and extend it with the missing properties.
  2. Update all estimator implementations and tests to populate the new fields.
  3. Refactor consumers (e.g., `hardware_validation.py`) to rely on the explicit attributes without `getattr` fallbacks.
- **Dependencies:** Awareness of existing estimator interfaces and downstream usage in the repository.

## Task 3 — Keep SSR Metrics Shot-Budget Accurate
- **Objective:** Ensure Shot Savings Ratio (SSR) calculations consistently incorporate calibration overhead so comparisons remain fair under the fixed 5,000-shot budget.
- **Deliverables:**
  - Regression tests covering SSR calculations with and without calibration overhead.
  - Documentation updates clarifying how calibration shots factor into SSR reporting.
- **Key Steps:**
  1. Review `compute_metrics` and any other SSR utilities to confirm `total_shots` includes calibration.
  2. Add automated tests (e.g., pytest) that fail if calibration shots are omitted from SSR math.
  3. Update the experiment design document with explicit SSR computation examples using total shots.
- **Dependencies:** Metric utilities in `src/quartumse/utils/metrics.py` and test infrastructure.

## Task 4 — Enforce Backend Circuit-Batch Limits for Shadows
- **Objective:** Prevent classical shadow submissions from exceeding backend experiment limits by chunking large shadow batches when necessary.
- **Deliverables:**
  - Logic in `run_shadows_experiment` (or underlying estimator) that queries `backend.configuration().max_experiments` (or runtime equivalent) and batches shadow circuits accordingly.
  - Tests or dry-run evidence showing batching kicks in when `shadow_size` exceeds backend limits.
  - Updated design documentation noting the batching strategy and any latency implications.
- **Key Steps:**
  1. Determine the relevant backend property for circuit limits in IBM Runtime.
  2. Implement batching/loop submission for shadows runs while preserving manifest aggregation.
  3. Validate that metrics aggregation still uses the full 5,000-shot dataset post-batching.
- **Dependencies:** Access to backend configuration APIs and estimator batching capabilities.

## Task 5 — Protect IBM Credentials in Documentation
- **Objective:** Remove any hard-coded IBM Quantum tokens from shared artifacts and codify the process for handling credentials safely.
- **Deliverables:**
  - Sanitised documentation with placeholders where tokens previously appeared.
  - Contributor guidance (e.g., in `CONTRIBUTING.md` or `SETUP.md`) describing secure credential storage.
  - Optional: add lint or pre-commit checks for patterns resembling IBM tokens.
- **Key Steps:**
  1. Audit repository history and current docs for accidental token exposure.
  2. Replace sensitive strings with placeholders and add environment-variable instructions.
  3. Document the credential handling policy and optionally enforce it via tooling.
- **Dependencies:** Coordination with security/compliance stakeholders if formal policies exist.

## Task 6 — Monitor Backend Queue and Access Assumptions
- **Objective:** Keep operational assumptions (free-tier runtime minutes, queue strategy, backend availability) current so the validation plan remains executable.
- **Deliverables:**
  - Living checklist or operational runbook capturing queue monitoring steps and fallback plans.
  - Scheduled review cadence (e.g., monthly) recorded in the roadmap or project tracker.
  - Optional alerting mechanism for IBM account usage thresholds.
- **Key Steps:**
  1. Document the current 10-minute/month allocation and the monitoring method for consumption.
  2. Establish fallback backends or rescheduling criteria if `ibm_torino` becomes unavailable.
  3. Integrate the monitoring checklist into the broader project plan (roadmap/status reports).
- **Dependencies:** Access to IBM account usage dashboards and project management tooling.

