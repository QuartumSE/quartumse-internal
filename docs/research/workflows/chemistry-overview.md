# Chemistry Workstream Overview (Workstream C)

## Motivation & Aims

Quantum chemistry is a natural application for shot-frugal measurements because computing molecular energies on quantum hardware (for example via the Variational Quantum Eigensolver, VQE) typically involves measuring a large number of Pauli terms.

A molecule's Hamiltonian is a sum of many Pauli operators; even modest molecules can have dozens of terms that need expectation values. Traditionally, one would group commuting terms and measure each group separately, or even measure terms one by one – a procedure that can dominate the runtime of VQE. Reducing this measurement overhead is crucial for any quantum advantage in chemistry.

The Chemistry workstream aims to demonstrate that classical shadows can estimate all Hamiltonian terms simultaneously from a single set of measurements, thereby dramatically reducing the total shots needed. In theory, for k terms, shadows need on the order of **O(k log k) measurements**, whereas even the best grouping methods need O(k) measurements per group (often 3–5 groups for typical molecules). This suggests a potential **3–5× improvement or more** in shot efficiency for molecular energy estimation.

**Phase 1 Aims:**

- Demonstrate that using classical shadows (with mitigation) can obtain the molecular ground state energy within chemical accuracy using significantly fewer shots than conventional approaches
- Generate the first "data drop" for the chemistry domain with fully logged experiments including manifests and shot data for H₂
- Establish a workflow for Shadow-VQE, where the measurement stage of VQE is powered by shadows
- Assess how hardware noise impacts the accuracy of energy estimates using v1 shadow protocol with measurement error mitigation (MEM)

**Success Criteria:**

- Energy estimation error ≤ 0.02–0.05 Hartree
- Shot-Savings Ratio (SSR) ≥ 1.1× vs. best Pauli grouping baseline

## Relevance

Workstream C validates that the shot-frugal measurement techniques proven in the [Shadows workstream](../workflows/shadows-overview.md) translate effectively to a real-world quantum chemistry application. Molecular energy estimation is one of the most anticipated use cases for quantum computers, and reducing measurement overhead directly impacts the feasibility of quantum chemistry on NISQ devices.

The integration with the [Optimization workstream](../workflows/optimization-overview.md) is natural – both VQE and QAOA involve iterative cost function evaluation, and shadow-based measurement reduction benefits both. By demonstrating chemical accuracy with reduced shots, this workstream provides evidence that quantum chemistry calculations can be made more practical and cost-effective on current hardware.

## Roadmap

The Chemistry workflow in Phase 1 consists of one main experiment and planning for follow-ups:

### Completed Experiments

- **[C-T01](../experiments/C/C-T01/01-rationale.md) - H₂ Hamiltonian** ✅
  Full end-to-end run on a 4-qubit H₂ molecular Hamiltonian (STO-3G basis). Prepared an H₂ ground state ansatz and measured all 12 Pauli terms using 300 shadow shots with v1 mitigation. Achieved ground state energy E = -1.517 Ha, demonstrating shot-efficient molecular energy estimation. Fulfilled Phase 1 requirement of producing the first chemistry dataset and report.

### Planned Experiments

- **Shadow-VQE Integration**
  Integrate classical shadows into a full VQE optimization loop, where after each variational circuit execution, a shadow is taken to evaluate the energy. C-T01 tested the "readout" part; combining it with an optimizer in Phase 2 or 3 will complete the Shadow-VQE vision. Aligned with planned QuartumSE patent on "Shot-Efficient VQE via Shadows" and expected publications in 2026.

### Phase 2 Preparations

- **C-T02 - LiH Molecule** 📋
  Scale up to 6-qubit system with 2× more Hamiltonian terms. Results from H₂ inform parameter choices and mitigation strategies.

- **C-T03 - BeH₂ Molecule** 📋
  Further scaling to 8-qubit system with 3× more Hamiltonian terms than H₂.

- **S-T03 - Fermionic Shadows** 📋
  Exploratory experiment to bypass explicit Pauli decomposition by directly estimating 2-RDM elements – a more direct method for chemistry that could further improve efficiency.

## State of the Art

The Chemistry workstream draws on several strands of cutting-edge research at the intersection of measurement reduction techniques and practical quantum chemistry experimentation on NISQ devices.

**Classical Shadows for Chemistry:**

- **Hadfield et al. (2022)** - Demonstrated that tailoring measurement bases (locally-biased shadows) can significantly cut down samples for molecular Hamiltonians. Their simulation results provided a theoretical foundation that influenced our parameter choices (~300–500 shadows for ~12 terms).

**Traditional Measurement Approaches:**

- **Zhao et al. (2021)** - Showed that even with optimal Pauli grouping, typical small molecules require 3–5 distinct measurement settings – which becomes impractical as molecules grow. This represents the baseline that our shadow approach seeks to beat in terms of total shot count.

**VQE Foundations:**

- **Peruzzo et al. (2014)** - Introduced the Variational Quantum Eigensolver algorithm.

- **McClean et al. (2016)** - Provided comprehensive VQE theory and quantified how shot noise scales with number of Hamiltonian terms, motivating methods like ours to reduce shots needed for each term.

**Error Mitigation:**

- **Kandala et al. (2019)** - Showed that measurement error mitigation (MEM) and zero-noise extrapolation can improve the effective fidelity of VQE experiments on IBM hardware. In [C-T01](../experiments/C/C-T01/01-rationale.md) we used simple MEM calibration (128 extra calibration circuits) to correct readout error, guided by techniques from this work.

Workstream C stands at the intersection of these advances, validating shadow-based measurement reduction for quantum chemistry on real quantum hardware.
