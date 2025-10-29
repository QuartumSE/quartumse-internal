# QuartumSE Documentation Map

The documentation library is organised to guide you from local setup through automated experiment campaigns. Start here and then drill into the section that matches your task.

## Tutorials

- [`tutorials/quickstart.md`](tutorials/quickstart.md) – install the SDK, validate the environment, and run the S‑T01 baseline.
- [`tutorials/hardware_quickstart.md`](tutorials/hardware_quickstart.md) – configure IBM Runtime credentials and queue managed experiments.

## How-to guides

Practical walkthroughs for day-to-day operations:

- [`how-to/run-tests.md`](how-to/run-tests.md) – pytest markers, notebook validation, and hardware readiness checks.
- [`how-to/run-st01-ghz.md`](how-to/run-st01-ghz.md) – canonical GHZ baseline run with configuration tips.
- [`how-to/run-mem-v1.md`](how-to/run-mem-v1.md) – enable noise-aware shadows with MEM calibration.
- [`how-to/replay-from-manifest.md`](how-to/replay-from-manifest.md) – compute new observables from stored shot data.
- [`how-to/generate-report.md`](how-to/generate-report.md) – build HTML/PDF experiment summaries.
- [`how-to/run-automated-pipeline.md`](how-to/run-automated-pipeline.md) – orchestrate scheduled simulator + hardware runs with reporting automation.

## Explanation

Deep dives into the design and theory underpinning QuartumSE:

- [`explanation/architecture.md`](explanation/architecture.md) – component-level architecture of the estimator, connectors, and reporting stack.
- [`explanation/manifest-schema.md`](explanation/manifest-schema.md) – manifest, Parquet, and report artefact formats.
- [`explanation/shadows-theory.md`](explanation/shadows-theory.md) – theoretical background for classical shadows and mitigation strategies.

## Operations & strategy

- [`ops/runtime_runbook.md`](ops/runtime_runbook.md) – monitor IBM Runtime quota usage and coordinate on-call response.
- [`strategy/project_bible.md`](strategy/project_bible.md) – mission, positioning, and product principles.
- [`strategy/roadmap.md`](strategy/roadmap.md) – phased delivery milestones and exit criteria.
- [`strategy/phase1_task_checklist.md`](strategy/phase1_task_checklist.md) – current R&D checklist for the Phase 1 programme.

---

If you add new documentation, prefer placing it under `docs/` (either as a tutorial, how-to guide, or explanatory note) to keep the repository root tidy and the navigation coherent.

## Citing QuartumSE

When preparing publications, pull citation metadata from the repository's [`CITATION.cff`](../CITATION.cff) file via GitHub's **Cite this repository** button. This ensures the version number and release date stay aligned with the latest tagged release.

## Building the API documentation

The API reference under `docs/api/` is generated with [Sphinx](https://www.sphinx-doc.org/) and pulls docstrings directly from the Python package in `src/quartumse`.

### Prerequisites

Install the optional documentation dependencies:

**Unix/macOS:**
```bash
pip install -e .[docs]
```

**Windows:**
```powershell
pip install -e .[docs]
```

### Build steps

Use [tox](https://tox.wiki/) to build the docs and fail on warnings:

**Unix/macOS:**
```bash
tox -e docs
```

**Windows:**
```powershell
tox -e docs
```

This command runs `sphinx-build` with the `-W` and `--keep-going` flags, ensuring the documentation remains warning-free. The generated HTML lives in `docs/_build/html`.
