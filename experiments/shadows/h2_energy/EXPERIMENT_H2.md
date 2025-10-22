# H₂ Ground State Energy (4 qubits, fixed bond length)

**Goal:** Prepare an approximate H₂ ground state (e.g., simple UCC-like circuit) and estimate ⟨H⟩ from ~10–15 Pauli terms using shadows v1+MEM vs. grouped direct.

## Notes
- The exact coefficients depend on bond length and basis. Fill in precise coefficients from your chemistry stack.
- This script includes placeholder coefficients; update them for your target geometry before hardware run.

## Metrics & Criteria
- Energy within 0.02–0.05 Ha of exact energy (for chosen geometry).
- ≥30% lower standard error (or SSR ≥ 1.3) vs. grouped direct for equal shots.
