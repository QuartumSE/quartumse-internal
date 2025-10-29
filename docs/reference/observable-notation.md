# Observable Notation Reference

QuartumSE uses **Pauli strings** to specify quantum observables for expectation value estimation. This guide explains the notation, common patterns, and expected values for standard quantum states.

---

## Pauli String Syntax

### Basic Format

An observable is written as a string of Pauli operators, one per qubit:

```python
from quartumse.shadows.core import Observable

# Single-qubit observables
Observable("X")     # X (Pauli-X) on qubit 0
Observable("Y")     # Y (Pauli-Y) on qubit 0
Observable("Z")     # Z (Pauli-Z) on qubit 0
Observable("I")     # I (Identity) on qubit 0

# Multi-qubit observables
Observable("ZII")   # Z on qubit 0, Identity on qubits 1 and 2
Observable("ZZI")   # Z on qubits 0 and 1, Identity on qubit 2
Observable("ZZZ")   # Z on all three qubits
Observable("XXX")   # X on all three qubits
```

### Qubit Ordering

QuartumSE uses **little-endian** (Qiskit-style) qubit ordering:
- **Leftmost character** = qubit 0
- **Rightmost character** = highest-index qubit

```python
# For a 3-qubit circuit
Observable("XYZ")
# X on qubit 0
# Y on qubit 1
# Z on qubit 2
```

### Coefficients

Observables can have multiplicative coefficients:

```python
Observable("ZZ", coefficient=0.5)   # 0.5 × Z₀Z₁
Observable("XX", coefficient=-1.0)  # -1.0 × X₀X₁
```

**Output format:** Results use `{coefficient}*{pauli_string}` notation:
```python
result.observables.keys()
# Returns: ['1.0*ZII', '1.0*ZZI', '1.0*ZZZ']
```

---

## Pauli Operator Properties

### Eigenvalues

All Pauli operators have eigenvalues **±1**:

| Operator | Eigenstate | Eigenvalue |
|----------|------------|------------|
| X | \|+⟩ = (\|0⟩ + \|1⟩)/√2 | +1 |
| X | \|-⟩ = (\|0⟩ - \|1⟩)/√2 | -1 |
| Y | \|i+⟩ = (\|0⟩ + i\|1⟩)/√2 | +1 |
| Y | \|i-⟩ = (\|0⟩ - i\|1⟩)/√2 | -1 |
| Z | \|0⟩ | +1 |
| Z | \|1⟩ | -1 |

### Commutation Relations

- Observables **commute** if they share qubits only on I or matching Pauli operators
- Observables **anticommute** if they differ on an odd number of qubits

```python
# Commuting observables (can measure simultaneously)
Observable("ZII") and Observable("ZZI")  # ✓ commute
Observable("XII") and Observable("YZZ")  # ✓ commute (different qubits)

# Anticommuting observables (cannot measure simultaneously)
Observable("XII") and Observable("ZII")  # ✗ anticommute (differ on qubit 0)
Observable("ZZ") and Observable("XZ")    # ✗ anticommute (differ on qubit 0)
```

---

## Expected Values for Common States

### Computational Basis States

**|00⟩ state:**
```python
Observable("ZI"): +1.0   # Z₀ = +1 (qubit 0 is |0⟩)
Observable("IZ"): +1.0   # Z₁ = +1 (qubit 1 is |0⟩)
Observable("ZZ"): +1.0   # Z₀Z₁ = (+1)(+1) = +1
Observable("XI"):  0.0   # X₀ = 0 (|0⟩ is equal superposition of X eigenstates)
Observable("XX"):  0.0   # X₀X₁ = 0
```

**|11⟩ state:**
```python
Observable("ZI"): -1.0   # Z₀ = -1 (qubit 0 is |1⟩)
Observable("IZ"): -1.0   # Z₁ = -1 (qubit 1 is |1⟩)
Observable("ZZ"): +1.0   # Z₀Z₁ = (-1)(-1) = +1
Observable("XI"):  0.0   # X₀ = 0
Observable("XX"):  0.0   # X₀X₁ = 0
```

### Bell States

**|Φ⁺⟩ = (|00⟩ + |11⟩)/√2 (Bell state):**
```python
Observable("ZI"):  0.0   # Equal |0⟩ and |1⟩ on qubit 0
Observable("IZ"):  0.0   # Equal |0⟩ and |1⟩ on qubit 1
Observable("ZZ"): +1.0   # Correlated: both qubits have same parity
Observable("XX"): +1.0   # Both qubits in X-basis |+⟩
Observable("YY"): -1.0   # Y correlation
Observable("XY"):  0.0   # No XY correlation
```

**|Ψ⁻⟩ = (|01⟩ - |10⟩)/√2 (singlet state):**
```python
Observable("ZI"):  0.0
Observable("IZ"):  0.0
Observable("ZZ"): -1.0   # Anti-correlated
Observable("XX"): -1.0
Observable("YY"): -1.0
Observable("XZ"):  0.0
```

### GHZ States

**|GHZ(3)⟩ = (|000⟩ + |111⟩)/√2:**

GHZ states are stabilized by **even-parity** Z operators:

```python
# Single-qubit Z observables → 0 (equal superposition)
Observable("ZII"):  0.0
Observable("IZI"):  0.0
Observable("IIZ"):  0.0

# Two-qubit Z observables → +1 (even parity stabilizers)
Observable("ZZI"): +1.0
Observable("ZIZ"): +1.0
Observable("IZZ"): +1.0

# Three-qubit Z observables → -1 (odd parity)
Observable("ZZZ"): -1.0

# X observables
Observable("XXX"): +1.0  # All qubits in |+⟩ superposition
Observable("XII"):  0.0  # Single X → 0
Observable("XXI"):  0.0  # Two X's → 0
```

**Rule for GHZ:**
- Even number of Z operators → +1
- Odd number of Z operators → 0 (for single Z) or -1 (for all Z)

**|GHZ(4)⟩ = (|0000⟩ + |1111⟩)/√2:**
```python
Observable("ZIII"):  0.0
Observable("ZZII"): +1.0
Observable("ZZZI"): +1.0
Observable("ZZZZ"): +1.0  # Even number (4) of Z's
Observable("XXXX"): +1.0
```

### W States

**|W(3)⟩ = (|001⟩ + |010⟩ + |100⟩)/√3:**

```python
Observable("ZII"): -1/3  # Two |0⟩ components, one |1⟩
Observable("IZI"): -1/3
Observable("IIZ"): -1/3
Observable("ZZZ"): -1/3  # Mix of even/odd parities
Observable("XXX"):  1/3  # Partial correlation
```

---

## Hamiltonian Observables

Many quantum algorithms estimate **Hamiltonian energy**:

### Ising Model (1D chain)

```python
# H = Σᵢ JᵢZᵢZᵢ₊₁ + ΣᵢhᵢZᵢ
# For 3 qubits with J=-1.0, h=0.5:

Observable("ZZI", coefficient=-1.0)  # Z₀Z₁ interaction
Observable("IZZ", coefficient=-1.0)  # Z₁Z₂ interaction
Observable("ZII", coefficient=0.5)   # Z₀ field
Observable("IZI", coefficient=0.5)   # Z₁ field
Observable("IIZ", coefficient=0.5)   # Z₂ field

# Total energy = sum of all observable expectation values
```

### Molecular Hamiltonians (VQE)

```python
# H₂ molecule (example coefficients)
Observable("II", coefficient=-0.8105)    # Identity term
Observable("ZI", coefficient=0.1721)     # Z₀ term
Observable("IZ", coefficient=0.1721)     # Z₁ term
Observable("ZZ", coefficient=-0.2279)    # Z₀Z₁ correlation
Observable("XX", coefficient=0.1809)     # XX exchange
Observable("YY", coefficient=0.1809)     # YY exchange
```

---

## Interpreting Results

### Confidence Intervals

QuartumSE reports 95% confidence intervals around expectation values:

```python
result.observables["1.0*ZZZ"]
# {
#     'expectation_value': -0.9922,
#     'variance': 0.0156,
#     'ci_95': (-1.0353, -0.9491),
#     'ci_width': 0.0862
# }
```

**Interpretation:**
- **Expectation value**: -0.9922 (close to theoretical -1.0 for GHZ)
- **Variance**: 0.0156 (measurement uncertainty)
- **95% CI**: [-1.0353, -0.9491] (true value likely in this range)
- **CI width**: 0.0862 (precision measure; smaller is better)

### Comparing to Theory

**Example: GHZ(3) validation**

```python
# Theoretical expectations
theory = {
    "1.0*ZII":  0.0,
    "1.0*ZZI": +1.0,
    "1.0*ZZZ": -1.0,
}

# Experimental results
for obs_str, data in result.observables.items():
    estimated = data['expectation_value']
    expected = theory[obs_str]
    ci = data['ci_95']

    # Check if theory is within confidence interval
    in_ci = ci[0] <= expected <= ci[1]
    status = "✓" if in_ci else "✗"

    print(f"{obs_str:10} Est: {estimated:+.4f}  "
          f"Theory: {expected:+.4f}  {status}")
```

**Output:**
```
1.0*ZII    Est: +0.0039  Theory: +0.0000  ✓
1.0*ZZI    Est: +0.9961  Theory: +1.0000  ✓
1.0*ZZZ    Est: -0.9922  Theory: -1.0000  ✓
```

---

## Common Patterns

### Entanglement Witnesses

**CHSH Inequality:**
```python
# S = |⟨XX⟩ + ⟨XY⟩ + ⟨YX⟩ - ⟨YY⟩|
# Classical limit: S ≤ 2
# Quantum (Bell state): S = 2√2 ≈ 2.828

Observable("XX")  # ⟨XX⟩
Observable("XY")  # ⟨XY⟩
Observable("YX")  # ⟨YX⟩
Observable("YY")  # ⟨YY⟩
```

### Fidelity Estimation

**Overlap with target state |ψ⟩:**
```python
# F = ⟨ψ|ρ|ψ⟩ = Σᵢ ⟨Pᵢ⟩ / 2ⁿ
# where Pᵢ are stabilizer observables

# For GHZ(3):
observables = [
    Observable("ZZI"),  # Stabilizer 1
    Observable("IZZ"),  # Stabilizer 2
]
# F ≈ (1 + ⟨ZZI⟩ + ⟨IZZ⟩ + ⟨ZZI⟩⟨IZZ⟩) / 4
```

### Symmetry Testing

**Check parity symmetry:**
```python
# Even parity: should be +1 or -1
Observable("ZZZZ")

# If result ≈ 0, state lacks definite parity
# (e.g., equal mixture of even/odd states)
```

---

## Further Reading

- **Qiskit Observable Tutorial**: [qiskit.org/documentation/tutorials/operators](https://qiskit.org/documentation/tutorials/operators/)
- **Pauli Operator Algebra**: See [Nielsen & Chuang, Chapter 2](http://mmrc.amss.cas.cn/tlb/201702/W020170224608149940643.pdf)
- **Classical Shadows Theory**: [Huang, Kueng, Preskill (2020)](https://arxiv.org/abs/2002.08953)
- **QuartumSE Architecture**: [docs/explanation/shadows-theory.md](../explanation/shadows-theory.md)

---

## Quick Reference

| Observable | Name | Measures |
|------------|------|----------|
| `I` | Identity | Always +1 |
| `X` | Pauli-X | X-basis projection |
| `Y` | Pauli-Y | Y-basis projection |
| `Z` | Pauli-Z | Computational basis projection |
| `ZZ` | Z-correlation | Parity between two qubits |
| `XX` | X-correlation | X-basis entanglement |
| `ZZZ` | 3-qubit parity | Stabilizer for GHZ states |

**Tip:** When debugging, start with Z observables (`ZI`, `ZZ`, etc.) since they measure in the computational basis and are easier to interpret from bitstring histograms.
