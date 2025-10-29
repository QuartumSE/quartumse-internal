# Quickstart

This guide walks through setting up a local development environment, running
core verification checks, and executing your first experiment.  It merges the
previous `INSTALL_GUIDE.md` and `SETUP.md` content into a single reference.

## Prerequisites

- **Python 3.10+** (3.11 recommended)
- **Git** for cloning the repository
- **Virtual environment** tooling such as `venv`, `conda`, or `pipenv`
- *(Optional)* **Jupyter** for running the demo notebooks

## 1. Clone the repository & create an environment

**Unix/macOS:**
```bash
# Clone repository
git clone https://github.com/quartumse/quartumse.git
cd quartumse

# Create virtual environment (replace with your preferred workflow)
python -m venv .venv

# Activate the environment
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
# Clone repository
git clone https://github.com/quartumse/quartumse.git
cd quartumse

# Create virtual environment
python -m venv .venv

# Activate the environment
.venv\Scripts\activate
```

**Windows (Command Prompt):**
```cmd
rem Clone repository
git clone https://github.com/quartumse/quartumse.git
cd quartumse

rem Create virtual environment
python -m venv .venv

rem Activate the environment
.venv\Scripts\activate.bat
```

If you use Conda or another environment manager, create an equivalent
environment targeting Python 3.10–3.12.

## 2. Install QuartumSE

Choose the extra set that matches your workflow:

**Unix/macOS:**
```bash
# Core SDK only
pip install -e .

# Core SDK + development tooling (pytest, black, ruff, mypy, jupyter)
pip install -e ".[dev]"

# With optional mitigation / chemistry dependencies (Python < 3.13)
pip install -e ".[dev,mitigation,chemistry]"
```

**Windows:**
```powershell
# Core SDK only
pip install -e .

# Core SDK + development tooling (pytest, black, ruff, mypy, jupyter)
pip install -e ".[dev]"

# With optional mitigation / chemistry dependencies (Python < 3.13)
pip install -e ".[dev,mitigation,chemistry]"
```

Upgrading `pip` before installation often avoids wheel build issues:

**Unix/macOS:**
```bash
python -m pip install --upgrade pip
```

**Windows:**
```powershell
python -m pip install --upgrade pip
```

## 3. Verify the installation

Run the basic smoke checks to make sure the package imports and the test suite
passes on simulators:

**Unix/macOS:**
```bash
# Confirm the CLI can be invoked
quartumse --help

# Quick import verification
python -c "from quartumse import ShadowEstimator; print('QuartumSE ready')"

# Run unit tests (skipping slow hardware checks)
pytest tests -m "not slow and not hardware" -v
```

**Windows:**
```powershell
# Confirm the CLI can be invoked
quartumse --help

# Quick import verification
python -c "from quartumse import ShadowEstimator; print('QuartumSE ready')"

# Run unit tests (skipping slow hardware checks)
pytest tests -m "not slow and not hardware" -v
```

Install `pre-commit` hooks to keep formatting and linting consistent:

**Unix/macOS:**
```bash
pre-commit install
```

**Windows:**
```powershell
pre-commit install
```

## 4. Launch the quickstart notebook (optional)

**Unix/macOS:**
```bash
# Ensure Jupyter is installed (included in the [dev] extras)
pip install jupyter

# Start Jupyter Notebook or Lab
jupyter notebook
# or
jupyter lab
```

**Windows:**
```powershell
# Ensure Jupyter is installed (included in the [dev] extras)
pip install jupyter

# Start Jupyter Notebook or Lab
jupyter notebook
# or
jupyter lab
```

Open `notebooks/quickstart_shot_persistence.ipynb` and choose **Run All**.  The
notebook walks through:

1. Preparing a 3-qubit GHZ state.
2. Estimating multiple observables with classical shadows.
3. Inspecting the saved Parquet shot data and JSON provenance manifest.
4. Replaying the experiment to calculate new observables without re-running the
   circuit.

Troubleshooting tips:

- `ModuleNotFoundError: quartumse` → ensure the environment is activated and
  `pip install -e .` succeeded.
- Browser does not open automatically → copy the Jupyter server URL from the
  terminal into your browser.
- Kernel crashes mid-run → restart the kernel and choose **Run All** again.

## 5. Run the S‑T01 GHZ baseline experiment

The CLI script demonstrates the same workflow outside notebooks and produces
provenance artifacts in `data/`:

**Unix/macOS:**
```bash
python experiments/shadows/S_T01_ghz_baseline.py --backend aer_simulator
```

**Windows:**
```powershell
python experiments/shadows/S_T01_ghz_baseline.py --backend aer_simulator
```

Key outputs:

- **Observable estimates** with 95% confidence intervals.
- **Shot-savings ratio (SSR)** versus direct measurement baselines.
- **Manifest & shot files** saved under `data/manifests/` and `data/shots/`.

Supply an IBM Quantum backend descriptor (e.g., `ibm:ibmq_qasm_simulator`) to run
against managed hardware or the cloud simulator once credentials are configured.

## 6. Next steps

- Review [Testing](../how-to/run-tests.md) for guidance on slow, integration,
  and hardware test markers.
- Explore the [Manifest Schema](../explanation/manifest-schema.md) reference to
  understand the manifest and Parquet schemas.
- Consult the [Runtime runbook](../ops/runtime_runbook.md) when planning IBM
  hardware executions.
- Study the strategic context in the [Project Bible](../strategy/project_bible.md)
  and [Roadmap](../strategy/roadmap.md).
