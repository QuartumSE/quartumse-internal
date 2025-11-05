# Shadows Workstream Overview (Workstream S)

## Motivation & Aims

The Shadows workstream underpins the entire **QuartumSE** research program by validating the classical shadows technique itself.

Classical shadows were introduced as a way to **predict many properties of a quantum state from few measurements**. In theory, using randomized Pauli measurements and classical post-processing, one can estimate an exponential number of observables with sample complexity that grows only logarithmically with the number of observables. This promises huge gains in shot efficiency for diverse tasks.

Workstream S is tasked with demonstrating these gains in practice: first in ideal noiseless conditions, and then on real hardware where noise and errors enter. The primary aim is to confirm that the v0 shadows implementation (random Cliffords with no mitigation) produces correct expectation values and achieves a **shot-savings ratio (SSR) ≥ 1.2×** in simulation, and to push toward **SSR ≥ 1.1×** on hardware by introducing a noise-mitigated v1 variant.

## Relevance

Proving even a ~10–20% shot count reduction on hardware would be a significant milestone for near-term quantum experiments. It validates the "measure once, reuse data" paradigm in a real-world setting, directly reducing experimental costs.

Moreover, Workstream S provides the **core infrastructure** (estimators, calibration capture, manifest format) that all other workstreams rely on. For example, a positive result in shadows means the [Chemistry workstream](../workflows/chemistry-overview.md) can trust this measurement layer for molecular observables, and the [Optimization workstream](../workflows/optimization-overview.md) can embed it in feedback loops. Essentially, Workstream S establishes the "trust anchor" that classical shadows work as intended.

## Roadmap

The Shadows workflow progresses through a series of experiments of increasing complexity:

### Completed Experiments

- **[SMOKE-SIM](../experiments/S/SMOKE-SIM/01-rationale.md) - Simulator Validation** ✅
  Baseline test on 3–5 qubit GHZ states using a noiseless simulator. This set the upper benchmark (achieved SSR ~17×) and verified correct implementation of shadows v0.

- **[SMOKE-HW](../experiments/S/SMOKE-HW/01-rationale.md) - Hardware Integration** ✅
  Short run (3 qubits, 100 shots) on an IBM Q backend to validate hardware integration and gather initial noise data. This ensured the pipeline (job submission, data capture) works on real devices before larger trials.

### In Progress

- **[S-T01](../experiments/S/S-T01/01-rationale.md) - Extended GHZ** ⏳
  A thorough test of shadows v0 on hardware: ≥10 independent runs on 4–5 qubit GHZ states. This will provide statistically significant evidence of any SSR > 1 on hardware and measure run-to-run variability.

### Planned Experiments

- **[S-T02](../experiments/S/S-T02/01-rationale.md) - Noise-Aware GHZ** 📋
  Introduces v1 shadows which include measurement error mitigation (MEM) and inverse calibration. By comparing S-T02 against S-T01 (v0), we will quantify how much mitigation improves the variance/accuracy (targeting ~20–30% variance reduction and hopefully pushing SSR beyond 1.1× on hardware).

### Optional Exploratory Experiments

- **[S-BELL](../experiments/S/S-BELL/01-rationale.md) - Parallel Bell Pairs** 📋
  Test shadows on disjoint subsystems to validate multi-subsystem measurements.

- **[S-CLIFF](../experiments/S/S-CLIFF/01-rationale.md) - Random Clifford** 📋
  Random Clifford states with many observables (~50) to benchmark shadows vs direct fidelity estimation.

- **[S-ISING](../experiments/S/S-ISING/01-rationale.md) - Ising Chain** 📋
  Small quantum simulation of an Ising model to test shadows in dynamics and measure energy & correlators.

These exploratory experiments will broaden the validation of shadows to different state types and use cases, feeding into Phase 2.

## State of the Art

The concept of shadow tomography was first explored in theoretical computer science (Aaronson et al., circa 2018–2020) as a means to learn properties of quantum states with optimal sample complexity.

The specific classical shadows protocol used by QuartumSE builds on **Huang, Kueng & Preskill (2020)**, who proved that with random Pauli measurements one can estimate M observables with only O(log M) samples (up to state-dependent constants). This result underpins the shot-savings claims.

Subsequent research has refined the technique:

- **Hadfield et al. (2022)** - Derandomization strategies that bias the measurements to further improve efficiency for structured problems like chemistry, which informed our later workstreams.

- **Chen et al. (2021)** - Developed robust shadow estimation to handle noise via invertible channels, providing a theoretical foundation for our v1 noise-mitigation approach.

- **Recent developments (2024)** - Emerging protocols combine shadow tomography with gate set tomography for more efficient randomized benchmarking procedures.

Workstream S stays abreast of these developments, and in fact [S-T02](../experiments/S/S-T02/01-rationale.md) will be one of the first implementations of a noise-aware shadow protocol on a public quantum device, directly testing the predictions of robust shadows theory.
