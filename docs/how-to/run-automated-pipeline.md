# Automated Experiment Pipeline (Phase-1)

The Phase-1 pipeline automates the reproducible baseline → shadows v0 → shadows v1
runs, aggregates metrics, and emits artefacts that can be replayed later. Use this
guide when you need to run, extend, or debug the `experiments/pipeline` package.

## Metadata schema

`experiments/pipeline/metadata_schema.py` defines the structured metadata that every
pipeline run consumes. Provide the fields below in YAML or JSON (see
`experiments/shadows/examples/extended_ghz/experiment_metadata.yaml` for a template):

| Field | Type | Purpose |
| --- | --- | --- |
| `experiment` | string | Human-readable experiment name that is echoed in manifests and reports. |
| `context` | string | One-paragraph background describing why the run exists. |
| `aims` | list[string] | Bullet points for the primary questions the run answers. |
| `success_criteria` | list[string] | Quantitative exit checks (used to infer default targets). |
| `methods` | list[string] | High-level procedure summary for provenance. |
| `budget.total_shots` | int | **Equal-budget anchor:** total shots to spend per approach (baseline, v0, v1). |
| `budget.calibration.shots_per_state` | int | Shots to allocate to each computational-basis state during MEM calibration. |
| `budget.calibration.total` | int | Total calibration shots (must equal `shots_per_state * 2^n`). |
| `budget.v0_shadow_size` | int | Measurement budget for the Phase-1 shadows v0 reference. |
| `budget.v1_shadow_size` | int | Measurement budget for the Phase-1 shadows v1 + MEM run (not including calibration shots). |
| `device` | string | Default backend descriptor (e.g. `aer_simulator` or `ibm:ibm_brisbane`). |
| `discussion_template` | string | Markdown template pre-populated in the generated HTML report. |
| `num_qubits` | int (optional) | Override for inferred qubit count (normally derived from the calibration budget). |
| `targets` | map[string, number] (optional) | Explicit metric thresholds (`ssr_average`, `ci_coverage`, etc.). |
| `ground_truth` | mapping (optional) | Observable → expectation pairs for MAE/CI/SSR calculations. |

> **Tip:** Leave `targets` blank if the success criteria already specify SSR/CI
thresholds—`run_full_pipeline.py` automatically parses numbers from those strings.

## Phase-1 equal-budget rules

Phase-1 comparisons assume every approach consumes the **same total shot budget**
and distributes resources uniformly across observables:

- Stage 1 (direct Pauli baseline) divides `budget.total_shots` evenly across the
  stabiliser observables using `_allocate_shots` in
  `experiments/pipeline/_runners.py`.
- Stage 2 (`ShadowVersion.V0_BASELINE`) records the exact `budget.v0_shadow_size`
  measurements with mitigation disabled.
- Stage 3 (`ShadowVersion.V1_NOISE_AWARE`) spends `budget.v1_shadow_size` on
  measurement shots and reuses calibration snapshots so that
  `calibration.total + v1_shadow_size = budget.total_shots`.
- The analysis layer (`experiments/pipeline/analyzer.py`) uses the equal-budget
  metrics from `src/quartumse/utils/metrics.py` (`compute_mae`, `compute_ci_coverage`,
  and `compute_ssr_equal_budget`) that treat each observable with uniform weight.

Violating the equal-budget assumption (for example, by changing the shot allocator
or by skipping calibration reuse) invalidates SSR/CI comparisons, so keep the
metadata and runner defaults aligned when you extend the pipeline.

## Calibration reuse and refresh windows

The pipeline and CLI share the `ReadoutCalibrationManager` so that measurement error
mitigation (MEM) snapshots are only regenerated when required:

**Unix/macOS:**
```bash
# Reuse cached confusion matrices unless forced or stale
quartumse calibrate-readout \
  --backend ibm:ibm_brisbane \
  --qubit 0 --qubit 1 --qubit 2 --qubit 3 \
  --shots 256 \
  --output-dir validation_data/calibrations \
  --max-age-hours 6
```

**Windows:**
```powershell
# Reuse cached confusion matrices unless forced or stale
quartumse calibrate-readout `
  --backend ibm:ibm_brisbane `
  --qubit 0 --qubit 1 --qubit 2 --qubit 3 `
  --shots 256 `
  --output-dir validation_data/calibrations `
  --max-age-hours 6
```

Key behaviours (`src/quartumse/cli.py`):

- **Reuse by default:** `ensure_calibration` returns cached matrices and marks the
  manifest as `"reused": true` when the existing artefact matches the qubit set and
  backend descriptor.
- **`--max-age-hours`:** Provide a float to refresh calibrations that are older than
  the allowed window. Pass `--force` to ignore age checks entirely.
- **Manifest trail:** Each calibration writes `<confusion>.manifest.json` alongside
  the `.npz`, recording backend version, shot counts, and reuse flags for provenance.

The automated pipeline (`experiments/pipeline/executor.py`) points its calibration
manager at `<output>/calibrations/` so reruns in the same directory automatically
reuse MEM artefacts as long as the age/force constraints permit.

## Running the CLI pipeline

Use the `run_full_pipeline.py` entrypoint to execute the three stages, verify
artefacts, and render a report.

### Simulator (Aer)

**Unix/macOS:**
```bash
python -m experiments.pipeline.run_full_pipeline \
  --metadata experiments/shadows/examples/extended_ghz/experiment_metadata.yaml \
  --output validation_data/pipeline_runs/ghz4_aer \
  --backend aer_simulator
```

**Windows:**
```powershell
python -m experiments.pipeline.run_full_pipeline `
  --metadata experiments/shadows/examples/extended_ghz/experiment_metadata.yaml `
  --output validation_data/pipeline_runs/ghz4_aer `
  --backend aer_simulator
```

- Produces manifests under `validation_data/pipeline_runs/ghz4_aer/manifests/`.
- Stores calibration artefacts in `validation_data/pipeline_runs/ghz4_aer/calibrations/`.
- Writes the result digest (`result_hash.txt`), analysis summary, and HTML report to the
  same directory.

### IBM Quantum hardware

**Unix/macOS:**
```bash
export QISKIT_IBM_TOKEN="<your-runtime-token>"
python -m experiments.pipeline.run_full_pipeline \
  --metadata experiments/shadows/examples/extended_ghz/experiment_metadata.yaml \
  --output data/pipeline_runs/ghz4_kyoto \
  --backend ibm:ibm_kyoto
```

**Windows (PowerShell):**
```powershell
$env:QISKIT_IBM_TOKEN="<your-runtime-token>"
python -m experiments.pipeline.run_full_pipeline `
  --metadata experiments/shadows/examples/extended_ghz/experiment_metadata.yaml `
  --output data/pipeline_runs/ghz4_kyoto `
  --backend ibm:ibm_kyoto
```

**Windows (Command Prompt):**
```cmd
set QISKIT_IBM_TOKEN=<your-runtime-token>
python -m experiments.pipeline.run_full_pipeline ^
  --metadata experiments/shadows/examples/extended_ghz/experiment_metadata.yaml ^
  --output data/pipeline_runs/ghz4_kyoto ^
  --backend ibm:ibm_kyoto
```

- Set `QISKIT_RUNTIME_API_TOKEN`/`QISKIT_IBM_CHANNEL`/`QISKIT_IBM_INSTANCE` if your hub
  requires them (see `quartumse connect ibm` hints in `src/quartumse/cli.py`).
- Hardware runs honour the same equal-budget accounting—MEM calibration shots are
  deducted from the total and reused when possible.
- The output directory is Git-ignored; move final manifests to `data/manifests/` when
  publishing results.

To override the backend encoded in the metadata file, pass a different `--backend`
value. Omit the flag to use `metadata.device` as-is.

## Artefacts and replay workflow

After a pipeline run completes, inspect the output directory:

**Unix/macOS:**
```bash
ls -R validation_data/pipeline_runs/ghz4_aer
cat validation_data/pipeline_runs/ghz4_aer/report_*.html | head
```

**Windows:**
```powershell
Get-ChildItem -Recurse validation_data/pipeline_runs/ghz4_aer
Get-Content validation_data/pipeline_runs/ghz4_aer/report_*.html | Select-Object -First 10
```

You should see:

- `manifests/` – baseline, v0, and v1 JSON manifests (Stage 1–3).
- `calibrations/` – MEM confusion matrices plus `.manifest.json` metadata (only when
  Phase-1 runs require mitigation).
- `analysis_<hash>.json` – Aggregated metrics (`ssr_average`, `ci_coverage`, MAE) and
  target evaluation flags.
- `report_<hash>.html` – Full Phase-1 report ready for review or screenshots.
- `result_hash.txt` – Stable digest derived from the manifest payloads.

Replaying artefacts does not require backend access:

**Unix/macOS:**
```bash
# Regenerate the HTML report after editing metadata or narrative sections
quartumse report validation_data/pipeline_runs/ghz4_aer/manifests/<manifest>.json \
  --output validation_data/pipeline_runs/ghz4_aer/replay_report.html

# Programmatic replay: recompute observables from saved manifests
python - <<'PY'
from quartumse.estimator import ShadowEstimator
from quartumse.reporting.manifest import ProvenanceManifest

manifest_path = "validation_data/pipeline_runs/ghz4_aer/manifests/<manifest>.json"
manifest = ProvenanceManifest.from_json(manifest_path)
estimator = ShadowEstimator.replay_from_manifest(manifest)
print(estimator)
PY
```

**Windows:**
```powershell
# Regenerate the HTML report after editing metadata or narrative sections
quartumse report validation_data/pipeline_runs/ghz4_aer/manifests/<manifest>.json `
  --output validation_data/pipeline_runs/ghz4_aer/replay_report.html

# Programmatic replay: recompute observables from saved manifests
python -c "from quartumse.estimator import ShadowEstimator; from quartumse.reporting.manifest import ProvenanceManifest; manifest_path = 'validation_data/pipeline_runs/ghz4_aer/manifests/<manifest>.json'; manifest = ProvenanceManifest.from_json(manifest_path); estimator = ShadowEstimator.replay_from_manifest(manifest); print(estimator)"
```

The verifier stage (`experiments/pipeline/verifier.py`) checks that shot files and MEM
confusion matrices still exist and match their checksums. If you relocate artefacts,
update `manifest.schema.shot_data_path` or keep the directory layout intact so replay
continues to pass.

---

Need more automation? Extend `experiments/pipeline/executor.py` with new stages, but
keep the metadata schema and equal-budget invariants intact so downstream analysis and
reports remain comparable.
