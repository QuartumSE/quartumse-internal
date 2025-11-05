# Benchmarking Workstream Overview (Workstream B)

## Motivation & Aims

Quantum hardware benchmarking is essential for assessing and improving device performance. Techniques like Randomized Benchmarking (RB) and Cross-Entropy Benchmarking (XEB) are widely used to estimate error rates and verify quantum advantage. However, these methods themselves can be resource-intensive – they require running many random circuits or specific sequences and collecting statistics.

The Benchmarking workstream explores whether classical shadows can make certain benchmarking tasks more sample-efficient or informative. The idea is that by using a unified measurement approach, one might **extract multiple metrics** (e.g. fidelity, purity, crosstalk) from the same experimental data, rather than running separate experiments for each. Additionally, shadows could potentially reduce the number of repetitions needed by leveraging a form of tomography on the noise processes.

**Phase 1 Aims:**

- Perform small-scale RB/XEB experiments on 1–3 qubit systems
- Explore if shadows provide at least **2× improvement in sample efficiency** compared to standard techniques
- Produce first "benchmarking data drop" with baseline RB decay curves and XEB fidelity measurements
- Test gate-set shadow protocol for extracting gate fidelities from randomized measurements
- Capture state purities, error correlators, and multiple metrics from single experimental campaign

**Success Criteria:**

- Generate validated RB decay curves matching known hardware values
- Collect XEB fidelity data on random circuits (1–3 qubits)
- Full provenance tracking via manifests for all benchmark sequences
- Stretch goal: Demonstrate ≥2× sample efficiency improvement (defer to Phase 2 if not achieved)

## Relevance

Workstream B validates that classical shadows can enhance not just computation-focused applications (proven in [Chemistry](../workflows/chemistry-overview.md) and [Optimization](../workflows/optimization-overview.md) workstreams), but also device characterization and quality assessment.

The ability to extract multiple benchmarking metrics from a single experimental campaign directly addresses a practical pain point: running comprehensive device characterization typically requires many separate experimental protocols (RB for gate fidelity, process tomography for noise characterization, purity measurements, crosstalk analysis, etc.). If shadows can unify these measurements, it significantly reduces the overhead of hardware validation and monitoring.

This workstream also provides critical feedback to the [Shadows workstream](../workflows/shadows-overview.md) by stress-testing shadow protocols on highly randomized circuits where noise characterization is the primary goal rather than state preparation.

## Roadmap

The Benchmarking workflow in Phase 1 is exploratory, establishing baseline data and protocols for shadow-enhanced device characterization:

### Planned Experiments

- **[B-T01](../experiments/B/B-T01/01-rationale.md) - RB/XEB** 📋
  Combined Randomized Benchmarking and Cross-Entropy Benchmarking trial on 1–3 qubit systems. Run short Clifford random sequences (for RB) and small-depth random circuits (for XEB). Use QuartumSE framework to log results via manifests. Baseline goal: obtain RB decay curve and confirm it matches known values for the hardware. Exploratory goal: test if shadows can estimate fidelity of multiple individual Clifford gates simultaneously or capture full output distribution of random circuits more efficiently.

### Integration of Shadows

How can shadows help in benchmarking?

- **Gate-Set Shadow Protocol** - Recently proposed technique that performs shadow tomography on noise channels to extract gate fidelities. Rather than just fitting an exponential to survival probabilities (standard RB), use randomized measurements to learn the effect of noise on many different input states at once.

- **Efficient XEB Sampling** - For Cross-Entropy Benchmarking, shadows might allow estimation of many output probabilities simultaneously, potentially reducing the number of random circuit instances needed. Google's supremacy experiment used 1 million samples per circuit to estimate XEB fidelity ~0.002; shadows could reduce this requirement by estimating off-diagonal terms and multi-output probabilities.

- **Unified Metrics Extraction** - Single experimental campaign could yield: RB error rate, coherence time estimates, crosstalk characterization, state purities, error correlators – all from the same shadow data set.

### Phase 2 Preparations

B-T01 establishes baseline protocols and data formats. Phase 2 will refine methods based on Phase 1 findings and pursue the 2× sample efficiency target if not achieved initially. Integration with [S-CLIFF](../experiments/S/S-CLIFF/01-rationale.md) planned experiment (random Clifford states) will compare shadow-based approaches against direct fidelity estimation (DFE).

## State of the Art

The Benchmarking workstream blends well-established benchmarking protocols with cutting-edge proposals to incorporate tomographic techniques (like shadows) into them.

**Randomized Benchmarking Foundations:**

- **Emerson, Magesan, and others (2008–2011)** - Formulated Randomized Benchmarking as a robust way to measure average gate fidelity independent of state preparation and measurement errors. Considered an industry standard with many variants (interleaved RB, simultaneous RB).

- **Silva & Greplova (2025)** - Hands-on introduction emphasizing RB as an essential tool for assessing quantum gate performance. Notably mentions new trends that "bridge shadow tomography with randomized benchmarking" – exactly the approach we are testing.

**Cross-Entropy Benchmarking:**

- **Arute et al. (2019)** - Google's quantum supremacy demonstration used linear XEB to validate their 53-qubit random circuit sampling against classical simulation. XEB checks that quantum device output probabilities match ideal circuit predictions better than random guessing.

- **Google Sycamore Result** - Achieved XEB fidelity ~0.002 with 1 million samples per circuit, demonstrating the scale of sampling required. Any technique reducing this sample requirement while maintaining accuracy would be valuable.

**Direct Fidelity Estimation:**

- **Flammia & Liu (2011)** - Showed that for certain states, fidelity can be estimated with fewer samples by measuring randomly chosen Pauli operators – conceptually akin to shadows. Our [S-CLIFF](../experiments/S/S-CLIFF/01-rationale.md) planned experiment extends this idea to generic circuits.

**Novel Integration:**

Workstream B doesn't seek to replace core benchmarking protocols but to enhance data collection efficiency. If successful, QuartumSE could offer an **advanced benchmarking mode** where a single experimental campaign yields comprehensive device characterization: RB error rates, coherence times, crosstalk analysis, and purity metrics – all from the same shadow data set.

**Vision:** Shadow-enhanced benchmarking that provides richer characterization with fewer experimental runs, making hardware validation and monitoring more practical and cost-effective.
