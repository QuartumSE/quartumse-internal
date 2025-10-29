# QuartumSE

**Vendor-neutral quantum measurement optimization with classical shadows and provenance tracking**

[![CI](https://github.com/quartumse/quartumse/workflows/CI/badge.svg)](https://github.com/quartumse/quartumse/actions)
[![Coverage](https://codecov.io/gh/quartumse/quartumse/branch/main/graph/badge.svg)](https://codecov.io/gh/quartumse/quartumse)
[![Docs](https://github.com/quartumse/quartumse/actions/workflows/ci.yml/badge.svg?branch=main&job=docs)](https://github.com/quartumse/quartumse/actions/workflows/ci.yml?query=branch%3Amain+workflow%3ACI+job%3Adocs)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Changelog](https://img.shields.io/badge/changelog-Keep%20a%20Changelog-1F6FEB.svg)](CHANGELOG.md)

> ⚠️ **EARLY R&D - NOT READY FOR PRODUCTION USE**
> QuartumSE is in active Phase 1 development. APIs are unstable and will change.

---

## Vision

QuartumSE is building the **default measurement and observability layer** for quantum computing. We provide:

- **Shot-efficient observable estimation** using classical shadows (v0 and v1 available now; v2–v4 on the roadmap)
- **Confidence interval estimation** via normal approximations today (bootstrap/Bayesian upgrades are planned)
- **Full provenance tracking** for reproducible quantum experiments
- **Vendor-neutral platform** with IBM Quantum + Aer support today and AWS Braket on the near-term roadmap
- **Cost-for-accuracy metrics** (SSR, RMSE@$) to quantify efficiency gains

**Goal:** Reduce quantum experiment costs by 2× while maintaining accuracy, with auditable results you can cite in papers.


---

## Getting Started in 5 Minutes

1. **Install QuartumSE**

   **Unix/macOS (bash/zsh):**
   ```bash
   git clone https://github.com/quartumse/quartumse.git
   cd quartumse
   python -m venv .venv && source .venv/bin/activate
   pip install -e .
   ```

   **Windows (PowerShell):**
   ```powershell
   git clone https://github.com/quartumse/quartumse.git
   cd quartumse
   python -m venv .venv
   .venv\Scripts\activate
   pip install -e .
   ```

   **Windows (Command Prompt):**
   ```cmd
   git clone https://github.com/quartumse/quartumse.git
   cd quartumse
   python -m venv .venv
   .venv\Scripts\activate.bat
   pip install -e .
   ```

2. **Run your first estimator**

   ```python
   from qiskit import QuantumCircuit
   from qiskit_aer import AerSimulator

   from quartumse import ShadowEstimator
   from quartumse.shadows import ShadowConfig
   from quartumse.shadows.core import Observable

   circuit = QuantumCircuit(3)
   circuit.h(0)
   circuit.cx(0, 1)
   circuit.cx(0, 2)

   observables = [Observable("ZII"), Observable("ZZI"), Observable("ZZZ")]
   config = ShadowConfig(shadow_size=256, random_seed=42)
   estimator = ShadowEstimator(backend=AerSimulator(), shadow_config=config)

   result = estimator.estimate(circuit=circuit, observables=observables)

   for obs, data in result.observables.items():
       print(f"{obs}: {data['expectation_value']:.3f} ± {data['ci_width']/2:.3f}")
   ```

   The manifest and shot data produced by the estimator land in `data/` for replay and auditing.

---

## Project Resources

- [API reference](https://quartumse.github.io/quartumse/api/)
- [Examples gallery](https://quartumse.github.io/quartumse/examples/)
- [Security policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## Testing & Coverage

We rely on `pytest` with `pytest-cov` for consistent coverage reporting across
local development and CI. The badge above reflects the latest `main` branch
results uploaded to Codecov.

**Unix/macOS:**
```bash
pip install -e ".[dev]"
pytest -m "not slow and not hardware" -v

# Generate coverage artifacts (terminal, XML for Codecov, and HTML summary)
pytest --cov --cov-report=term-missing --cov-report=xml --cov-report=html
```

**Windows:**
```powershell
pip install -e ".[dev]"
pytest -m "not slow and not hardware" -v

# Generate coverage artifacts (terminal, XML for Codecov, and HTML summary)
pytest --cov --cov-report=term-missing --cov-report=xml --cov-report=html
```

Open `htmlcov/index.html` in a browser to inspect annotated source files. CI
publishes the `coverage.xml` artifact to Codecov on Ubuntu Python 3.11 runs.

#### IBM Quantum connector quick start

QuartumSE ships with an IBM Quantum connector that authenticates against Qiskit Runtime
and records the calibration snapshot used for each experiment. Configure credentials via
`QISKIT_IBM_TOKEN` (or `QISKIT_RUNTIME_API_TOKEN`) and optionally
`QISKIT_IBM_CHANNEL`/`QISKIT_IBM_INSTANCE` to target a specific hub/group/project.

Example experiment configuration (`config.yaml`):

```yaml
backend:
  provider: ibm
  name: ibmq_qasm_simulator
shadow_size: 512
baseline_shots: 1000
```

Validate the configuration and preview calibration data with the CLI:

```bash
quartumse run --config config.yaml
```

Experiment scripts also accept inline overrides:

```bash
python experiments/shadows/S_T01_ghz_baseline.py --backend ibm:aer_simulator
```

If credentials are unavailable, QuartumSE automatically falls back to a local Aer simulator
while still emitting a provenance snapshot.

---

## Core Features

### 🔬 Classical Shadows (v0-v4)

Measure once, estimate many observables offline:

- [x] **v0 (Baseline):** Random local Clifford measurements
- [x] **v1 (Noise-Aware):** Inverse channel calibration + MEM
- [ ] **v2 (Fermionic):** Direct 2-RDM estimation for quantum chemistry
- [ ] **v3 (Adaptive):** Derandomized measurement selection
- [ ] **v4 (Robust):** Bayesian inference with bootstrapped CIs

### 📊 Provenance & Reproducibility

Every experiment generates:
- **JSON Manifest:** Circuit, backend calibration, mitigation config, seeds, versions
- **Shot Data:** Parquet files with raw measurement outcomes + diagnostics
  - Measurement basis distribution (X/Y/Z frequencies)
  - Bitstring histograms (top outcome patterns)
  - Qubit marginal probabilities (single-qubit statistics)
- **HTML/PDF Reports:** Human-readable experiment summaries with integrated diagnostics

**Replay capability:** Re-compute new observables from saved shot data without re-running on hardware.

```python
# Replay from saved manifest to compute new observables
from quartumse import ShadowEstimator

estimator = ShadowEstimator(backend="aer_simulator")
new_observables = [Observable("XXX", coefficient=1.0)]
result = estimator.replay_from_manifest(
    "data/manifests/a3f2b...json",
    observables=new_observables,
)
```

### 📈 Cost-for-Accuracy Metrics

- **SSR (Shot-Savings Ratio):** QuartumSE shots / baseline shots at equal precision
- **RMSE@$:** Cost in dollars to achieve target RMSE

### 🌐 Vendor-Neutral

One API, multiple backends:
- ✅ Qiskit Aer (simulator)
- ✅ IBM Quantum (Phase 1)
- 🚧 AWS Braket (Phase 4)
- 🔮 IonQ, Rigetti (future)

---

## R&D Notebooks

### Start Here: Comprehensive Test Suite

**`notebooks/comprehensive_test_suite.ipynb`** — Complete end-to-end testing covering all QuartumSE features:
- Section 1: Quick Start (Bell state with v0 shadows)
- Section 2: Shot Persistence & Replay ("measure once, ask later")
- Section 3: Noise-Aware Shadows (v1 + MEM)
- Section 4: IBM Quantum Connector
- Section 5: End-to-End Workflow (simulator → hardware → replay)
- Section 6: Diagnostics & Provenance Inspection

**Runtime:** ~5 minutes on simulator, ~15 minutes with IBM hardware

### Additional Notebooks

- `notebooks/noise_aware_shadows_demo.ipynb` – MEM-enhanced classical shadows (v0 vs v1 comparison)
- `notebooks/quickstart_shot_persistence.ipynb` – Shot data persistence basics with replay
- `notebooks/archive/` – Historical smoke-test walkthroughs retained for reference

All notebooks save data into local directories (`demo_data/` or `notebook_data/`) for easy inspection without touching the main `data/` tree.

---

## Project Status

### Phase 1 (Now → Nov 2025)

**Objective:** Foundation & R&D sprints

- [x] Repository structure & CI/CD
- [x] Provenance Manifest v1 schema
- [x] Classical Shadows v0 (baseline)
- [x] Shot data persistence + diagnostics
- [x] S-T01 experiment scaffold (GHZ states)
- [x] S-T02 experiment (noise-aware shadows with MEM)
- [x] Full S-T01 validation (SSR ≥ 1.2×, CI coverage ≥ 90%) ✅
- [x] **Hardware smoke test on IBM ibm_torino** 🎉 (Oct 22, 2025)
- [ ] Extended hardware validation (SSR ≥ 1.1× on IBM)
- [ ] Starter experiments for C, O, B, M workstreams
- [x] MEM integration (ZNE pending)
- [x] Noise-aware classical shadows v1
- [x] IBM Quantum connector (Runtime Sampler SamplerV2)

**Exit Criteria:** **5/7 Complete** ✅

- ✅ SSR ≥ 1.2× on simulator (0.98-7.16×)
- ✅ CI coverage ≥ 90% (100%)
- ✅ Hardware validation (ibm_torino smoke test passed)
- ⏳ SSR ≥ 1.1× on IBM hardware (smoke test complete, extended validation pending)
- ⏳ Patent themes identified (in progress)

**Latest:** Preliminary smoke test successfully executed on IBM ibm_torino (Oct 22). All quality checks passed. Classical Shadows v0/v1 + MEM validated on real hardware. See [docs/archive/status_report_20251022.md](docs/archive/status_report_20251022.md) for detailed results and analysis.

See [docs/strategy/roadmap.md](docs/strategy/roadmap.md) for full timeline through Phase 5 (Public Beta, Sep 2026).

---

## Architecture

```
quartumse/
├── src/quartumse/
│   ├── estimator/          # High-level estimation API
│   ├── shadows/            # Classical shadows implementations (v0 & v1 today)
│   ├── mitigation/         # Error mitigation (MEM, ZNE scaffolding)
│   ├── connectors/         # Backend adapters (IBM Runtime + Aer helpers)
│   ├── reporting/          # Provenance manifests & report generation
│   └── utils/              # Metrics (SSR, RMSE@$), helpers
├── experiments/            # Research experiments (shadows + validation harness)
├── notebooks/              # Guided demos and validation walkthroughs
├── docs/                   # Guides, runbooks, roadmap
├── tests/                  # pytest test suite
├── tools/                  # Dev scripts (lint, release helpers)
├── data*/                  # Default output directory (gitignored)
├── validation_data*/       # Phase 1 validation artifacts (gitignored)
└── demo_data*/             # Notebook/demo artifacts (gitignored)

*Gitignored working directories that are created on demand.
```

---

## Experiments

QuartumSE development is experiment-driven. Maintained scripts live in
`experiments/shadows/` and `experiments/validation/`:

```bash
# S-T01: Classical shadows on GHZ states
python experiments/shadows/S_T01_ghz_baseline.py --backend aer_simulator

# Hardware validation harness
python experiments/validation/hardware_validation.py
```

Prototype scaffolds for chemistry, optimization, metrology, and benchmarking
reside under `experiments/shadows/*` with dedicated run scripts.
Historical or superseded prototypes have been relocated to `experiments/archive/`.

The GHZ baseline script accepts `--config` and `--backend` flags so you can
target IBM Quantum backends (for example,
`python experiments/shadows/S_T01_ghz_baseline.py --backend ibm:ibmq_qasm_simulator`).

All experiments generate manifests in `data/manifests/` (or your configured data directory)
and reports in `data/reports/`.

For Phase-1 automation, the [Automated Experiment Pipeline guide](docs/guides/pipeline.md)
covers metadata, equal-budget rules, calibration reuse, and CLI commands for simulator
and IBM Quantum hardware runs.

---

## Development

### Running Tests

**Unix/macOS:**
```bash
# All tests (fast)
pytest tests/ -m "not slow and not hardware"

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# With coverage
pytest --cov=quartumse --cov-report=html
```

**Windows:**
```powershell
# All tests (fast)
pytest tests/ -m "not slow and not hardware"

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# With coverage
pytest --cov=quartumse --cov-report=html
```

### Code Quality

**Unix/macOS:**
```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/quartumse
```

**Windows:**
```powershell
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/quartumse
```

### Pre-commit Hooks

**Unix/macOS:**
```bash
pre-commit install
pre-commit run --all-files
```

**Windows:**
```powershell
pre-commit install
pre-commit run --all-files
```

---

## Documentation

- [docs/README.md](docs/README.md) — Index of setup guides, ops notes, and strategy docs
- [Research/](Research/) — Classical shadows papers and references

---

## Roadmap Highlights

| Phase | Focus | Key Milestone | Target |
|-------|-------|--------------|--------|
| **P1** | Foundation & R&D | First IBM runs + Shadows v1 | **Nov 2025** |
| **P2** | Hardware iteration | IBM campaign #1 + provisional patents | **Dec 2025** |
| **P3** | Internal validation | SSR ≥1.5× + journal submissions | **Mar 2026** |
| **P4** | Early Access | 2-3 partners + AWS Braket | **Jun 2026** |
| **P5** | Public Beta | v1.0 + pilots | **Sep 2026** |

Full details: [docs/strategy/roadmap.md](docs/strategy/roadmap.md)

---

## Contributing

QuartumSE is in **closed R&D** until Phase 3 (Q1 2026).

We are not accepting external contributions at this time. After Phase 3 patent filings and journal submissions, we will open Early Access for design partners.

Even during this closed phase, we expect all community interactions to follow our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it alongside the [contribution guidelines](CONTRIBUTING.md) so you're ready when contributions open.

---

## License

Apache 2.0 — See [LICENSE](LICENSE)

---

## Team

- **Core Team:** Solo founder (quant analyst + engineering background)
- **Advisor:** Quantum physicist (occasional support)

---

## Citation

If you use QuartumSE in your research (after Phase 3 when validated), export the
preferred format from GitHub's **Cite this repository** button, which is backed
by [`CITATION.cff`](CITATION.cff). Manual BibTeX entry:

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

## Contact

- **Issues:** [GitHub Issues](https://github.com/quartumse/quartumse/issues)
- **Email:** contact@quartumse.dev (placeholder)

## Security

Please review our [Security Policy](SECURITY.md) for the latest list of supported
versions and detailed vulnerability reporting instructions. To protect users,
kindly avoid filing public GitHub issues for security-related reports—email
security@quartumse.dev instead so we can coordinate a private fix.

---

**QuartumSE** — Building trust and efficiency in quantum computing, one measurement at a time.
