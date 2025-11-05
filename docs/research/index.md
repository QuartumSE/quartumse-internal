# QuartumSE Research Overview & Workflows

**QuartumSE**’s research program is designed to **maximize shot-efficiency** in quantum measurements – extracting more information per experiment while rigorously tracking uncertainty. The core methodology revolves around **classical shadows**, a randomized measurement technique that allows one to “measure once, ask later”, estimating many observables from the same set of quantum circuit runs.

This approach aims to reduce the total number of shots required for tasks like **Hamiltonian estimation**, **algorithm optimization**, and **device benchmarking**, thereby lowering the cost per result without sacrificing accuracy. Key metrics such as the **Shot-Savings Ratio (SSR)** – the factor by which shots are reduced compared to conventional methods – are used to quantify these advantages. 

Currently, the research emphasis is on validating the shadows-based workflow on both **simulators and real hardware**, with targets of SSR ≥ 1.2× on simulator and SSR ≥ 1.1× on **IBM hardware** as proof of shot-efficiency gains before scaling up in subsequent phases.

To organize this effort, we have divided experiments into **five parallel workstreams** (or workflows), each focused on a different application domain but integrated under the common goal of shot-efficient measurement. The workstreams are:

- **Shadows** (Workstream S): Establishes and validates the base classical shadows technique on well-defined quantum states (e.g. GHZ states) using both simulators and hardware. This forms the foundation for all other workstreams.

- **Chemistry** (Workstream C): Applies classical shadows to molecular Hamiltonian estimation (e.g. computing a molecule’s energy) to demonstrate more efficient Quantum Chemistry experiments.

- **Optimization** (Workstream O): Integrates shadows into variational algorithms (specifically QAOA for MAX-CUT) to reduce the measurement overhead per optimization step.

- **Benchmarking** (Workstream B): Uses shadows for device characterization tasks like Randomized Benchmarking (RB) and Cross-Entropy Benchmarking (XEB), aiming to obtain fidelity metrics with fewer runs.

- **Metrology** (Workstream M): Explores the use of shadows in quantum sensing scenarios (e.g. GHZ-phase estimation) to see if entanglement-assisted measurements can be read out more efficiently.

---

### Progress Dashboard

- **Status:** Phase 1 Foundation & R&D (Nov 2025)
- **Experiments:** 4 completed ✅ | 7 planned 📋 | 11 total
- **Coverage:** 36% complete | All 5 workstreams active

The tables below lists all Phase 1 experiments across these workstreams, with their status and a brief description of each study

---

## 📊 Completed Experiments

| ID | Name | Status | Description | Key Result |
|----|------|--------|------------|------|
| [SMOKE-SIM](experiments/S/SMOKE-SIM/) | Simulator Smoke Test | ✅ Completed (Nov 2025) | 3–5 qubit GHZ states on simulator (baseline shadows v0) | SSR = 17.37× |
| [SMOKE-HW](experiments/S/SMOKE-HW/) | Hardware Smoke Test | ✅ Completed (Nov 2025) | 3 qubit GHZ on IBM hardware (v0 shadows, no mitigation) | ibm_fez validated |
| [C-T01](experiments/C/C-T01/) | H₂ Chemistry | ✅ Completed (Nov 2025) | H₂ molecule @STO-3G, 4 qubits – estimate 12-term Hamiltonian with shadows v1 (MEM mitigation) | E = -1.517 Ha |
| [O-T01](experiments/O/O-T01/) | QAOA MAX-CUT | ✅ Completed (Nov 2025) | 5-node ring QAOA optimization with shadow-based cost estimation (ibm_fez, 300 shadows, v1+MEM) | 85% shot reduction, 0.83 approx ratio |

---

## 📋 Planned Experiments

| **Experiment (ID)** | **Workstream**   | **Status**                 | **Description**                                                                                                                     |
| ------------------- | ---------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **S-T01**           | S (Shadows)      | ⏳ *In Progress* (Nov 2025) | Extended GHZ validation – ≥10 trials on hardware to confirm SSR > 1.1× (v0 shadows).                                                |
| **S-T02**           | S (Shadows)      | 📋 *Planned* (Nov 2025)    | Noise-aware GHZ test – compare v1 shadows (with MEM) vs v0 on hardware, target 20–30% variance reduction.                           |
| **O-T01**           | O (Optimization) | 📋 *Planned* (Nov 2025)    | QAOA MAX-CUT on 5-node ring (p=1–2) – use shadows for cost estimation to reduce shots per iteration.                                |
| **B-T01**           | B (Benchmarking) | 📋 *Planned* (Nov 2025)    | Device benchmarking – 1–3 qubit RB sequences and shallow random circuits for XEB (fidelity and purity metrics).                     |
| **S-BELL**          | S (Shadows)      | 📋 *Planned* (Optional)    | Parallel Bell pairs (4–8 qubits total) – test multi-subsystem shadows, CHSH entanglement violation.                                 |
| **S-CLIFF**         | S (Shadows)      | 📋 *Planned* (Optional)    | Random Clifford circuits (5 qubits) – many-observable (~50) scenario to compare against direct fidelity estimation.                 |
| **S-ISING**         | S (Shadows)      | 📋 *Planned* (Optional)    | Trotterized Ising chain (6 qubits) – simulate dynamics, measure energy & correlators to test shadows in a small quantum simulation. |
| **M-T01**           | M (Metrology)    | 📋 *Planned* (Optional)    | GHZ-phase sensing demo (3–4 qubits) – use GHZ states to probe phase with entangled measurements (exploratory).                      |

---

[Results & Analysis](experiments/index.md)

[Theory & Data Models](experiments/index.md)

[Literature Library](experiments/index.md)

[Collaborate](experiments/index.md)