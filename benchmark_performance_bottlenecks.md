# Benchmark Performance Bottlenecks

Identified 2026-02-20 during research benchmark runs. Small circuits (4-7 qubits) are taking hours to benchmark with config: `n_shots_grid=[5000, 10000, 20000]`, `n_replicates=10`, 3 protocols, ~100-300 observables.

## Bottleneck 1: Per-Setting Circuit Recompilation (CRITICAL)

**Location:** `src/quartumse/protocols/base.py:398-412`

Every measurement setting triggers a full `transpile()` call via `_execute_measurement_circuit`. No caching across replicates.

- 25 settings x 10 replicates x 3 protocols x 3 shot counts = **2,250 transpile passes**
- Each transpile: ~200-500ms (scales with qubit count)
- **Estimated cost: 7-18 minutes on compilation alone**

## Bottleneck 2: Python Loops in DirectGrouped/DirectOptimized (CRITICAL)

**Location:**
- `src/quartumse/protocols/baselines/direct_grouped.py:313-316`
- `src/quartumse/protocols/baselines/direct_optimized.py:388-391`

Eigenvalue computation uses per-bitstring Python loops:

```python
eigenvalues = []
for bs in bitstrings:  # Per-bitstring Python loop!
    parity = sum(int(bs[i]) for i in support) % 2
    eigenvalues.append((-1) ** parity)
```

With 200 observables x 10 replicates x 3 protocols x 3 shot counts x ~15,000 avg shots = **~270 million Python loop iterations**.

Ironically, `DirectNaive` already has the vectorized numpy version (`base.py:253-258`):

```python
bs_array = np.frombuffer(
    "".join(bitstrings).encode(), dtype=np.uint8
).reshape(len(bitstrings), -1)[:, support]
parities = (bs_array - 48).sum(axis=1) % 2  # Vectorized!
eigenvalues_array = np.where(parities == 0, 1.0, -1.0)
```

## Bottleneck 3: No Circuit Caching Across Replicates

**Location:** `src/quartumse/tasks/sweep.py:223-287`

The sweep orchestrator runs a nested loop:

```
for protocol (3):
  for n_shots (3):
    for replicate (10):
      protocol.run()  # Rebuilds ALL measurement circuits from scratch
```

Each replicate independently builds and compiles the same measurement circuits. 10 replicates = 10x redundant compilation for identical measurement bases (only the random seed differs).

## Bottleneck 4: Double Circuit Copy Per Setting

**Location:** `src/quartumse/protocols/base.py:427-442`

Two full circuit copies every time a measurement circuit is built:

1. `circuit.remove_final_measurements(inplace=False)` - copy 1
2. `base_circuit.copy()` - copy 2

## Bottleneck 5: Backend Execution Overhead

**Location:** `src/quartumse/protocols/base.py:486-520`

When `AerSimulator` lacks `.sample()`, the fallback path:
- Transpiles per setting (redundant with Bottleneck 1)
- Expands counts dict to bitstring list in Python
- Reverses every bitstring with `[bs[::-1] for bs in bitstrings]`

---

## Recommended Fixes (Priority Order)

### Fix 1: Vectorize eigenvalue computation
Copy the numpy-based approach from `DirectNaive` into `DirectGrouped` and `DirectOptimized`. Expected speedup: **10-100x** on the eigenvalue step.

### Fix 2: Cache compiled measurement circuits
Compile each unique measurement basis circuit once, store in a dict keyed by basis string. Reuse across replicates and shot counts. Expected speedup: **~10x** on circuit compilation.

### Fix 3: Build measurement circuits once per protocol run
Move `_build_measurement_circuit` outside the replicate loop. Only the shot sampling needs to change per replicate.

### Fix 4: Eliminate redundant circuit copies
Use a single base circuit (with measurements stripped) and modify in place, or pre-build all measurement variants once.

### Fix 5: Batch backend execution
Submit multiple measurement settings as a single job where possible, rather than one-at-a-time execution.

---

## Observed Timings (n_shots=[5000,10000,20000], n_replicates=10, noise_sweep=off)

| Circuit | Qubits | Observables | Merged Time |
|---------|--------|-------------|-------------|
| S-ISING-4 | 4 | ~100 | ~1h |
| C-LiH | 6 | ~12 | ~12min |
| O-QAOA-5 | 5 | ~200 | ~3.3h |
| S-ISING-6 | 6 | ~100 | ~4h |
| O-QAOA-7 | 7 | ~300 | TBD (running) |
