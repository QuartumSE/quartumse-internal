# Technical Gaps (Clifford)
- If you want exact stabilizers to compute DFE analytically, add a stabilizer extraction step (e.g., via qiskit.quantum_info.StabilizerState if available) and include those as explicit observables.
- Current script focuses on many random Pauli observables; add grouped-direct baseline if desired.
