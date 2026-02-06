# Codex Tasks: Optimization & Sparse-Matrix Follow-Ups

This file lists ready-to-run Codex tasks derived from the optimization discussion
and the observable sparse-matrix work. Each task includes a clear goal and a
command you can run from the repo root.

> **Note:** Tasks marked ✅ are already implemented in this branch; others are
> validation or profiling tasks you can run on demand.

## Task Group A — Optimization Validation (from Q2)

### A1) Profile ground-truth computation cost (statevector)
**Goal:** Measure time and memory scaling with `n_qubits` and observable count.  
**Command:**
```
python - <<'PY'
import time
from qiskit import QuantumCircuit
from quartumse.backends.truth import StatevectorBackend
from quartumse.observables import Observable, ObservableSet

def make_obs(n, m):
    obs = []
    for i in range(m):
        pauli = ["I"] * n
        pauli[i % n] = "Z"
        obs.append(Observable("".join(pauli)))
    return ObservableSet(obs)

for n in [4, 6, 8, 10]:
    circuit = QuantumCircuit(n)
    obs_set = make_obs(n, m=20)
    backend = StatevectorBackend()
    start = time.time()
    backend.compute_ground_truth(circuit, obs_set, circuit_id=f"n{n}")
    elapsed = time.time() - start
    print(f"n={n}, elapsed={elapsed:.3f}s")
PY
```

### A2) Benchmark protocol runtime sweep (publication benchmark)
**Goal:** Estimate runtime overhead of full sweeps; identify hot loops.  
**Command:**
```
python - <<'PY'
from qiskit import QuantumCircuit
from quartumse.benchmarking import run_publication_benchmark
from quartumse.observables import Observable, ObservableSet

qc = QuantumCircuit(4)
obs = ObservableSet([Observable("ZZII"), Observable("IIZZ"), Observable("ZIZI")])
run_publication_benchmark(qc, obs, n_shots_grid=[100], n_replicates=2, compute_truth=False)
print("Benchmark completed.")
PY
```

### A3) Smoke-test sparse vs dense matrix creation costs
**Goal:** Compare dense vs sparse matrix building time for longer strings.  
**Command:**
```
python - <<'PY'
import time
from quartumse.observables import Observable

obs = Observable("XYZI" * 3)
start = time.time()
obs.to_matrix()
print("dense:", time.time() - start)

start = time.time()
obs.to_sparse_matrix()
print("sparse:", time.time() - start)
PY
```

### A4) Parallelize benchmark sweep (experimental)
**Goal:** Explore parallelization by running separate shot budgets in parallel.  
**Command:**
```
python - <<'PY'
import concurrent.futures as cf
from qiskit import QuantumCircuit
from quartumse.benchmarking import run_publication_benchmark
from quartumse.observables import Observable, ObservableSet

qc = QuantumCircuit(4)
obs = ObservableSet([Observable("ZZII"), Observable("IIZZ"), Observable("ZIZI")])

def run(shots):
    run_publication_benchmark(qc, obs, n_shots_grid=[shots], n_replicates=1, compute_truth=False)
    return shots

with cf.ProcessPoolExecutor() as ex:
    for result in ex.map(run, [100, 500, 1000]):
        print("completed shots:", result)
PY
```

## Task Group B — Efficiency Improvements (implementation tasks)

### B1) Add batched ground-truth evaluation
**Goal:** Reduce per-observable overhead by batching expectation evaluation.  
**Command:**
```
rg -n "compute_ground_truth" src/quartumse/backends/truth.py
```
**Suggested change:** build a `SparsePauliOp` with multiple Paulis and call
`Statevector.expectation_value` once for a batched operator list.

### B2) Parallelize benchmark sweeps at the orchestration level
**Goal:** Reduce wall-clock time by running shot budgets or replicates in parallel.  
**Command:**
```
rg -n "run_publication_benchmark" src/quartumse/benchmarking.py
```
**Suggested change:** add an optional `n_jobs` parameter that uses
`concurrent.futures` to fan out over shot budgets or replicates.

### B3) Cache observable matrix outputs (dense + sparse)
**Goal:** Avoid repeated `kron` rebuilds for repeated calls.  
**Command:**
```
rg -n "to_matrix|to_sparse_matrix" src/quartumse/observables/core.py
```
**Suggested change:** memoize the computed matrix in instance attributes
and invalidate only if `pauli_string` or `coefficient` changes.

### B4) Introduce a fast-path for identity-only observables
**Goal:** Short-circuit matrix construction for `"IIII..."` strings.  
**Command:**
```
rg -n "to_sparse_matrix" src/quartumse/observables/core.py
```
**Suggested change:** return `coefficient * I` immediately without `kron`.

### B5) Optional: add a lightweight profiling CLI
**Goal:** Provide a reproducible way to time common paths.  
**Command:**
```
rg -n "cli.py" src/quartumse/cli.py
```
**Suggested change:** add a `quartumse profile` command to run A1–A3 quickly.

## Task Group C — Sparse Matrix & API (5 tasks)

### C1) Decide API strategy ✅
**Status:** Implemented `to_sparse_matrix()` while keeping `to_matrix()` dense.  
**Command (inspect):**
```
rg -n "to_sparse_matrix" src/quartumse/observables/core.py
```

### C2) Docstring update ✅
**Status:** `to_matrix()` now documents dense output, `to_sparse_matrix()` added.  
**Command (inspect):**
```
rg -n "to_matrix|to_sparse_matrix" src/quartumse/observables/core.py
```

### C3) Add tests ✅
**Status:** Added unit tests validating sparse/dense equivalence.  
**Command:**
```
pytest -q tests/unit/test_observable_matrix.py
```

### C4) Audit for downstream usage ✅
**Status:** Search indicates `to_matrix()` used only in its definition within `src/`.  
**Command:**
```
rg -n "to_matrix\\(" src/quartumse
```

### C5) Optional: sparse helper wiring ✅
**Status:** Sparse Pauli matrices and sparse kron path added.  
**Command:**
```
rg -n "SPARSE_PAULI_MATRICES|to_sparse_matrix" src/quartumse/observables/core.py
```
