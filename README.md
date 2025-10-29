# QuartumSE

**Vendor-neutral classical shadows with built-in provenance and reporting**

[![CI](https://github.com/quartumse/quartumse/workflows/CI/badge.svg)](https://github.com/quartumse/quartumse/actions)
[![Coverage](https://codecov.io/gh/quartumse/quartumse/branch/main/graph/badge.svg)](https://codecov.io/gh/quartumse/quartumse)
[![Docs](https://github.com/quartumse/quartumse/actions/workflows/ci.yml/badge.svg?branch=main&job=docs)](https://github.com/quartumse/quartumse/actions/workflows/ci.yml?query=branch%3Amain+workflow%3ACI+job%3Adocs)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

QuartumSE delivers a measurement layer that is **shot-efficient, auditable,** and **vendor-neutral**. The SDK combines classical shadows (v0 baseline and v1 noise-aware variants), provenance manifests, and automated reporting so that you can move from simulator validation to hardware experiments with a single workflow.

> ⚠️ **Phase 1 R&D:** APIs are evolving rapidly. Expect breaking changes while we harden the estimator and reporting stacks.

---

## Why QuartumSE?

- **Shot-efficiency:** Estimate many observables from a shared classical shadow instead of re-running circuits.
- **Provenance-first:** Every experiment emits machine-readable manifests, Parquet shot data, and human-readable reports.
- **Noise-aware:** Optional measurement mitigation (MEM) and calibration capture keep hardware experiments trustworthy.
- **Automation-friendly:** CLI tooling, reproducible configs, and reporting pipelines support continuous experiment campaigns.

---

## Quickstart (10 minutes)

1. **Clone and create an environment**

   ```bash
   git clone https://github.com/quartumse/quartumse.git
   cd quartumse
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. **Install the SDK**

   ```bash
   python -m pip install --upgrade pip
   pip install -e ".[dev]"  # include pytest, black, ruff, mypy, jupyter
   ```

3. **Smoke test the CLI and estimator**

   ```bash
   quartumse --help
   python -c "from quartumse import ShadowEstimator; print('QuartumSE ready')"
   pytest tests -m "not slow and not hardware" -v
   ```

4. **Run the GHZ baseline experiment on Aer**

   ```bash
   python experiments/shadows/S_T01_ghz_baseline.py --backend aer_simulator
   ```

   The script prints observable estimates with confidence intervals and writes manifests + Parquet shot data to `data/` for replay and reporting.

5. **Replay with new observables**

   ```python
   from quartumse import ShadowEstimator
   from quartumse.shadows.core import Observable

   estimator = ShadowEstimator(backend="aer_simulator")
   replay = estimator.replay_from_manifest(
       "data/manifests/<manifest-id>.json",
       observables=[Observable("XXX")],
   )
   ```

Ready for hardware? Follow the [hardware quickstart](docs/tutorials/hardware_quickstart.md) to configure IBM Runtime credentials and run the same script on managed backends.

---

## Guided learning path

| Step | Goal | Resource |
|------|------|----------|
| 1 | Understand the workflow end-to-end | `notebooks/quickstart_shot_persistence.ipynb` |
| 2 | Compare v0 vs v1 shadows with mitigation | `notebooks/noise_aware_shadows_demo.ipynb` |
| 3 | Exercise the full estimator + reporting stack | `notebooks/comprehensive_test_suite.ipynb` |
| 4 | Automate runs and reporting | [Automated pipeline how-to](docs/how-to/run-automated-pipeline.md) |
| 5 | Deep-dive into manifests and data products | [Manifest schema explainer](docs/explanation/manifest-schema.md) |

Each notebook writes demo artefacts to `demo_data/` or `notebook_data/`, keeping the main `data/` tree reserved for production experiments.

---

## Features at a glance

### Classical shadows

- **v0 Baseline:** Random local Clifford measurements with post-processing.
- **v1 Noise-aware:** Measurement error mitigation (MEM) + calibration capture.
- **Replay:** Compute additional observables from stored shot data without re-executing circuits.

### Provenance + reporting

- JSON manifests: circuits, calibration snapshots, seeds, software versions.
- Parquet shot data: bitstrings, basis frequencies, per-qubit statistics.
- HTML/PDF experiment reports: automatically generated summaries and diagnostics.
- Cost-for-accuracy metrics: SSR (shot-savings ratio) and RMSE@$.

### Automation

- CLI entry points (`quartumse run`, experiment scripts) with config-driven execution.
- Reporting pipeline that stitches manifests, diagnostics, and metrics into shareable artefacts.
- Validation suite with pytest markers for fast, slow, and hardware-specific checks.

---

## Repository tour

```
quartumse/
├── src/quartumse/            # Estimator, classical shadows, mitigation, reporting
├── experiments/              # Reproducible experiment scripts + validation harnesses
├── notebooks/                # Guided tutorials and validation walkthroughs
├── docs/                     # Tutorials, how-to guides, reference, operations, strategy
├── tests/                    # Pytest suites (unit, integration, hardware)
├── tools/                    # Development scripts (lint, release helpers)
├── data*/                    # Experiment outputs (gitignored)
├── validation_data*/         # Validation artefacts (gitignored)
└── demo_data*/               # Notebook/demo artefacts (gitignored)

*Created on demand and ignored by Git.
```

Key experiment entry points:

```bash
# Classical shadows GHZ baseline (v0/v1)
python experiments/shadows/S_T01_ghz_baseline.py --backend aer_simulator

# Noise-aware validation sweep
python experiments/validation/hardware_validation.py
```

---

## Documentation index

- **Quickstart:** [docs/tutorials/quickstart.md](docs/tutorials/quickstart.md)
- **Hardware setup:** [docs/tutorials/hardware_quickstart.md](docs/tutorials/hardware_quickstart.md)
- **Automation guides:** [`docs/how-to/`](docs/how-to)
- **Architecture & theory:** [`docs/explanation/`](docs/explanation)
- **Operations:** [`docs/ops/`](docs/ops)
- **Roadmap & strategy:** [`docs/strategy/`](docs/strategy)

Browse the full site at [https://quartumse.github.io/quartumse](https://quartumse.github.io/quartumse).

---

## Testing & quality gates

We rely on `pytest` with coverage, static analysis, and type checking to keep the codebase production-ready.

```bash
# Fast tests (default in CI)
pytest tests/ -m "not slow and not hardware"

# Full simulator + hardware suite (requires credentials)
pytest tests/ -m "not slow"

# Format, lint, type check
black src/ tests/
ruff check src/ tests/
mypy src/quartumse
```

Install `pre-commit` hooks to run formatting and linting before each commit:

```bash
pre-commit install
pre-commit run --all-files
```

---

## Roadmap snapshot

| Phase | Focus | Key milestone | Target |
|-------|-------|---------------|--------|
| **P1** | Foundation & R&D | First IBM runs + Shadows v1 | **Nov 2025** |
| **P2** | Hardware iteration | IBM campaign #1 + provisional patents | **Dec 2025** |
| **P3** | Internal validation | SSR ≥ 1.5× + journal submissions | **Mar 2026** |
| **P4** | Early Access | 2–3 partners + AWS Braket integration | **Jun 2026** |
| **P5** | Public Beta | v1.0 + pilot deployments | **Sep 2026** |

See [docs/strategy/roadmap.md](docs/strategy/roadmap.md) for the detailed plan and milestone criteria.

---

## Contributing & community

QuartumSE is in **closed R&D** until Phase 3 (Q1 2026). External contributions are paused while we stabilise the core APIs, but feedback is welcome through issues and discussions.

- Review the [Code of Conduct](CODE_OF_CONDUCT.md) and [contribution guidelines](CONTRIBUTING.md).
- File ideas or bug reports via [GitHub Issues](https://github.com/quartumse/quartumse/issues).

---

## License & citation

- **License:** [Apache 2.0](LICENSE)
- **Citation:** Export BibTeX or other formats from [`CITATION.cff`](CITATION.cff) via GitHub’s **Cite this repository** action.

```bibtex
@software{quartumse2025,
  title = {QuartumSE: Vendor-Neutral Quantum Measurement Optimization},
  author = {QuartumSE Team},
  year = {2025},
  url = {https://github.com/quartumse/quartumse},
  version = {0.1.0}
}
```

---

## Security contact

Refer to the [security policy](SECURITY.md) for supported versions and reporting guidelines. Responsible disclosure reports should be emailed to `security@quartumse.dev` rather than opened as public issues.

---

**QuartumSE** — Building trust and efficiency in quantum computing, one measurement at a time.
