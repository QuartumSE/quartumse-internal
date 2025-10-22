# Transverse Ising Chain (6 qubits, 1–2 Trotter steps)

**Hamiltonian:** H = J * Σ Z_i Z_{i+1} + h * Σ X_i

**Goal:** Prepare |ψ(t)⟩ ≈ e^{-iHt} |0...0⟩ using a single (or two) Trotter steps. Estimate energy ⟨H⟩ by measuring all terms with shadows vs. two-basis direct sampling.

## Metrics & Criteria
- Energy error < 5% of full scale (vs. exact small-system diagonalization).
- ≥2× variance reduction (or SSR ≥ 2 for equal precision) compared to two-basis direct.
- Extract all term expectations from one dataset.
