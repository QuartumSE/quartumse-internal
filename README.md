# QuartumSE

**Vendor-neutral quantum measurement optimization with classical shadows and provenance tracking**

[![CI](https://github.com/quartumse/quartumse/workflows/CI/badge.svg)](https://github.com/quartumse/quartumse/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

> ⚠️ **EARLY R&D - NOT READY FOR PRODUCTION USE**
> QuartumSE is in active Phase 1 development. APIs are unstable and will change.

---

## Vision

QuartumSE is building the **default measurement and observability layer** for quantum computing. We provide:

- **Shot-efficient observable estimation** using classical shadows (v0→v4)
- **Rigorous confidence intervals** via bootstrapping and Bayesian inference
- **Full provenance tracking** for reproducible quantum experiments
- **Vendor-neutral platform** supporting IBM Quantum, AWS Braket, and more
- **Cost-for-accuracy metrics** (SSR, RMSE@$) to quantify efficiency gains

**Goal:** Reduce quantum experiment costs by 2× while maintaining accuracy, with auditable results you can cite in papers.

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/quartumse/quartumse.git
cd quartumse

# Install in development mode
pip install -e ".[dev]"

# (Optional) Set up pre-commit hooks
pre-commit install
```

### Hello World: Classical Shadows on GHZ State

```python
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from quartumse import ShadowEstimator
from quartumse.shadows import ShadowConfig
from quartumse.shadows.core import Observable

# Create a 3-qubit GHZ state
qc = QuantumCircuit(3)
qc.h(0)
qc.cx(0, 1)
qc.cx(0, 2)

# Define observables to estimate
observables = [
    Observable("ZII", coefficient=1.0),  # ⟨Z_0⟩
    Observable("ZZI", coefficient=1.0),  # ⟨Z_0 Z_1⟩
    Observable("ZZZ", coefficient=1.0),  # ⟨Z_0 Z_1 Z_2⟩
]

# Configure classical shadows estimator
config = ShadowConfig(shadow_size=500, random_seed=42)
estimator = ShadowEstimator(backend=AerSimulator(), shadow_config=config)

# Estimate observables with automatic provenance tracking
result = estimator.estimate(circuit=qc, observables=observables)

# View results
for obs_str, data in result.observables.items():
    print(f"{obs_str}: {data['expectation_value']:.4f} ± {data['ci_width']/2:.4f}")

print(f"\nProvenance manifest saved: {result.manifest_path}")
```

Output:
```
1.0*ZII: 0.0000 ± 0.0521
1.0*ZZI: 1.0000 ± 0.0421
1.0*ZZZ: 1.0000 ± 0.0398

Provenance manifest saved: data/manifests/a3f2b...json
Shot data saved: data/shots/a3f2b...parquet
```

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

- **v0 (Baseline):** Random local Clifford measurements ✅
- **v1 (Noise-Aware):** Inverse channel calibration + MEM ✅
- **v2 (Fermionic):** Direct 2-RDM estimation for quantum chemistry
- **v3 (Adaptive):** Derandomized measurement selection
- **v4 (Robust):** Bayesian inference with bootstrapped CIs

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

estimator = ShadowEstimator()
new_observables = [Observable("XXX", coefficient=1.0)]
result = estimator.replay_from_manifest(
    "data/manifests/a3f2b...json",
    observables=new_observables
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

## Project Status

### Phase 1 (Now → Nov 2025)

**Objective:** Foundation & R&D sprints

- [x] Repository structure & CI/CD
- [x] Provenance Manifest v1 schema
- [x] Classical Shadows v0 (baseline)
- [x] Shot data persistence + diagnostics
- [x] S-T01 experiment scaffold (GHZ states)
- [x] S-T02 experiment (noise-aware shadows with MEM)
- [ ] Full S-T01 validation (SSR ≥ 1.2×, CI coverage ≥ 90%)
- [ ] Starter experiments for C, O, B, M workstreams
- [x] MEM integration (ZNE pending)
- [x] Noise-aware classical shadows v1
- [x] IBM Quantum connector

**Exit Criteria:**
- SSR ≥ 1.2× on simulator, ≥ 1.1× on IBM hardware
- CI coverage ≥ 80%
- Patent themes identified

See [ROADMAP.md](ROADMAP.md) for full timeline through Phase 5 (Public Beta, Sep 2026).

---

## Architecture

```
quartumse/
├── src/quartumse/
│   ├── estimator/          # High-level estimation API
│   ├── shadows/            # Classical shadows implementations (v0-v4)
│   ├── mitigation/         # Error mitigation (MEM, ZNE, PEC, RC)
│   ├── connectors/         # Backend adapters (IBM, AWS, etc.)
│   ├── reporting/          # Provenance manifests & report generation
│   └── utils/              # Metrics (SSR, RMSE@$), helpers
├── experiments/            # Research experiments (S-T01, C-T01, etc.)
├── tests/                  # pytest test suite
├── benchmarks/             # Performance benchmarks
└── docs/                   # Documentation
```

---

## Experiments

QuartumSE development is experiment-driven. Run Phase 1 experiments:

```bash
# S-T01: Classical shadows on GHZ states
python experiments/shadows/S_T01_ghz_baseline.py

# C-T01: Shadow-VQE for H₂ (starter)
python experiments/chemistry/C_T01_h2_vqe_starter.py

# O-T01: QAOA for MAX-CUT (starter)
python experiments/optimization/O_T01_maxcut_starter.py

# B-T01: Randomized benchmarking (starter)
python experiments/benchmarking/B_T01_rb_starter.py

# M-T01: GHZ phase sensing (starter)
python experiments/metrology/M_T01_ghz_phase_starter.py
```

The GHZ baseline script now accepts `--config` and `--backend` flags so you can point it at IBM Quantum backends (for example, `python experiments/shadows/S_T01_ghz_baseline.py --backend ibm:ibmq_qasm_simulator`).

All experiments generate manifests in `data/manifests/` and reports in `data/reports/`.

---

## Development

### Running Tests

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

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/quartumse
```

### Pre-commit Hooks

```bash
pre-commit install
pre-commit run --all-files
```

---

## Documentation

- [Project Bible](PROJECT_BIBLE.md) — Vision, architecture, competitive landscape
- [Roadmap](ROADMAP.md) — Detailed R&D plan (2025-2026)
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

Full details: [ROADMAP.md](ROADMAP.md)

---

## Contributing

QuartumSE is in **closed R&D** until Phase 3 (Q1 2026).

We are not accepting external contributions at this time. After Phase 3 patent filings and journal submissions, we will open Early Access for design partners.

---

## License

Apache 2.0 — See [LICENSE](LICENSE)

---

## Team

- **Core Team:** Solo founder (quant analyst + engineering background)
- **Advisor:** Quantum physicist (occasional support)

---

## Citation

If you use QuartumSE in your research (after Phase 3 when validated), please cite:

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

---

**QuartumSE** — Building trust and efficiency in quantum computing, one measurement at a time.
