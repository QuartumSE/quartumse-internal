# Profiling: Optimization Commits (2026-02-06)

Commits under review: `850d488`, `bbf97e8`, `e9a7e0a`

## Summary

| Optimization | Median speedup | Verdict |
|---|---|---|
| `to_matrix()` via sparse kron | **21x slower** (4q), **2x slower** (8q) | Regression |
| `basis_indices` caching | **10x faster** | Genuine win |
| Batched `PauliList` ground truth | **1.6x slower** | Regression (silent fallback) |
| `scipy.sparse` module-level import | 86 ms one-time | Minor cost at import |

## Details

### 1. `Observable.to_matrix()`: `np.kron` vs `sparse.kron` → `.toarray()`

The old code built dense matrices via `np.kron` directly. The new code builds sparse matrices via `scipy.sparse.kron`, then converts to dense with `.toarray()`.

Sparse kronecker products are designed for large matrices where the result is mostly zeros. Pauli matrices are 2x2 and the tensor products at 4-8 qubits (16x16 to 256x256) are too small to benefit — the overhead of sparse bookkeeping dominates.

```
4 qubits:  OLD=60 us, NEW=1269 us  → 21x slower
6 qubits:  OLD=149 us, NEW=1917 us → 13x slower
8 qubits:  OLD=1441 us, NEW=3046 us → 2x slower
```

Additionally, `to_matrix()` now delegates through `to_sparse_matrix().toarray()`, adding an extra method call and allocation even when the caller only wants the dense result.

### 2. `basis_indices`: per-call dict rebuild vs cached property

The old shadows estimator rebuilt a `{"X": 1, "Y": 2, "Z": 0}` dict and created a new numpy array on every call to `_pauli_expectation_single` and `_pauli_expectation_vectorized`. The new code pre-computes this in `Observable.__post_init__` and caches it.

```
OLD=1.1 us per call, NEW=0.1 us per call → 10x faster
```

This is a clear win with negligible memory cost.

### 3. Ground truth: one-at-a-time vs batched `PauliList`

The intent was to replace per-observable `SparsePauliOp` calls with a single batched `statevector.expectation_value(PauliList(...))`. However, `Statevector.expectation_value()` does not accept `PauliList` in qiskit 2.3.0 — it throws a `QiskitError`.

The code wraps this in a bare `except Exception` that silently falls back to the old one-at-a-time loop. So in practice, every call:

1. Constructs a `PauliList` (wasted work)
2. Calls `expectation_value`, which fails
3. Catches the exception
4. Runs the old path anyway

```
OLD=2043 us, NEW=3336 us → 1.6x slower
```

### 4. `scipy.sparse` import at module level

`from scipy import sparse` and `from scipy.sparse import csr_matrix` were added as top-level imports in `observables/core.py`. This adds ~86 ms to the first `import quartumse`, even if sparse matrices are never used.

## Profiling methodology

- Platform: Windows 11, Python 3.13.5, qiskit 2.3.0, scipy 1.15.3
- Timing: `time.perf_counter()`, median of 200-50000 iterations after warmup
- Script: `bench_optimizations.py` in repo root
