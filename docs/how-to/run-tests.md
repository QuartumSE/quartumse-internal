# Run QuartumSE Tests

This guide explains how to exercise the automated test suites, when to run
hardware checks, and which notebooks provide manual validation coverage.  It
replaces the older `TESTING_GUIDE.md` marketing summary with a concise workflow
reference.

## Test matrix overview

| Layer        | Marker(s)                 | Purpose                               |
|--------------|---------------------------|---------------------------------------|
| Unit         | *(default)*               | Fast logic tests for shadows, manifests, and utilities |
| Integration  | `integration`             | Exercising estimator + storage pipelines on simulators |
| Slow         | `slow`                    | Longer-running variance/CI checks     |
| Hardware     | `hardware`                | Requires IBM Quantum credentials and quota |

Tests use `pytest` markers so you can opt into the heavier scenarios as needed.

## Running the suites

**Unix/macOS:**
```bash
# Core unit tests (quick feedback)
pytest tests/unit -v

# Fast integration matrix (skip slow + hardware markers)
pytest tests -m "not slow and not hardware" -v

# Include slow scenarios (still skip hardware)
pytest tests -m "not hardware" -v --durations=20

# Hardware runs (requires QISKIT_IBM_TOKEN, see ../ops/runtime_runbook.md)
pytest tests -m hardware -v
```

**Windows:**
```powershell
# Core unit tests (quick feedback)
pytest tests/unit -v

# Fast integration matrix (skip slow + hardware markers)
pytest tests -m "not slow and not hardware" -v

# Include slow scenarios (still skip hardware)
pytest tests -m "not hardware" -v --durations=20

# Hardware runs (requires QISKIT_IBM_TOKEN, see ../ops/runtime_runbook.md)
pytest tests -m hardware -v
```

Enable coverage reporting (mirrors the CI configuration) when preparing releases:

**Unix/macOS:**
```bash
pytest --cov --cov-report=term-missing --cov-report=xml --cov-report=html
```

**Windows:**
```powershell
pytest --cov --cov-report=term-missing --cov-report=xml --cov-report=html
```

This writes `coverage.xml` for Codecov uploads and an `htmlcov/` directory for
annotated source review.

## Manual validation notebooks

Three curated notebooks cover the major user journeys:

- `notebooks/quickstart_shot_persistence.ipynb` – GHZ classical shadows demo
  with manifest + Parquet replay.
- `notebooks/noise_aware_shadows_demo.ipynb` – MEM-enhanced (v1) workflow and
  confusion-matrix diagnostics.
- `notebooks/comprehensive_test_suite.ipynb` – End-to-end path combining CLI,
  replay, and reporting.

The notebooks folder now contains only the actively maintained tutorials so new
users can focus on the recommended path. Historical experiments have been
retired from version control to keep the repo lightweight.

## Experiment scripts

The active experiment scripts are under `experiments/shadows/` and
`experiments/validation/`.  Legacy scaffolds were removed during the repo
cleanup, so everything under `experiments/` is production-supported. The S‑T01
GHZ baseline remains the canonical CLI example:

**Unix/macOS:**
```bash
python experiments/shadows/S_T01_ghz_baseline.py --backend aer_simulator
```

**Windows:**
```powershell
python experiments/shadows/S_T01_ghz_baseline.py --backend aer_simulator
```

Pass `--backend ibm:<device>` to exercise the IBM Runtime integration.  Hardware
runs automatically persist manifests and shot data under `data/`.

## Hardware readiness checklist

Before running the `hardware` test marker or the CLI against real backends:

1. Export `QISKIT_IBM_TOKEN` (and optional instance overrides).
2. Ensure `qiskit-ibm-runtime` is installed (`pip install qiskit-ibm-runtime` or `pip install quartumse[mitigation]`).
3. Confirm remaining quota via `quartumse runtime-status`.
4. Schedule runs inside the free-tier 10 minute window.  See the
   [IBM Runtime runbook](../ops/runtime_runbook.md) for quota guidance and
   webhook notifications.

## Troubleshooting tips

- **Missing optional dependencies** – install `quartumse[dev,mitigation]` to
  enable MEM notebooks and tests.
- **Runtime quota errors** – rerun on the Aer simulator or wait for the next
  monthly reset; manifests still capture simulated evidence.
- **Inconsistent notebook output** – clear previous artifacts under
  `notebook_data/` or supply a unique `data_dir` when instantiating
  `ShadowEstimator`.

For a broader program view, pair this document with the updated
[Project Bible](../strategy/project_bible.md) and
[Roadmap](../strategy/roadmap.md).
