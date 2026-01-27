# Sampler Performance Recommendations

**File reviewed:** `src/quartumse/backends/sampler.py`

## Performance Issues Identified

### 1. Bitstring Expansion is Wasteful (lines 105-107, 208-210)

```python
bitstrings = []
for bitstring, count in counts.items():
    bitstrings.extend([bitstring] * count)
```

**Problem:** This expands counts into individual bitstrings, creating `n_shots` string objects in memory. For 10,000 shots, you get 10,000 strings. This is memory-intensive and slow.

**Impact:** High - O(n_shots) memory allocation and string duplication.

---

### 2. Unnecessary Shuffle (lines 110-111, 212-213)

```python
rng = np.random.default_rng(seed)
rng.shuffle(bitstrings)
```

**Problem:** The shuffle operation is O(n) over all shots. For many use cases (shadow estimation, expectation values), the order of bitstrings doesn't matter.

**Impact:** Medium - adds O(n_shots) time complexity for no benefit in most protocols.

---

### 3. StatevectorSampler String Formatting (line 264)

```python
bitstrings = [format(outcome, f"0{n_qubits}b") for outcome in outcomes]
```

**Problem:** Python string formatting in a loop is slow. This creates `n_shots` individual format operations.

**Impact:** Medium - Python loops are significantly slower than vectorized numpy operations.

---

### 4. New Backend Per Call (lines 293-295)

```python
if noise_profile == "ideal":
    sampler = IdealSampler()
else:
    sampler = NoisySampler(noise_profile_id=noise_profile, **noise_params)
```

**Problem:** The convenience function `sample_circuit()` creates a new `AerSimulator` instance for every call, which has initialization overhead.

**Impact:** Medium - backend initialization is not free, especially when sampling many circuits.

---

### 5. SamplingResult.counts() is O(n) (lines 36-41)

```python
def counts(self) -> dict[str, int]:
    result = {}
    for bs in self.bitstrings:
        result[bs] = result.get(bs, 0) + 1
    return result
```

**Problem:** If counts are needed downstream, this re-iterates through all bitstrings to reconstruct counts. The data was already in counts form before being expanded.

**Impact:** High if `counts()` is called frequently - duplicates work that was already done.

---

## Recommendations

### 1. Store counts internally, generate bitstrings lazily

Instead of immediately expanding counts to bitstrings, store the counts and only generate bitstrings when explicitly requested:

```python
@dataclass
class SamplingResult:
    _counts: dict[str, int]
    n_shots: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def counts(self) -> dict[str, int]:
        return self._counts.copy()

    @property
    def bitstrings(self) -> list[str]:
        # Lazy generation only when needed
        result = []
        for bitstring, count in self._counts.items():
            result.extend([bitstring] * count)
        return result
```

### 2. Use numpy for batch operations

For `StatevectorSampler`, use vectorized numpy operations:

```python
# Instead of list comprehension
outcomes = rng.choice(len(probs), size=n_shots, p=probs)

# Use numpy to count outcomes directly
unique, counts = np.unique(outcomes, return_counts=True)
result_counts = {
    format(outcome, f"0{n_qubits}b"): int(count)
    for outcome, count in zip(unique, counts)
}
```

This reduces string formatting from O(n_shots) to O(unique_outcomes).

### 3. Remove or make shuffle optional

Add a parameter to control shuffling:

```python
def sample(self, circuit, n_shots, seed=None, shuffle=False):
    ...
    if shuffle:
        rng.shuffle(bitstrings)
```

### 4. Reuse sampler instances

Modify calling code to create samplers once and reuse them:

```python
# Instead of calling sample_circuit() in a loop
sampler = IdealSampler()
for circuit in circuits:
    result = sampler.sample(circuit, n_shots, seed)
```

### 5. Consider batch sampling

Add a method to sample multiple circuits in one call:

```python
def sample_batch(
    self,
    circuits: list[QuantumCircuit],
    n_shots: int,
    seed: int | None = None,
) -> list[SamplingResult]:
    """Sample from multiple circuits efficiently."""
    ...
```

---

## Expected Performance Improvement

With these changes, you should see:

- **Memory usage:** Reduced by ~10-100x for large shot counts (storing counts vs. individual strings)
- **Time for StatevectorSampler:** ~5-10x faster (vectorized counting vs. Python loops)
- **Time for repeated sampling:** ~2-3x faster (reusing backend instances)

---

## Priority Order

1. **High:** Store counts internally (biggest impact)
2. **High:** Use numpy for batch counting in StatevectorSampler
3. **Medium:** Reuse sampler instances
4. **Low:** Remove shuffle (minor but easy)
5. **Low:** Add batch sampling (architectural change)
