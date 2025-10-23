# IBM Runtime Operations Runbook

This runbook tracks IBM Quantum free-tier runtime usage and provides quick recovery paths when the quota is depleted.

## Free-tier quota snapshot

- **Monthly allocation:** 600 seconds (10 minutes) of wall-clock runtime on physical devices per calendar month under the IBM Quantum Free/Open plan.
- **Concurrency limits:** Up to **5 pending jobs** and **1 running job** per account/instance at a time. Excess submissions are rejected until the queue drains.
- **Reset schedule:** Allocation resets at 00:00 UTC on the first day of each month. Unused minutes do not roll over.

## Checking remaining runtime

### Via IBM Quantum portal

1. Sign in to <https://quantum.ibm.com>.
2. Open **My Account → Usage** and select the active hub/group/project.
3. Review the **Runtime usage** panel for remaining seconds, refresh date, and pending job caps.

### Via QuartumSE CLI (preferred for automation)

```
quartumse runtime-status --backend ibm:ibmq_brisbane --instance ibm-q/open/main
```

Key behaviours:

- The command queries queue depth, quota consumption, and refresh date using the IBM Runtime API. 【F:src/quartumse/utils/runtime_monitor.py†L44-L193】
- Pass `--json` for machine-readable output (suitable for CI dashboards).
- Provide credentials via standard environment variables (`QISKIT_IBM_TOKEN`, `QISKIT_IBM_CHANNEL`, `QISKIT_IBM_INSTANCE`) or CLI overrides.

### Notifications

- Set `QUARTUMSE_SLACK_WEBHOOK` (or pass `--slack-webhook`) to push the status summary into project chat. Use `--dry-run` during testing to avoid posting. 【F:src/quartumse/cli.py†L119-L213】
- The webhook payload includes queue depth, quota usage, and the next reset date for quick triage.

## Fallback backends when quota is exhausted

| Scenario | Immediate action | Notes |
| --- | --- | --- |
| Free-tier minutes depleted mid-sprint | Switch estimator config to `ibm:ibmq_qasm_simulator` or `aer_simulator` for continued functional work. | Simulator runs do not consume runtime quota but still validate integration paths. |
| Hardware-specific regression blocking validation | Use `qiskit.providers.fake_provider` fake backends to reproduce calibration-dependent logic without hardware access. | Capture manifests to document the simulated evidence until hardware minutes refresh. |
| Queue cap reached (max pending jobs) | Pause new submissions, monitor `quartumse runtime-status --json` until `pendingJobs < maxPendingJobs`. | CLI returns job caps from the active instance, mirroring portal data. |

## Operational cadence

- **Monthly review:** First business day of each month, review the runtime usage dashboard, confirm remaining free-tier minutes, and update fallback readiness in this runbook.
- **Weekly spot-check (Mondays):** Run `quartumse runtime-status --json` against the primary hardware backend and capture output in the team notebook to watch queue health trends.

## Incident response tips

1. If quota hits zero before reset, pivot planned hardware executions to simulator-only experiments and reschedule hardware runs after the reset date.
2. When backlog persists beyond 24 hours, escalate in the team comms channel with the webhook payload and consider re-prioritising experiments toward simulator coverage.
3. Document any quota-related delays in `STATUS_REPORT.md` for visibility during phase reviews.
