# Shadows Workstream Overview (Workstream S)

## Motivation & Aims
The Shadows workstream underpins the entire **QuartumSE** research program by validating the classical shadows technique itself. 

Classical shadows were introduced as a way to **predict many properties of a quantum state from few measurements**. In theory, using randomized Pauli measurements and classical post-processing, one can estimate an exponential number of observables with sample complexity that grows only logarithmically with the number of observables. This promises huge gains in shot efficiency for diverse tasks. Workstream S is tasked with demonstrating these gains in practice: first in ideal noiseless conditions, and then on real hardware where noise and errors enter. The primary aim is to confirm that the v0 shadows implementation (random Cliffords with no mitigation) produces correct expectation values and achieves a shot-savings ratio ≥ 1.2× in simulation, and to push toward SSR ≥ 1.1× on hardware by introducing a noise-mitigated v1 variant.

## Relevance
Proving even a ~10–20% shot count reduction on hardware would be a significant milestone for near-term quantum experiments. It validates the “measure once, reuse data” paradigm in a real-world setting, directly reducing experimental costs. Moreover, Workstream S provides the **core infrastructure** (estimators, calibration capture, manifest format) that all other workstreams rely on. For example, a positive result in shadows means the Chemistry workstream can trust this measurement layer for molecular observables, and the Optimization workstream can embed it in feedback loops. Essentially, Workstream S establishes the “trust anchor” that classical shadows work as intended.

## Roadmap
The Shadows workflow progresses through a series of experiments of increasing complexity, as follows:

- **Simulator Smoke Test (SMOKE-SIM)** – Completed. Baseline test on 3–5 qubit GHZ states using a noiseless simulator. This set the upper benchmark (achieved SSR ~17×) and verified correct implementation of shadows v0.

- **Hardware Smoke Test (SMOKE-HW)** – Completed. Short run (3 qubits, 100 shots) on an IBM Q backend to validate hardware integration and gather initial noise data. This ensured the pipeline (job submission, data capture) works on real devices before larger trials.

- **Extended Hardware Validation (S-T01)** – In progress (Nov 2025). A thorough test of shadows v0 on hardware: ≥10 independent runs on 4–5 qubit GHZ states. This will provide statistically significant evidence of any SSR > 1 on hardware and measure run-to-run variability.

- **Noise-Mitigated Shadows (S-T02)** – Pending. Introduces v1 shadows which include measurement error mitigation (MEM) and inverse calibration. By comparing S-T02 against S-T01 (v0), we will quantify how much mitigation improves the variance/accuracy (targeting ~20–30% variance reduction and hopefully pushing SSR beyond 1.1× on hardware).

- Optional exploratory experiments: **S-BELL** (parallel Bell pairs to test shadows on disjoint subsystems), **S-CLIFF** (random Clifford states with many observables, to benchmark shadows vs direct fidelity estimation), and **S-ISING** (a small quantum simulation of an Ising model) are also planned. These will broaden the validation of shadows to different state types and use-cases, feeding into Phase 2.

## State of the Art
The concept of shadow tomography was first explored in theoretical computer science (Aaronson et al., circa 2018–2020) as a means to learn properties of quantum states with optimal sample complexity. The specific classical shadows protocol used by QuartumSE builds on Huang, Kueng & Preskill (2020), who proved that with random Pauli measurements one can estimate 
𝑀
M observables with only 
𝑂
(
log
⁡
𝑀
)
O(logM) samples (up to state-dependent constants). This result underpins the shot-savings claims. Subsequent research has refined the technique: for example, derandomization strategies by Hadfield et al. (2022) bias the measurements to further improve efficiency for structured problems like chemistry, which informed our later workstreams. On the hardware side, recent studies have begun testing shadows in noisy conditions. Chen et al. (2021) developed robust shadow estimation to handle noise via invertible channels, providing a theoretical foundation for our v1 noise-mitigation approach. Additionally, connecting shadows with benchmarking is an emerging idea – e.g. a 2024 protocol combines shadow tomography with gate set tomography for more efficient RB-like procedures. Workstream S stays abreast of these developments, and in fact S-T02 will be one of the first implementations of a noise-aware shadow protocol on a public quantum device, directly testing the predictions of robust shadows theory.
