# QuartumSE Shadow Experiments

This directory contains publication-grade validation experiments for QuartumSE's classical shadows and error mitigation features on IBM Quantum hardware.

## Structure

Each experiment folder contains:
- **Run script** (`run_*.py`) - Executable Python script for IBM hardware
- **Design docs** (`EXPERIMENT*.md`) - Setup, observables, metrics, shot budgets, success criteria
- **Technical gaps** (`TECHNICAL_GAPS.md`) - Missing implementations or dependencies
- **Subdirectories:**
  - `methodology/` - Detailed procedures and experimental notes
  - `results/` - Raw data (manifests, shot data, JSON outputs)
  - `discussion/` - Analysis notebooks, plots, interpretations

## Experiments

### Phase A: Preliminary Validation
- **`preliminary_test/`** - 2-qubit Bell state smoke test
  - Verifies end-to-end connectivity to IBM hardware
  - Tests shadows v0, v1+MEM, and manifest saving
  - Runtime: ~1 minute (~1,712 shots)

### Phase B: Publication-Grade Validation

1. **`extended_ghz/`** - Extended GHZ entanglement (4-5 qubits)
   - Tests MEM effectiveness on larger entangled states
   - Fidelity ≥ 0.5 threshold with mitigation
   - Runtime: ~1-2 minutes

2. **`parallel_bell_pairs/`** - Disjoint Bell pair arrays
   - Simultaneous subsystem observables
   - CHSH violation recovery with MEM
   - Runtime: ~1-2 minutes

3. **`random_clifford/`** - Random Clifford state benchmarking
   - 50+ observable estimation
   - CI coverage and statistical robustness
   - Runtime: ~2 minutes

4. **`ising_trotter/`** - Trotterized Ising chain (6 qubits)
   - Hamiltonian energy estimation
   - Variance reduction demonstration
   - Runtime: ~3-4 minutes

5. **`h2_energy/`** - H₂ molecule ground state
   - Quantum chemistry Hamiltonian (10-15 Pauli terms)
   - Shot efficiency for VQE-like workflows
   - Runtime: ~4 minutes

## Quick Start

```bash
# Set IBM credentials
export QISKIT_IBM_TOKEN='<your_token>'

# Navigate to experiments directory
cd experiments/shadows

# 1) Run smoke test first (recommended)
python preliminary_test/run_smoke_test.py

# 2) Run any publication experiment
python extended_ghz/run_ghz_extended.py
python parallel_bell_pairs/run_bell_pairs.py
python random_clifford/run_random_clifford.py
python ising_trotter/run_ising_chain.py
python h2_energy/run_h2_energy.py
```

## Documentation

- **`EXPERIMENT_PLAN.md`** - Condensed experimental plan
- **`EXPERIMENT_PLAN_TASKS.md`** - Comprehensive task breakdown with citations
- **Phase 1 validation** - See `../validation/hardware_validation.py` for original GHZ-3 baseline

## Total Runtime Budget

All experiments designed to fit within IBM Quantum free tier (10 minutes/month):
- Preliminary test: ~1 min
- Extended GHZ + Bell pairs: ~2-3 min
- Random Clifford: ~2 min
- Ising + H₂: ~7-8 min
- **Total:** ~10-12 minutes (can split across 2 months if needed)

## Success Criteria Summary

| Experiment | Key Metric | Target |
|------------|------------|--------|
| Smoke Test | Connectivity + correlations | ZZ, XX > 0.8 with MEM |
| Extended GHZ | Fidelity with MEM | ≥ 0.5 (entanglement threshold) |
| Bell Pairs | CHSH violation | S > 2 with MEM |
| Clifford | Multi-observable SSR | > 2× efficiency |
| Ising | Energy error | < 5% of full scale |
| H₂ | Energy accuracy | 0.02-0.05 Ha, SSR ≥ 1.3× |

## References

- Research paper: `../../Research/Experiment Plan for Validating QuartumSE...pdf`
- Original Phase 1 validation: `../validation/`
- Classical shadows theory: Huang, Kueng, Preskill (2020) - Nature Physics
