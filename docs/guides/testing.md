# Testing QuartumSE

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

```bash
# Core unit tests (quick feedback)
pytest tests/unit -v

# Fast integration matrix (skip slow + hardware markers)
pytest tests -m "not slow and not hardware" -v

# Include slow scenarios (still skip hardware)
pytest tests -m "not hardware" -v --durations=20

# Hardware runs (requires QISKIT_IBM_TOKEN, see docs/ops/runtime_runbook.md)
pytest tests -m hardware -v
```

Enable coverage reporting (mirrors the CI configuration) when preparing releases:

```bash
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

Archived or superseded notebooks now live under `notebooks/archive/` to keep the
entry points focused.

## Experiment scripts

The active experiment scripts are under `experiments/shadows/` and
`experiments/validation/`.  Additional scaffolds for chemistry, optimization,
and metrology have been moved to `experiments/archive/` until they are fully
implemented.  The S‑T01 GHZ baseline remains the canonical CLI example:

```bash
python experiments/shadows/S_T01_ghz_baseline.py --backend aer_simulator
```

Pass `--backend ibm:<device>` to exercise the IBM Runtime integration.  Hardware
runs automatically persist manifests and shot data under `data/`.

## Hardware readiness checklist

Before running the `hardware` test marker or the CLI against real backends:

1. Export `QISKIT_IBM_TOKEN` (and optional instance overrides).
2. Ensure `qiskit-ibm-runtime` is installed (`pip install qiskit-ibm-runtime` or `pip install quartumse[mitigation]`).
3. Confirm remaining quota via `quartumse runtime-status`.
4. Schedule runs inside the free-tier 10 minute window.  See
   [`docs/ops/runtime_runbook.md`](../ops/runtime_runbook.md) for quota guidance
   and webhook notifications.

## Troubleshooting tips

- **Missing optional dependencies** – install `quartumse[dev,mitigation]` to
  enable MEM notebooks and tests.
- **Runtime quota errors** – rerun on the Aer simulator or wait for the next
  monthly reset; manifests still capture simulated evidence.
- **Inconsistent notebook output** – clear previous artifacts under
  `notebook_data/` or supply a unique `data_dir` when instantiating
  `ShadowEstimator`.

For a broader program view, pair this document with the updated
[`docs/strategy/project_bible.md`](../strategy/project_bible.md) and
[`docs/strategy/roadmap.md`](../strategy/roadmap.md).
