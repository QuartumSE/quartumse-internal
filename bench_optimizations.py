"""Profile the three optimizations from commits 850d488, bbf97e8, e9a7e0a.

Tests:
  1. Observable.to_matrix(): direct np.kron vs sparse-then-dense
  2. basis_indices: per-call dict rebuild vs cached property
  3. Ground truth: one-at-a-time vs batched PauliList
  4. scipy.sparse import cost at module load
"""

import time
import numpy as np


# ── Helpers ──────────────────────────────────────────────────────────────

def timeit(fn, n_iter=1000, warmup=50, label=""):
    """Time a callable, return median time in microseconds."""
    for _ in range(warmup):
        fn()
    times = []
    for _ in range(n_iter):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    arr = np.array(times) * 1e6  # to microseconds
    med = np.median(arr)
    p25, p75 = np.percentile(arr, [25, 75])
    print(f"  {label:40s}  median={med:8.1f} us  [P25={p25:.1f}, P75={p75:.1f}]  (n={n_iter})")
    return med


# ── Test 1: to_matrix() ─────────────────────────────────────────────────

def test_to_matrix():
    """Compare direct np.kron (old) vs sparse.kron -> toarray (new)."""
    from scipy import sparse

    PAULI_MATRICES = {
        "I": np.array([[1, 0], [0, 1]], dtype=complex),
        "X": np.array([[0, 1], [1, 0]], dtype=complex),
        "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
        "Z": np.array([[1, 0], [0, -1]], dtype=complex),
    }
    SPARSE_PAULI = {k: sparse.csr_matrix(v) for k, v in PAULI_MATRICES.items()}

    for n_qubits, pauli_str in [(4, "XZIY"), (6, "XZIYZX"), (8, "XZIYZXII")]:
        coeff = 0.5

        def old_to_matrix():
            result = np.array([[1.0]], dtype=complex)
            for c in pauli_str:
                result = np.kron(result, PAULI_MATRICES[c])
            return coeff * result

        def new_to_matrix():
            result = sparse.csr_matrix([[1.0]], dtype=complex)
            for c in pauli_str:
                result = sparse.kron(result, SPARSE_PAULI[c], format="csr")
            return (coeff * result).toarray()

        # No caching — measures raw construction cost each call
        print(f"\n  to_matrix() — {n_qubits} qubits, pauli_str='{pauli_str}':")
        t_old = timeit(old_to_matrix, n_iter=2000, label="OLD (np.kron)")
        t_new = timeit(new_to_matrix, n_iter=2000, label="NEW (sparse.kron -> toarray)")
        ratio = t_new / t_old
        winner = "OLD faster" if ratio > 1 else "NEW faster"
        print(f"  --> ratio NEW/OLD = {ratio:.2f}x  ({winner})")


# ── Test 2: basis_indices ────────────────────────────────────────────────

def test_basis_indices():
    """Compare per-call dict rebuild (old) vs cached property (new)."""

    pauli_string = "XZIY"
    support = [i for i, c in enumerate(pauli_string) if c != "I"]

    # Old: rebuild every call
    def old_basis_indices():
        pauli_to_basis = {"X": 1, "Y": 2, "Z": 0}
        return np.array([pauli_to_basis[pauli_string[q]] for q in support], dtype=int)

    # New: pre-cached (simulate by computing once)
    cached = np.array([{"X": 1, "Y": 2, "Z": 0}[pauli_string[q]] for q in support], dtype=int)

    def new_basis_indices():
        return cached

    print(f"\n  basis_indices — pauli_str='{pauli_string}', support={support}:")
    t_old = timeit(old_basis_indices, n_iter=50000, label="OLD (rebuild each call)")
    t_new = timeit(new_basis_indices, n_iter=50000, label="NEW (cached property)")
    ratio = t_new / t_old
    winner = "OLD faster" if ratio > 1 else "NEW faster"
    print(f"  --> ratio NEW/OLD = {ratio:.2f}x  ({winner})")


# ── Test 3: Ground truth batched vs one-at-a-time ────────────────────────

def test_ground_truth():
    """Compare one-at-a-time vs batched PauliList expectation values."""
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Pauli, PauliList, SparsePauliOp, Statevector

    # Build a 4-qubit circuit with some rotations
    qc = QuantumCircuit(4)
    rng = np.random.default_rng(42)
    for q in range(4):
        qc.ry(rng.uniform(0, np.pi), q)
    qc.cx(0, 1)
    qc.cx(2, 3)

    sv = Statevector.from_instruction(qc)

    # Generate 20 random Pauli strings (typical observable set size)
    paulis_chars = ["I", "X", "Y", "Z"]
    pauli_strings = []
    coefficients = []
    for _ in range(20):
        ps = "".join(rng.choice(paulis_chars) for _ in range(4))
        pauli_strings.append(ps)
        coefficients.append(rng.uniform(0.1, 1.0))

    def old_one_at_a_time():
        results = {}
        for i, (ps, coeff) in enumerate(zip(pauli_strings, coefficients)):
            op = SparsePauliOp(Pauli(ps))
            val = float(np.real(sv.expectation_value(op)))
            results[f"obs_{i}"] = val * coeff
        return results

    def new_batched_with_fallback():
        """What actually runs in production: try PauliList, fall back on exception."""
        try:
            pl = PauliList(pauli_strings)
            expectations = sv.expectation_value(pl)
            results = {}
            for i, (exp, coeff) in enumerate(zip(expectations, coefficients)):
                results[f"obs_{i}"] = float(np.real(exp)) * coeff
            return results
        except Exception:
            # Falls through to one-at-a-time (this is what actually happens)
            results = {}
            for i, (ps, coeff) in enumerate(zip(pauli_strings, coefficients)):
                op = SparsePauliOp(Pauli(ps))
                val = float(np.real(sv.expectation_value(op)))
                results[f"obs_{i}"] = val * coeff
            return results

    # Verify the batched path actually fails with this qiskit version
    try:
        pl = PauliList(pauli_strings)
        sv.expectation_value(pl)
        batched_works = True
    except Exception:
        batched_works = False

    print(f"\n  ground_truth — 4 qubits, 20 observables:")
    print(f"  NOTE: PauliList batching {'WORKS' if batched_works else 'FAILS'} "
          f"with qiskit {__import__('qiskit').__version__} — "
          f"{'batched path used' if batched_works else 'fallback to one-at-a-time every call'}")

    t_old = timeit(old_one_at_a_time, n_iter=200, label="OLD (one-at-a-time, no try/except)")
    t_new = timeit(new_batched_with_fallback, n_iter=200, label="NEW (try PauliList + fallback)")
    ratio = t_new / t_old
    winner = "OLD faster" if ratio > 1 else "NEW faster"
    print(f"  --> ratio NEW/OLD = {ratio:.2f}x  ({winner})")
    if not batched_works:
        print(f"  --> The 'optimization' adds PauliList construction + exception overhead "
              f"then does the same work")


# ── Test 4: scipy.sparse import overhead ─────────────────────────────────

def test_import_overhead():
    """Measure import time for scipy.sparse (loaded at module level in new code)."""
    import importlib
    import sys

    n_iter = 20

    # Measure time to import scipy.sparse from scratch
    times = []
    for _ in range(n_iter):
        # Remove from cache
        mods_to_remove = [k for k in sys.modules if k.startswith("scipy.sparse")]
        for m in mods_to_remove:
            del sys.modules[m]

        t0 = time.perf_counter()
        import scipy.sparse  # noqa: F401
        times.append(time.perf_counter() - t0)

    arr = np.array(times) * 1000  # milliseconds
    print(f"\n  scipy.sparse import (cold): median={np.median(arr):.1f} ms  "
          f"[min={np.min(arr):.1f}, max={np.max(arr):.1f}]  (n={n_iter})")
    print(f"  (This cost is paid once at module load when importing observables/core.py)")


# ── Main ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 72)
    print("PROFILING OPTIMIZATION COMMITS (850d488, bbf97e8, e9a7e0a)")
    print("=" * 72)

    print("\n[1] Observable.to_matrix(): np.kron vs sparse.kron -> toarray")
    print("-" * 72)
    test_to_matrix()

    print("\n\n[2] basis_indices: per-call rebuild vs cached")
    print("-" * 72)
    test_basis_indices()

    print("\n\n[3] Ground truth: one-at-a-time vs batched PauliList")
    print("-" * 72)
    test_ground_truth()

    print("\n\n[4] scipy.sparse import overhead")
    print("-" * 72)
    test_import_overhead()

    print("\n" + "=" * 72)
    print("DONE")
    print("=" * 72)
