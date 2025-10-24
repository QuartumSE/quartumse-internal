# Runtime Budgeting Checklist Template

Use this checklist before launching any IBM Quantum workload. Populate it with
`quartumse runtime-status --json` output (which now includes a `budgeting`
section) and the planned experiment slate.

## Suggested Workflow

1. Capture runtime status:
   ```bash
   quartumse runtime-status \
     --backend ibm:ibmq_jakarta \
     --json \
     --shots-per-second 8.3 \
     --batch-seconds 600 \
     --calibration-shots 1024 \
     > runtime_status.json
   ```
2. Feed the JSON into `experiments.shadows.common_utils.load_budgeting_summary`
   (see helper below) to obtain standardized allocation notes.
3. Transcribe the summary into the YAML template and record any manual
   adjustments or fallback decisions.

## YAML Checklist Template

```yaml
runtime_budget_review:
  collected_at: <ISO8601 timestamp from payload.collected_at>
  backend: <payload.queue.backend_name>
  queue:
    pending_jobs: <payload.queue.pending_jobs>
    operational: <payload.queue.operational>
    status_msg: <payload.queue.status_msg>
  runtime_quota:
    plan: <payload.quota.plan>
    limit_seconds: <payload.quota.limit_seconds>
    remaining_seconds: <payload.quota.remaining_seconds>
    refresh_date: <payload.quota.refresh_date>
  budgeting:
    assumptions: <payload.budgeting.assumptions>
    timing: <payload.budgeting.timing>
    shot_capacity: <payload.budgeting.shot_capacity>
    fallbacks: <payload.budgeting.fallbacks>

shot_allocation:
  total_measurement_shots: <summary.total_measurement_shots>
  total_calibration_shots: <summary.total_calibration_shots>
  per_experiment:
    - name: <experiment label>
      allocated_shots: <derived via allocate_shots>
      notes: <batch ordering / grouping>

batching_strategy:
  target_window_seconds: <payload.budgeting.assumptions.batch_seconds>
  estimated_batches: <payload.budgeting.timing.estimated_batches>
  queue_checkpoint: <time to re-query runtime-status>
  batching_notes:
    - [ ] Submitted circuits grouped to respect measurement shots envelope
    - [ ] Calibration reuse verified (if measurement shots ~= payload.budgeting.shot_capacity.estimated_batch_shots)

fallback_plan:
  - trigger: <condition from payload.budgeting.fallbacks>
    action: <planned mitigation>
    owner: <on-call engineer>
  - trigger: "Runtime quota under 10%"
    action: "Trim measurement shots and re-run allocate_shots for high-priority experiments only"
```

## Markdown Checklist Variant

For teams preferring Markdown checklists, adapt the YAML above into the
following structure:

```markdown
- [ ] Runtime status captured (`runtime_status.json` attached)
- [ ] Queue depth reviewed (pending: <payload.queue.pending_jobs>)
- [ ] Remaining seconds mapped to measurement shots (<payload.budgeting.shot_capacity.measurement_shots_available>)
- [ ] Shots allocated via `allocate_shots(total_shots, n_experiments)`
- [ ] Batching window (<payload.budgeting.assumptions.batch_seconds> s) confirmed
- [ ] Fallback scenarios acknowledged:
  - <condition>: <action>
```

Keep the JSON artifact with the filled checklist so downstream analyses can
reference the same budgeting envelope.
