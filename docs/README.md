# QuartumSE Documentation Map

The documentation has been reorganised to keep the root directory lean and to
highlight the most up-to-date sources of truth.  Start with the sections below
when exploring the project.

## Tutorials

- [`tutorials/quickstart.md`](tutorials/quickstart.md) – environment setup,
  installation options, and first experiments.
- [`tutorials/hardware_quickstart.md`](tutorials/hardware_quickstart.md) –
  minimum hardware configuration steps for IBM Quantum backends.

## How-to

- [`how-to/run-tests.md`](how-to/run-tests.md) – pytest markers, notebook
  validation, and hardware readiness checks.
- **Pipeline guide** – Phase-1 automated experiment pipeline usage, calibration
  reuse, and replay workflow (legacy location under *Guides → Pipeline*).

## Explanation

- [`explanation/manifest-schema.md`](explanation/manifest-schema.md) – manifest,
  Parquet, and report artefact formats.

## Operations & strategy

- [`ops/runtime_runbook.md`](ops/runtime_runbook.md) – monitoring IBM Runtime
  quota usage and posting Slack alerts.
- [`strategy/project_bible.md`](strategy/project_bible.md) – long-term vision and
  positioning.
- [`strategy/roadmap.md`](strategy/roadmap.md) – phased delivery milestones.

## Archives

Historical planning artefacts remain available for reference but are no longer
considered active documentation:

- [`archive/bootstrap_summary_20251020.md`](archive/bootstrap_summary_20251020.md)
- [`archive/status_report_20251022.md`](archive/status_report_20251022.md)
- [`archive/strategic_analysis_20251021.md`](archive/strategic_analysis_20251021.md)

These files capture the October 2025 bootstrap and validation updates.  Link to
this archive only when the historical context is required.

---

If you add new documentation, prefer placing it under `docs/` (either as a new
guide or alongside the strategic/ops material) to keep the repository root tidy.

## Citing QuartumSE

When preparing publications, pull citation metadata from the repository's
[`CITATION.cff`](../CITATION.cff) file via GitHub's **Cite this repository**
button. This ensures the version number and release date stay aligned with the
latest tagged release.

## Building the API documentation

The API reference under `docs/api/` is generated with [Sphinx](https://www.sphinx-doc.org/)
and pulls docstrings directly from the Python package in `src/quartumse`.

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

This command runs `sphinx-build` with the `-W` and `--keep-going` flags, ensuring the
documentation remains warning-free.  The generated HTML lives in `docs/_build/html`.
