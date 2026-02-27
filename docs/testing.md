# Test Inventory & Architecture

This document catalogues every test file, explains the marker system,
describes the CI pipeline, and covers the performance regression framework.
For day-to-day run commands see [how-to/run-tests.md](how-to/run-tests.md).

---

## Overview

| Metric | Value |
|--------|-------|
| Test files | 28 (unit 22, integration 3, smoke 2, validation 1, perf 1) |
| Test functions | ~155 |
| Layers | Unit, Integration, Smoke, Validation, Performance |
| Framework | pytest with strict markers |

## Marker system

Markers are declared in `pyproject.toml` under `[tool.pytest.ini_options]`.

| Marker | Count | Purpose |
|--------|------:|---------|
| `slow` | 3 | Long-running variance / convergence tests |
| `hardware` | 0 | Requires IBM Quantum credentials and quota |
| `integration` | 4 | Exercising estimator + storage pipelines on simulators |
| `smoke` | 1 | Quick validation of critical end-to-end paths |
| `perf` | 9 | Performance regression tests (see below) |

Unmarked tests are plain unit tests. The CI filter `-m "not slow and not hardware"`
runs everything except `slow` and `hardware`, including `integration`, `smoke`,
and `perf` tests.

## Test file catalog

### Unit tests (`tests/unit/`)

| File | Tests | Module under test | Markers | Description |
|------|------:|-------------------|---------|-------------|
| `test_args.py` | 30 | `quartumse.observables` | — | Observable, ObservableSet, Pauli validation |
| `test_backends.py` | 9 | `quartumse.backends` | — | Backend abstraction, AerSimulator wrapper |
| `test_benchmarking.py` | 12 | `quartumse.benchmarking` | — | simulate_protocol_execution, quick_comparison, SSF, metrics |
| `test_connectors_ibm.py` | 2 | `quartumse.connectors.ibm` | — | IBM Runtime connector mocking |
| `test_manifest.py` | 6 | `quartumse.manifest` | — | Manifest creation, serialization |
| `test_manifest_io.py` | 5 | `quartumse.io` | — | Manifest read/write to disk |
| `test_mem.py` | 2 | `quartumse.noise.mem` | — | Measurement Error Mitigation |
| `test_mermin_expand.py` | 2 | `quartumse.observables` | — | Mermin polynomial expansion |
| `test_metadata_schema.py` | 2 | `quartumse.metadata` | — | Metadata Pydantic schemas |
| `test_metrics.py` | 6 | `quartumse.stats.metrics` | — | Error metrics (MSE, MAE, MaxAE) |
| `test_observable_matrix.py` | 2 | `quartumse.observables` | — | Observable matrix representations |
| `test_reporter_sanitization.py` | 1 | `quartumse.viz.reporter` | — | HTML report sanitization |
| `test_runtime_monitor.py` | 11 | `quartumse.tasks.runtime_monitor` | — | Runtime monitoring, budget alerts |
| `test_shadow_estimator_batching.py` | 1 | `quartumse.shadows` | slow | Batched shadow estimation |
| `test_shadow_estimator_noise_aware.py` | 3 | `quartumse.shadows` | slow (2) | Noise-aware shadow estimator |
| `test_shadows_protocol.py` | 15 | `quartumse.protocols.shadows` | — | ClassicalShadowsProtocol, ShadowsV0 |
| `test_shadows_v0.py` | 6 | `quartumse.protocols.shadows` | — | ShadowsV0Protocol specifics |
| `test_shot_data.py` | 9 | `quartumse.io.shot_data` | — | Shot data persistence (Parquet) |
| `test_tasks_new.py` | 4 | `quartumse.tasks` | — | Task orchestration |
| `test_topology_chain.py` | 5 | `quartumse.noise.topology` | — | Chain topology noise model |
| `test_verifier.py` | 5 | `quartumse.analysis.verifier` | — | Result verification, provenance |

### Integration tests (`tests/integration/`)

| File | Tests | Module under test | Markers | Description |
|------|------:|-------------------|---------|-------------|
| `test_analyzer.py` | 1 | `quartumse.analysis` | integration | Full analysis pipeline |
| `test_direct_pauli_runner.py` | 2 | `quartumse.protocols.baselines` | integration | Direct Pauli measurement runner |
| `test_executor.py` | 1 | `quartumse.tasks.executor` | integration | Task executor end-to-end |

### Smoke tests (`tests/smoke/`)

| File | Tests | Module under test | Markers | Description |
|------|------:|-------------------|---------|-------------|
| `test_pipeline_cli.py` | 1 | `quartumse.cli` | smoke | CLI pipeline invocation |
| `test_reporter_smoke.py` | 1 | `quartumse.viz.reporter` | — | Reporter generates valid HTML |

### Validation tests (`tests/experiments/validation/`)

| File | Tests | Module under test | Markers | Description |
|------|------:|-------------------|---------|-------------|
| `test_hardware_validation.py` | 2 | experiments validation | — | Post-hardware-run validation checks |

### Performance tests (`tests/perf/`)

| File | Tests | Module under test | Markers | Description |
|------|------:|-------------------|---------|-------------|
| `test_perf.py` | 9 | Multiple (protocols, observables, benchmarking) | perf | Regression tests against committed baselines |

## Fixtures

### Global fixtures (`tests/conftest.py`)

| Fixture | Scope | Description |
|---------|-------|-------------|
| `backend` | function | `AerSimulator()` instance |
| `shadow_config` | function | `ShadowConfig(shadow_size=100, random_seed=42)` |
| `ghz_circuit_3q` | function | 3-qubit GHZ circuit |
| `ghz_circuit_4q` | function | 4-qubit GHZ circuit |
| `simple_observables_3q` | function | 4 observables for 3-qubit system |
| `bell_circuit` | function | Bell state circuit (2 qubits) |
| `simple_observables_2q` | function | 4 observables for 2-qubit system |

### Performance fixtures (`tests/perf/conftest.py`)

| Fixture | Scope | Description |
|---------|-------|-------------|
| `perf_baseline` | session | Loads `tests/perf/perf_baseline.json` |
| `perf_workload` | session | 4-qubit Bell circuit + 20 random observables (seed 12345) |

Helper functions: `run_timed(fn, n_runs)`, `assert_no_regression(name, times, baseline)`.

## How to run

```bash
# All tests except slow and hardware (matches CI)
pytest tests/ -m "not slow and not hardware" -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v -m integration

# Performance regression tests only
pytest tests/perf/ -v -m perf

# Include slow tests
pytest tests/ -m "not hardware" -v

# Everything (requires IBM Quantum credentials)
pytest tests/ -v
```

See [how-to/run-tests.md](how-to/run-tests.md) for coverage options and
hardware setup.

## CI flow

The CI pipeline (`.github/workflows/ci.yml`) runs on every push and PR to
`master`, `main`, or `develop`.

| Job | Runs on | What it does |
|-----|---------|--------------|
| **test** | 6 matrix configs (Ubuntu 3.10-3.13, Windows 3.11, macOS 3.11) | Lint (ruff), format (black), type-check (mypy), all tests except `slow`/`hardware` |
| **integration** | 3 platforms (Ubuntu, Windows, macOS) | Re-runs `tests/integration/` with `-m integration` |
| **experiments** | Ubuntu 3.11 | Runs `S_T01_ghz_baseline.py` (continue-on-error) |
| **docs** | Ubuntu 3.11 | Builds mkdocs with `--strict` |

Performance tests run in the **test** job because `perf` is not excluded by
the `-m "not slow and not hardware"` filter.

## Performance regression tests

### How they work

Each test in `tests/perf/test_perf.py` times a hot-path function across
multiple runs, takes the median, and compares it against the committed baseline
in `tests/perf/perf_baseline.json`.

- **Threshold**: 30% — generous to tolerate CI runner variance while still
  catching real regressions (typically 2-10x).
- **Linux-only enforcement**: On Linux (`sys.platform == "linux"`) regressions
  fail the test. On Windows/macOS they produce a warning only, since timing
  noise on those CI runners is higher.

### Benchmarks (9)

| Benchmark | What it times | Runs |
|-----------|--------------|-----:|
| `simulate_direct_naive` | DirectNaiveProtocol end-to-end | 7 |
| `simulate_direct_grouped` | DirectGroupedProtocol end-to-end | 7 |
| `simulate_direct_optimized` | DirectOptimizedProtocol end-to-end | 7 |
| `simulate_shadows_v0` | ShadowsV0Protocol end-to-end | 7 |
| `observable_set_construction` | ObservableSet(20 obs, 4q) | 7 |
| `grouping_algorithms` | greedy + sorted_insertion grouping | 7 |
| `quick_comparison_3proto` | quick_comparison (3 protocols) | 7 |
| `eigenvalue_direct_naive` | `DirectNaiveProtocol._estimate_from_bitstrings` | 21 |
| `eigenvalue_direct_grouped` | `DirectGroupedProtocol._estimate_from_bitstrings` | 21 |

### Updating baselines

After a deliberate performance change (optimization or workload change), update
the baseline:

```bash
python scripts/update_perf_baseline.py
```

This runs all 9 benchmarks and writes `tests/perf/perf_baseline.json` with
metadata (commit SHA, timestamp, Python version, platform). Commit the updated
JSON file.

### Workload

The workload matches `scripts/perf_regression.py`:
- 4-qubit circuit (two Bell pairs)
- 20 random Pauli observables (seed 12345)
- 1000 shots, seed 42

## Known gaps

1. **DirectOptimizedProtocol** has no dedicated unit tests — only covered
   transitively via benchmarking tests and the new perf tests.
2. **2 tests skipped** in `test_shadow_estimator_noise_aware.py` due to a
   `Protocol.run()` interface bug (tracked).
3. **Reproducibility tests** (`test_benchmarking.py::TestBenchmarkReproducibility`)
   only cover DirectNaiveProtocol — other protocols not yet verified for
   seed determinism.
