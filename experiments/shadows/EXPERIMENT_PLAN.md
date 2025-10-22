EXPERIMENTAL PLAN – QuartumSE on IBM ‘ibm_torino’ (Free-tier 10-minute constraint)

Overview
- Purpose: Validate classical shadows (v0), noise-aware shadows with MEM (v1), and direct/grouped baselines under tight runtime budgets.
- Deliverables: Shot-efficiency (SSR), CI coverage, MAE; plus fidelity/energy metrics; full provenance (manifests & shot data).

Phase A – Preliminary Smoke Test
- 2-qubit Bell state; verify backend connectivity, measurement pipeline, and manifest saving.
- Targets: ZZ, XX ~ +1 with MEM; complete within ~1 minute.

Phase B – Research-grade Experiments
1) Extended GHZ (4–5 qubits)
   - Prepare GHZ-N (H + CNOT chain). Measure pairwise ZZ and global X...X parity.
   - Success: Fidelity >= 0.5 with MEM; MAE < 0.1 on parities; SSR > 1 vs. direct; CI ~95%.
2) Disjoint Bell Pairs (4 qubits)
   - Two Bell states; estimate XX and ZZ per pair; optional CHSH violation.
   - Success: Fidelity per pair > 0.9 (MEM); CHSH S > 2 with >=3σ; CI ~95%.
3) Random Clifford (5 qubits)
   - Depth ~10 random (H,S,CX) circuit; estimate 50+ Pauli observables; DFE via stabilizers (optional).
   - Success: SSR > 2× vs grouped direct; CI ~95%; fidelity within ±0.05 of ideal.
4) Ising Chain (6 qubits)
   - 1–2 Trotter steps for H = J Σ Z_i Z_{i+1} + h Σ X_i; estimate ⟨H⟩ from all terms.
   - Success: <5% energy error; ≥2× variance reduction vs. two-basis direct; all terms from one dataset.
5) H2 Energy (4 qubits)
   - Prepare approximate ground state; estimate ~10–15 Pauli terms with v1+MEM vs grouped direct.
   - Success: Energy within 0.02–0.05 Ha of exact; ≥30% lower SE (SSR ≥ 1.3).

Shot & Runtime Guidance
- Total monthly runtime ~10 minutes; prioritize Ising and H2; GHZ/Bell/Clifford are 1–2 minutes each.
- Use batch shots (500–1500 per submission) to minimize overhead; perform MEM calibration once per experiment.

Provenance & Reproducibility
- Save manifests and shot data; capture backend snapshot (T1/T2, gate/readout errors, calibration timestamp).
- Fix RNG seeds for repeatability; store experiment IDs and file paths in results JSON.
