# QuartumSE Development Setup Guide

Quick guide to get QuartumSE running on your local machine.

## Prerequisites

- **Python 3.10+** (3.11 recommended)
- **Git**
- **Virtual environment** (recommended)

## Installation Steps

### 1. Clone and Create Virtual Environment

```bash
# Clone repository
git clone https://github.com/quartumse/quartumse.git  # (or your local path)
cd quartumse

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install QuartumSE in editable mode with development dependencies
pip install --upgrade pip
pip install -e ".[dev]"
```

This installs:
- Core dependencies (qiskit, numpy, scipy, pandas, etc.)
- Development tools (pytest, black, ruff, mypy)
- Documentation tools (jupyter, nbconvert)

### 3. Verify Installation

```bash
# Check QuartumSE version
quartumse version

# Run a quick test
python -c "from quartumse import ShadowEstimator; print('✓ QuartumSE imported successfully')"

# Run test suite (quick tests only)
pytest tests/ -m "not slow and not hardware" -v
```

Expected output:
```
QuartumSE version 0.1.0
✓ QuartumSE imported successfully
=================== test session starts ===================
...
=================== XX passed in X.XXs ===================
```

### 4. Set Up Pre-commit Hooks (Optional but Recommended)

```bash
pre-commit install
```

This will automatically run linters and formatters before each commit.

### 5. Run Your First Experiment

```bash
# Run S-T01: Classical Shadows on GHZ states
python experiments/shadows/S_T01_ghz_baseline.py
```

This will:
- Create GHZ states with 3, 4, 5 qubits
- Run classical shadows estimation
- Compare to baseline direct measurement
- Generate provenance manifests in `data/manifests/`
- Save shot data to `data/shots/` (Parquet format with diagnostics)
- Print metrics (SSR, CI coverage)

### 6. Explore the Codebase

```bash
# Package structure
tree src/quartumse/  # or use `ls -R src/quartumse/` on Windows

# View a sample manifest
ls data/manifests/

# View shot data files
ls data/shots/

# Generate an HTML report from a manifest (includes shot diagnostics)
quartumse report data/manifests/<experiment-id>.json --output report.html
```

## Common Tasks

### Running Tests

```bash
# All fast tests
pytest tests/ -m "not slow and not hardware"

# Unit tests only
pytest tests/unit/ -v

# With coverage report
pytest tests/ --cov=quartumse --cov-report=html
# Then open htmlcov/index.html
```

### Code Formatting & Linting

```bash
# Format code
black src/ tests/

# Check linting
ruff check src/ tests/

# Fix auto-fixable issues
ruff check src/ tests/ --fix

# Type checking
mypy src/quartumse/
```

### Running Experiments

```bash
# Individual experiments
python experiments/shadows/S_T01_ghz_baseline.py
python experiments/chemistry/C_T01_h2_vqe_starter.py
python experiments/optimization/O_T01_maxcut_starter.py

# All Phase 1 experiments (takes longer)
for exp in experiments/*/*.py; do python "$exp"; done
```

### Working with Jupyter Notebooks

```bash
# Start Jupyter
jupyter notebook

# Navigate to experiments/ and create a new notebook
# Import QuartumSE:
#   from quartumse import ShadowEstimator, ShadowConfig
#   from quartumse.shadows.core import Observable
```

## IBM Quantum Setup (Phase 1+)

When you're ready to run on real IBM hardware:

1. **Create an IBM Quantum account:** https://quantum.ibm.com/

2. **Save your API token:**

```bash
# Create .env file
echo "IBM_QUANTUM_TOKEN=your_token_here" > .env

# Never commit .env to git (it's in .gitignore)
```

3. **Update experiments to use IBM backend:**

```python
from qiskit_ibm_runtime import QiskitRuntimeService

service = QiskitRuntimeService(channel="ibm_quantum")
backend = service.backend("ibmq_manila")  # Or any available backend

estimator = ShadowEstimator(backend=backend, shadow_config=config)
```

## Troubleshooting

### ImportError: No module named 'quartumse'

**Solution:** Make sure you installed in editable mode:
```bash
pip install -e ".[dev]"
```

### Qiskit version conflicts

**Solution:** Update Qiskit to latest stable:
```bash
pip install --upgrade qiskit qiskit-aer qiskit-ibm-runtime
```

### Tests failing on Windows

**Issue:** Path separators in test fixtures

**Solution:** Tests should use `Path()` from pathlib. Report issue if you encounter path-related failures.

### Experiments producing no output

**Check:**
1. Data directories exist: `mkdir -p data/manifests data/reports`
2. Permissions allow writing to `data/`
3. No errors in console output

## Next Steps

1. **Read the documentation:**
   - [PROJECT_BIBLE.md](PROJECT_BIBLE.md) — Vision & architecture
   - [ROADMAP.md](ROADMAP.md) — Development timeline
   - [README.md](README.md) — Quick overview

2. **Run all Phase 1 experiments** and compare to targets

3. **Explore classical shadows theory:**
   - See `Research/Advanced Algorithms for NISQ Devices – Emphasizing Classical Shadows.pdf`
   - Review Huang, Kueng, Preskill (2020) arXiv:2002.08953

4. **Contribute to development** (once Phase 3+ opens contributions)

## Getting Help

- **Technical issues:** Check existing code comments and docstrings
- **Experiment questions:** Review experiment scaffolds and TODO comments
- **General questions:** Email contact@quartumse.dev (Phase 5+)

---

Happy quantum computing! 🚀
