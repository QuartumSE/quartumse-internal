# Measurements Bible v3
*A publication-grade methodology and implementation blueprint for benchmarking quantum measurement protocols in QuartumSE*

**Status:** normative specification for QuartumSE benchmarking and reporting  
**Audience:** researchers and engineers implementing/using measurement benchmarks  
**Core promise:** any headline claim can be reproduced from logged configs + seeds + artifacts, and compared fairly against strong baselines.

---

## 0. Methodology-as-code: versioning, artifacts, and reproducibility

### 0.1 Versioning
- This document defines a **versioned benchmark standard**.
- Every benchmark run **must** store:
  - `methodology_version`: e.g., `"3.0.0"`
  - git commit hash (code)
  - environment lock (pip freeze / uv lock / conda env export)
  - all RNG seeds used (see §9.2)

### 0.2 Required artifacts per run
A run is complete only if it produces:
1. Long-form results table (tidy format, §10.1)
2. Summary tables (§10.2)
3. Required plots (§10.3)
4. Machine-readable manifest with config + provenance (§13)
5. Notebook reproducibility (at minimum Notebook A and B, §12)

### 0.3 Determinism policy
- For a **deterministic backend**, fixed seeds must yield identical outputs.
- For **hardware**, determinism is not expected; instead, runs must record all hardware metadata needed to explain variability.

---

## 1. Scope and goals

This document specifies a rigorous, extensible suite to benchmark **measurement protocols** that estimate expectation values of many observables from repeated quantum circuit executions (“shots”).

Goals:
- Produce **defensible** comparisons across protocols, including strong direct-measurement baselines.
- Evaluate both:
  - **accuracy vs truth** (when available), and
  - **reported uncertainty** (what users see in practice).
- Support:
  - multiple observable families (Pauli, Pauli sums, mapped fermionic operators),
  - multiple backends (ideal/noisy simulators, optional hardware),
  - multiple estimators (mean, robust, bootstrap),
  - adaptive protocols (sequential design).

Non-goals:
- Declaring a universally best protocol. The suite produces **regime maps** showing where each approach wins/loses.

---

## 2. Core definitions and first-class performance quantities

### 2.1 Fundamental resources
- **Shot**: one independent execution of the target circuit (state preparation) followed by measurement.
- **Measurement setting**: the measurement basis/unitary choices used for a subset of shots.
- **Quantum runtime**: wall-clock time attributable to quantum execution (simulator time or hardware runtime).
- **Classical runtime**: wall-clock time for planning + post-processing (including adaptive decision logic).
- **Memory**: peak resident memory used during estimation (and optionally planning).

### 2.2 Estimands
For each observable \(O_i\), the target is:
\[
o_i := \langle O_i \rangle = \mathrm{tr}(O_i \rho)
\]
A protocol produces:
- estimate \(\widehat{o}_i(N)\)
- uncertainty summary (SE/CI), \(\widehat{\mathrm{SE}}_i(N)\) and/or \([\mathrm{CI}_{i,\mathrm{low}}, \mathrm{CI}_{i,\mathrm{high}}]\)

### 2.3 Two types of uncertainty (mandatory distinction)
1. **Empirical error vs truth** (requires truth \(o_i\)):
   - absolute error, squared error, RMSE, bias
2. **Reported uncertainty** (available in practice):
   - standard error and confidence intervals
Both must be tracked and compared; reported uncertainty must be checked for **calibration** (§7, §6.2).

### 2.4 Canonical efficiency and quality measures (define early; used throughout)

#### Shots-to-target
Given a criterion \(\mathcal{C}\) and global failure probability \(\delta\) (see §8), define:
\[
N^\*(\varepsilon, \delta; \mathcal{C}) := \min\{N : \mathcal{C}(N,\varepsilon,\delta)\ \text{is satisfied}\}
\]

#### Shot-savings factor (relative efficiency)
For two protocols A (candidate) and B (baseline):
\[
\mathrm{SSF}_{A\leftarrow B} := \frac{N^\*_B}{N^\*_A}
\]
Interpretation:
- \(\mathrm{SSF} > 1\): A saves shots vs B
- \(\mathrm{SSF} < 1\): A uses more shots than B (negative result)

#### Attainment function
For fixed \(N\) and target \(\varepsilon\):
\[
f(N;\varepsilon) := \frac{1}{M}\#\{ i : \text{quality}_i(N)\le \varepsilon \}
\]
where `quality_i` is either reported CI half-width or truth-based error, depending on the task definition.

#### Multi-objective reporting (recommended default)
Do not collapse everything into one scalar unless explicitly configured. Report the Pareto profile:
- (shots, #settings, quantum runtime, classical runtime, memory, optional cost)

---

## 3. Workloads: circuits, observable sets, and truth

### 3.1 Circuit families (recommended benchmark set)
Benchmarks should include multiple circuit families to avoid cherry-picking:
- product states (sanity)
- GHZ-like / stabilizer circuits (structured)
- hardware-efficient ansatz circuits (typical NISQ)
- random Clifford / random circuits (scrambling/expressiveness regimes)

Each circuit instance must record:
- `n_qubits`
- a circuit identifier + serialized representation
- compilation/transpilation settings used (backend-dependent)
- post-compilation gate counts and depth (including measurement pre-rotations)

### 3.2 Observable representations (required adapters)
The suite must treat observables as objects with explicit representations, not ad-hoc strings.

An `Observable` must provide one of:
- **Pauli string** representation
- **Pauli sum** representation (Hamiltonian-like)
- **projector / measurement-basis representation** (if applicable)
- **sparse matrix** (truth computation only; optional)
- **fermionic operator** + mapping (extension; see §4.2F)

All observables must include required metadata:
- `observable_id`
- `observable_type`
- `locality` (e.g., Pauli weight; or a meaningful proxy)
- `coefficient` (if part of a sum)
- `group_id` (if assigned for grouped baselines)

### 3.3 Standardized observable-set generation (required for reproducibility)
Every benchmark must specify the observable set via a seeded generator spec, not only by listing observables.

Required config fields:
- `observable_set_id`
- `generator_id` and `generator_version`
- `generator_seed`
- generator parameters (e.g., weight distribution, coefficient distribution, support structure)

Required built-in generators (minimum):
- Random Pauli strings with controlled weight distribution
- Hamiltonian-like Pauli sums with controlled coefficient distribution (e.g., heavy-tailed vs decaying)
- Structured correlators (e.g., 2-point Z_i Z_j on a graph)
- Clustered-support sets (many observables overlapping on a subset of qubits)

### 3.4 Ground truth and reference truth (required policy)

The suite distinguishes **exact truth** from **reference truth**:

**Exact truth (preferred):**
- Compute \(o_i=\mathrm{tr}(O_i\rho)\) exactly via statevector or density-matrix simulation.

**Reference truth (allowed):**
- If exact truth is infeasible, define a high-precision reference procedure and treat its output as truth with uncertainty.

Truth feasibility must be config-driven using a **memory budget**, not a fixed qubit cutoff:

Approximate memory requirements:
- statevector: \(\approx 16\cdot 2^n\) bytes (complex128)
- density matrix: \(\approx 16\cdot 4^n\) bytes (complex128)

Required config fields:
- `truth_mode`: `exact_statevector` | `exact_density_matrix` | `reference`
- `truth_memory_limit_bytes`
- If `reference`:
  - `truth_reference_protocol_id`
  - `truth_reference_budget`
  - `truth_reference_ci_method`
  - requirement: `truth_se_target_ratio` (default: reference truth SE must be ≤ ε/10 for tasks using ε)

**Error propagation rule (required when truth is reference):**
- Any error metric that uses `truth_value` must also carry `truth_se` (or `truth_ci`) and report results with this uncertainty clearly labeled.

---

## 4. Protocol taxonomy and required baselines

A defensible benchmark requires both:
- *strong* direct-measurement baselines for the relevant workload, and
- at least one shadows-family protocol.

### 4.1 Direct measurement baselines (required)

**A. Direct-naive (sanity baseline; required)**
- Measure each observable separately in a compatible basis.
- Simple shot allocation (e.g., equal).
- Purpose: correctness and baseline reference.

**B. Direct with commuting grouping (strong baseline; required)**
- Partition Pauli observables into commuting families.
- Each family measured in a shared basis setting.
- Must verify commutation and basis construction correctness (unit tests required).

**C. Direct with optimized allocation (best-case direct baseline; required)**
- Optimize shot allocation across observables or groups under the benchmark criterion.
- Must record the optimization objective and constraints in the manifest.

### 4.2 Shadows-family protocols (minimum required + extensions)

**D. Local random-basis shadows (required)**
- Random local basis choices per shot (e.g., local Cliffords or Pauli bases).
- Snapshot-based estimation of many observables.

**E. Global Clifford shadows (recommended)**
- Random global Clifford per shot then computational-basis measurement.
- Record additional circuit depth and 2Q gate counts; do not treat compilation overhead as free.

**F. Fermionic / matchgate-compatible shadows (extension; recommended for chemistry)**
- Measurement design and estimators adapted to fermionic operators and Gaussian structure where applicable.
- When used, explicitly state structural assumptions and benchmark against mapped-Pauli baselines.

**G. Locally-scrambled shadows (extension)**
- Structured shallow random local unitaries between local and global regimes.

### 4.3 Estimator modules (orthogonal to measurement ensemble)
Estimator modules must be composable across protocols:
- mean estimator
- robust estimators (e.g., median-of-means)
- bootstrap/batch CI estimators
- heavy-tail diagnostics (required for automatic CI selection; see §6)

### 4.4 Regime mapping (required reporting aid)
Benchmarks must include a short “expected regime behavior” table in reports to avoid misinterpretation.

Minimum dimensions:
- number of observables \(M\): small / medium / large
- locality: low-weight / high-weight
- commutation structure: mostly commuting / mostly non-commuting
- noise: ideal / moderate / high
- circuit depth: shallow / deep

Reports must explicitly include at least one regime where each protocol class is expected to **underperform** (§13.1).

---

## 5. Protocol interface contract (required; supports adaptive protocols)

All protocols must implement the same contract. The suite supports **static** and **adaptive** protocols.

### 5.1 Core interface (required)
A protocol implementation must provide:

- `initialize(observable_set, config, seed) -> ProtocolState`
- `next_plan(state, remaining_budget) -> MeasurementPlan`
- `acquire(circuit, plan, backend, seed) -> RawDatasetChunk`
- `update(state, data_chunk) -> ProtocolState`
- `finalize(state) -> Estimates`

Static (non-adaptive) protocols may implement:
- `next_plan` that returns a single plan consuming the full budget
- `update` that only accumulates data
- `finalize` that performs one-shot estimation

Adaptive protocols must record:
- number of rounds
- per-round classical time
- per-round settings and allocations
- stopping criteria if early stopping is used

### 5.2 MeasurementPlan (required fields)
A plan must define:
- list of measurement settings
- shot allocation per setting
- mapping of observables estimable from each setting
- any pre-rotations / metadata required for acquisition
- planned per-setting circuit modifications (if any)

### 5.3 Estimates object (required fields)
For each observable:
- `estimate`
- uncertainty outputs: `se` and/or (`ci_low`, `ci_high`)
- diagnostics (effective sample size proxy, tail flags, batch stats)
- (optional) estimator method ID/version

---

## 6. Uncertainty estimation and confidence intervals (required methodology)

### 6.1 CI conventions (mandatory)
Every CI must specify:
- confidence level (default 95%)
- CI method (normal/t, bootstrap, robust/bootstrap-on-blocks, conservative bounded)
- parameters (bootstrap replicates, block size, etc.)
- whether bounds were clamped to a valid range (e.g., [-1,1])

If bounds are clamped:
- store both `ci_low_raw/ci_high_raw` and `ci_low/ci_high` (clamped) to preserve calibration analysis.

### 6.2 Default CI selection policy (required)
The suite must implement a deterministic rule for selecting CI method (with config overrides).

**Default A: Normal/t CI**
Eligible when:
- effective sample size for the observable ≥ `ci_normal_min_n` (default 100), **and**
- heavy-tail diagnostics are below thresholds.

**Default B: Bootstrap CI**
Used when:
- effective sample size < threshold, or
- heavy-tail diagnostics trigger, or
- estimator is known to be non-Gaussian.

Recommended defaults:
- `bootstrap_replicates = 1000`
- use block/bootstrap-on-batches when data are naturally batched (e.g., MoM blocks).

**Optional C: Conservative bounded-variable CI**
Offered when samples are bounded and i.i.d. (e.g., direct Pauli measurement outcomes in {-1,+1}):
- provides conservative coverage guarantees
- may be used for sanity checks and auditability

### 6.3 Heavy-tail diagnostics (recommended but strongly encouraged)
Record diagnostics per observable such as:
- variance across MoM blocks
- outlier rates / trimmed statistics
- effective sample size proxy

Use diagnostics to:
- select CI method automatically
- explain failures of normal approximation
- justify robust estimator usage

### 6.4 Calibration / coverage evaluation (required when reporting CIs)
Two coverage notions must be reported:

**Per-observable coverage**
\[
\Pr(o_i \in \mathrm{CI}_i) \approx 1-\alpha
\]

**Family-wise (simultaneous) coverage** (required when claiming “all observables meet target”)
\[
\Pr(\forall i,\ o_i \in \mathrm{CI}_i) \approx 1-\delta
\]
See §8 for multiple comparisons control.

---

## 7. Multiple comparisons and simultaneous inference (required for publishable rigor)

When estimating many observables, per-observable 95% intervals do **not** imply “95% confidence that all observables are accurate.” Any “all observables” claim must define and control a **global failure probability** \(\delta\).

### 7.1 Global error budgets
The suite must support two global regimes:

- **FWER / simultaneous guarantees** (strong):
  - control probability of *any* CI failure across the family
  - required for tasks that assert “all observables are within ε” (worst-case tasks)

- **FDR (false discovery rate)** (weaker; optional):
  - suitable when identifying which observables are “good” rather than guaranteeing all are good

Default benchmark claims should use **FWER** unless explicitly stated otherwise.

### 7.2 Default FWER control methods (required)
Implement at least:

**Bonferroni correction (default, conservative)**
- Global failure probability: \(\delta\)
- Per-observable significance: \(\alpha_i = \delta/M\)
- Build each CI at confidence \(1-\alpha_i\).

**Šidák correction (optional, slightly tighter under independence)**
- \(\alpha_i = 1-(1-\delta)^{1/M}\)

**Holm–Bonferroni (optional, tighter step-down)**
- Requires p-values or ordered CI procedures; include if implementing.

### 7.3 How this changes stopping rules and tasks (mandatory)
Any stopping rule that checks “all observables meet target” must:
- choose a global \(\delta\)
- build simultaneous CIs using an FWER method
- assert target satisfaction only if simultaneous criteria are met

Example stopping criterion (CI half-width based):
- stop at smallest \(N\) such that for all \(i\),
  - CI half-width ≤ ε, **and**
  - CI constructed at global FWER δ.

### 7.4 Reporting requirements (mandatory)
For any report making an “all observables” claim:
- state \(\delta\) explicitly (e.g., δ = 0.05)
- state multiple-comparisons method (Bonferroni / Šidák / Holm)
- report both:
  - per-observable coverage
  - family-wise coverage (empirical estimate across repetitions)

---

## 8. Benchmark tasks (decision problems)

Tasks define how to compute \(N^\*\), curves, and comparisons.

Let:
- \(M\) = number of observables
- \(N\) = total shots
- \(R\) = number of independent repetitions

### Task 1 — Worst-case guarantee (simultaneous; required)
**Objective:** minimal \(N\) such that **all** observables meet target at global confidence \(1-\delta\).

Default criterion (CI-based, FWER-corrected):
- For each observable \(i\), compute a simultaneous CI at global δ (§7).
- Stop when each CI half-width ≤ ε.

Truth-based alternative (preferred in simulation with exact truth):
- Stop when \(\max_i |\widehat{o}_i - o_i| \le \varepsilon\) in a high-probability sense; report empirical success probability across repetitions.

Outputs:
- \(N^\*(\varepsilon,\delta)\)
- worst offenders
- SSF vs baselines

### Task 2 — Average/weighted accuracy target
**Objective:** minimal \(N\) such that average criterion meets target (specify whether global δ applies).

Common variants:
- mean CI half-width ≤ ε
- coefficient-weighted mean (Hamiltonian coefficients)
- energy estimator CI half-width ≤ ε

Outputs:
- \(N^\*\) per variant
- sensitivity to weighting

### Task 3 — Fixed-budget distribution (required)
**Objective:** compare distributions of uncertainty and truth-error across observables at fixed \(N\).

Report:
- percentiles (median/90%/95%/max)
- CDF curves
- attainment fraction vs ε

### Task 4 — Dominance and crossover (required)
**Objective:** determine shot budgets where one protocol dominates another.

Two versions:
- uncertainty-based dominance (using simultaneous CIs where appropriate)
- truth-based dominance (preferred in simulation)

Report:
- crossover point(s) if they exist
- observables preventing dominance otherwise

### Task 5 — Pilot-based selection (meta-protocol; required)
**Objective:** allocate a pilot budget to predict which protocol reaches target fastest; quantify regret.

Report:
- selection accuracy
- regret vs oracle
- robustness under noise and miscalibration

### Task 6 — Bias-variance decomposition (required in simulation; recommended otherwise)
**Objective:** separate systematic bias from variance.

For each observable:
- bias across repetitions
- variance across repetitions
- RMSE

Aggregate:
- mean/max bias, distribution of biases
- bias-vs-noise-level curves

### Task 7 — Noise sensitivity and robustness (recommended; required for hardware claims)
**Objective:** evaluate performance degradation as noise increases or backend varies.

Report vs noise profile parameter:
- \(N^\*(\varepsilon,\delta)\) curves
- coverage degradation
- failure rates (e.g., no convergence within N_max)
- crossovers that change under noise

### Task 8 — Adaptive protocol efficiency (recommended)
**Objective:** compare adaptive vs non-adaptive under the same budgets and accounting rules.

Report:
- total classical time + rounds
- whether adaptivity changes shots-to-target
- whether adaptivity changes robustness/coverage

---

## 9. Experimental methodology (execution rules)

### 9.1 Shot schedules (explicit; required)
Use an explicit grid; default geometric progression:
- `N_min`, `N_max`, `ratio`
- `N_k = round(N_min * ratio^k)` until `N_k <= N_max`
Store the resolved list `N_grid` in the manifest.

### 9.2 Repetitions and seeding (required)
For each (circuit, observable set, protocol, N), run \(R\) repetitions.

Required seeds:
- `seed_protocol` (planning randomness)
- `seed_acquire` (sampling randomness)
- `seed_bootstrap` (if bootstrap used)
- For adaptive protocols: `seed_policy`

Record all seeds in the manifest per repetition.

### 9.3 Fairness constraints (required)
- Same total shot budget \(N\) for fixed-budget tasks.
- If a protocol uses deeper circuits, record depth/gate counts and quantum runtime.
- For grouped baselines, reuse outcomes only when observables commute and share a measurable basis.

### 9.4 Canonical noise profiles (required when evaluating noise)
Define a standard library of noise profiles. Each profile must have:
- `noise_profile_id`
- explicit parameters
- backend implementation mapping

Minimum required profiles:
1. `ideal` (no noise)
2. `readout_bitflip(p)` with p in {1e-3, 1e-2, 5e-2}
3. `depolarizing_1q(p1) + depolarizing_2q(p2)` with (p1,p2) in {(1e-4,1e-3), (1e-3,1e-2), (1e-2,5e-2)}
4. `amplitude_phase_damping(T1,T2,dt)` or equivalent parameterization (optional but recommended)

Noise profiles must be referenced by ID in configs and logged in manifests.

### 9.5 Hardware execution guidelines (required if hardware is used)

Hardware introduces non-i.i.d. variability; the suite must record enough metadata to interpret results.

**Queue time and scheduling**
- Record job submission/start/end times and queue time.
- Prefer contiguous batches to reduce drift.

**Calibration drift**
- Record calibration metadata before and after an experiment batch.
- Define `max_batch_duration_s`; if exceeded, mark runs as drift-risk.

**Connectivity and compilation**
- Record coupling map/topology and compilation settings.
- Record post-compilation depth and 2Q gate count.

**Failures and partial data**
- Preserve partial outputs with explicit run status:
  - `success`, `partial_success`, `failed`
- Never silently drop failed runs.

---

## 10. Data model and outputs (required schema)

### 10.1 Long-form results table (required)
Each row corresponds to:
- one repetition
- one protocol
- one circuit instance
- one shot budget
- one observable

Minimum required columns:

**Identifiers**
- `run_id`, `methodology_version`
- `circuit_id`, `observable_set_id`, `observable_id`
- `protocol_id`, `protocol_version`
- `backend_id`, `noise_profile_id`
- `replicate_id`, seeds

**Problem descriptors**
- `n_qubits`, `circuit_depth`, `twoq_gate_count`
- `observable_type`, `locality`
- `coefficient`, `group_id`
- `M_total`

**Budget/resources**
- `N_total`, `n_settings`
- `time_quantum_s`, `time_classical_s`
- `memory_bytes`
- optional: `cost_model_id`, `cost_usd_estimate`
- hardware: `job_status`, `queue_time_s`, timestamps

**Estimation**
- `estimate`
- `se`
- `ci_low_raw`, `ci_high_raw` (nullable if not applicable)
- `ci_low`, `ci_high` (clamped if required)
- `ci_method_id`
- `truth_value` (nullable)
- `truth_se` (nullable)
- derived: `abs_err`, `sq_err`

### 10.2 Storage and scalability requirements
- Use **Parquet** as default storage for long-form outputs.
- Partition/shard by a stable scheme, e.g.:
  - `run_id/` then `protocol_id/` then `N_total=.../part-*.parquet`
- Store summary tables separately to avoid reading full raw data for common analyses.
- Raw per-shot datasets are optional and may be stored only for small runs or audit runs; if stored, they must be referenced in the manifest.

### 10.3 Summary tables (required)
Produce at least:
- per (protocol, circuit, N): percentile summaries + attainment fraction
- per (protocol, circuit): \(N^\*(\varepsilon,\delta)\) for each task
- coverage summaries:
  - per-observable coverage
  - family-wise coverage for simultaneous tasks

### 10.4 Required plots (required)
At minimum:
- attainment vs N
- shots-to-target comparisons for Tasks 1–2
- CDFs of uncertainty and truth-error at fixed N
- coverage plots (per-observable and family-wise)
- runtime vs M and runtime vs N (recommended)
- settings count vs N (recommended)
- regime maps (recommended): SSF heatmaps vs (M, locality, noise)

Plots must:
- label protocols, ε, δ, CI method, noise profile
- include error bands across repetitions where applicable

---

## 11. Testing and validation (required)

### 11.1 Unit tests (required)
- shot accounting correctness
- commutation/grouping correctness
- estimator sanity on simple states
- reproducibility with fixed seeds on deterministic backends
- CI monotonicity: CI width decreases with N under i.i.d. conditions

### 11.2 Integration tests (required)
- end-to-end benchmark on small circuits (n ≤ 6), small M, multiple protocols, multiple N, multiple repetitions
- schema validation for Parquet outputs
- truth-mode validation (exact vs reference)
- regression tests for output schema and key metrics

### 11.3 Edge-case stress tests (required)
Include at least:
- n=1, M=1
- M very large with small n (data volume/throughput)
- extreme noise profile (to test failure modes and reporting)
- empty/invalid observable set handling (should fail fast)

### 11.4 Statistical validation (recommended)
- coverage calibration (per-observable and family-wise)
- bias detection tests on known states
- heavy-tail diagnostic triggers tested on adversarial observables

---

## 12. Required notebooks (executable specifications)

Notebooks serve as living documentation and regression catchers.

### Notebook A — Protocol smoke tests (required)
- exercises every protocol
- validates schema + shot accounting

### Notebook B — Ground truth validation and calibration (required)
- exact truth on small n
- bias/variance/RMSE scaling
- per-observable and family-wise coverage evaluation

### Notebook C — Commuting grouping baseline study (required)
- grouping construction + correctness
- direct-naive vs grouped vs optimized allocation
- group size statistics

### Notebook D — Scaling with number of observables (required)
- vary M (10, 100, 1k, 5k, …)
- shots-to-target + runtime vs M

### Notebook E — Scaling with locality (required)
- sweep locality/weight
- show regime where shadows may degrade

### Notebook F — Fixed-budget distribution analysis (required)
- CDFs/percentiles at fixed N
- attainment curves across ε

### Notebook G — Uncertainty calibration and diagnostics (required)
- CI method comparisons (normal vs bootstrap)
- heavy-tail diagnostics demonstration
- calibration failures highlighted and explained

### Notebook H — Pilot-based selection and regret (required)
- pilot fraction sweep
- selection accuracy and regret under noise

### Notebook I — Noise and hardware-readiness (required for hardware claims)
- canonical noise profile sweeps
- optional hardware pilot with metadata logging
- partial-job handling demonstration

### Notebook J — Multiple comparisons and simultaneous inference (required for publishable “all observables” claims)
- demonstrate Bonferroni/Šidák/optional Holm
- compare per-observable vs family-wise coverage
- show impact on stopping rules and N*

---

## 13. Reporting standards (required)

### 13.1 Negative and null results (mandatory policy)
Benchmarks must reveal regimes where protocols do not improve efficiency.

Requirements:
- report SSF < 1 outcomes explicitly
- avoid cherry-picking circuits or observable sets
- provide regime maps across:
  - M, locality, noise, circuit family
- include at least one benchmark where each protocol class loses

### 13.2 Claims checklist (mandatory in reports)
Any report that claims:
- “Protocol A is better than B”
must specify:
- the task definition (which criterion)
- ε and δ
- CI method + multiple comparisons method (if applicable)
- baselines included
- backend and noise profile
- resource profile beyond shots (runtime, settings, memory)

### 13.3 Hardware claim policy
If presenting hardware results:
- include at least one simulation benchmark matched to the hardware circuit family and observable set
- include hardware metadata (queue time, calibration snapshots, compilation metrics)
- avoid over-interpreting small-N regimes without calibration evidence

---

## 14. Implementation guidance for QuartumSE

### 14.1 Repository layout (recommended)
QuartumSE uses `src/quartumse/`:

- `src/quartumse/`
  - `protocols/` (direct + shadows + adaptive)
  - `estimators/` (mean, MoM, CI, bootstrap, diagnostics)
  - `observables/` (representations + generators + grouping)
  - `backends/` (ideal/noisy simulators + optional hardware)
  - `benchmarks/` (tasks + sweeps + aggregation + plotting + cost models)
  - `io/` (schemas + parquet + manifests)
  - `tests/` (unit + integration + stress)
- `notebooks/` (A–J)
- `configs/`
- `reports/`

### 14.2 Backend adapter contract (recommended)
Be explicit about supported backends and keep adapters small:
- ideal sampler
- noisy sampler
- optional SDK adapters (Qiskit/Cirq/etc.) as separate modules

If multiple SDKs are supported:
- add adapter conformance tests (same circuit + seed yields consistent ideal probabilities).

### 14.3 Protocol IDs and deprecation policy (required for reproducibility)
All protocols must have:
- stable `protocol_id` (human-readable)
- semantic `protocol_version`
- code provenance via git commit hash in manifest

Deprecation:
- old protocol versions must remain runnable, or
- provide a migration tool plus a mapping from old IDs/versions to new.

---

## 15. Optional cost model (hardware economics)

Because platforms may bill by runtime/credits:
- treat monetary cost as optional derived output
- require raw resource recording (quantum runtime, settings, depth, gate counts)
- implement pluggable `CostModel`:
  - `cost_model_id`
  - `cost_inputs`
  - computed `cost_estimate` (USD/credits)

Reports should present:
- shots-to-target and cost-to-target side-by-side when cost is available.

---

## 16. Glossary

- **Shot**: one circuit execution and measurement outcome.
- **Setting**: a measurement configuration reused across shots.
- **Observable**: Hermitian operator whose expectation is estimated.
- **Estimator**: maps raw data to estimate + uncertainty.
- **Per-observable coverage**: CI contains truth for a given observable.
- **Family-wise coverage**: all CIs simultaneously contain truth.
- **FWER**: family-wise error rate control (strong).
- **FDR**: false discovery rate control (weaker).
- **Shot-savings factor (SSF)**: ratio of shots-to-target between baseline and protocol.

---

## 17. Minimal acceptance checklist

Before using results for scientific or commercial claims:

- [ ] Strong baselines included (direct grouping + optimized allocation).
- [ ] Exact truth used when feasible; otherwise reference truth with uncertainty.
- [ ] ε and δ defined for all tasks; multiple comparisons handled for “all observables” claims.
- [ ] Per-observable and family-wise coverage evaluated where CIs are used.
- [ ] Observable set generation is seeded and fully specified.
- [ ] Noise profiles use canonical IDs and parameters.
- [ ] Resource metrics beyond shots are recorded and reported.
- [ ] Outputs stored in Parquet with validated schema; summaries and plots generated.
- [ ] Negative/null regimes are included and reported.
- [ ] Notebooks A, B, J run end-to-end for any publishable claim involving simultaneous guarantees.

---

## 18. Implementation roadmap

This section defines the phased implementation plan to bring QuartumSE into full compliance with this methodology specification.

### 18.1 Current state assessment

**Implemented:**
- Classical shadows v0 (local random Clifford) and v1 (noise-aware with MEM)
- Basic provenance/manifest system with Parquet shot data persistence
- IBM Quantum backend integration with calibration snapshot capture
- Bootstrap CI computation (partial)

**Critical gaps:**
- No direct-measurement baselines (§4.1 A-C)
- Protocol interface does not match §5 contract
- No seeded observable generators (§3.3)
- No FWER/multiple comparisons control (§7)
- No benchmark tasks implemented (§8)
- Required notebooks missing (§12)

### 18.2 Implementation phases

#### Phase 0: Foundation (estimated: 2 weeks)

**0.1 Protocol interface contract**
```
src/quartumse/protocols/
├── base.py           # Protocol ABC with initialize/next_plan/acquire/update/finalize
├── registry.py       # Protocol registration with ID and version
├── state.py          # ProtocolState, MeasurementPlan, RawDatasetChunk, Estimates
└── __init__.py
```

Key deliverables:
- `Protocol` abstract base class implementing §5.1
- `MeasurementPlan` dataclass implementing §5.2
- `Estimates` dataclass implementing §5.3
- Protocol registry with `protocol_id` and `protocol_version`

**0.2 Observable infrastructure**
```
src/quartumse/observables/
├── core.py           # Observable, ObservableSet with full metadata
├── generators.py     # Seeded generators per §3.3
├── grouping.py       # Commutation analysis and grouping algorithms
├── metadata.py       # observable_id, locality, group_id tracking
└── __init__.py
```

Key deliverables:
- `ObservableSet` class with required metadata (§3.2)
- `ObservableGenerator` base class with seeded generation
- Required generators: RandomPauli, Hamiltonian, Correlator, ClusteredSupport
- Commutation checker and grouping algorithm

**0.3 Data model infrastructure**
```
src/quartumse/io/
├── schemas.py        # Pydantic models for §10.1 long-form schema
├── long_form.py      # LongFormResultBuilder
├── parquet_io.py     # Partitioned Parquet I/O
├── summary.py        # Summary table aggregation (§10.2)
└── __init__.py
```

Key deliverables:
- `LongFormRow` Pydantic model matching §10.1 exactly
- Parquet writer with partitioning: `run_id/protocol_id/N_total=.../`
- Summary table aggregator

#### Phase 1: Baselines (estimated: 2 weeks)

**1.1 Direct-naive baseline (§4.1A)**
- File: `src/quartumse/protocols/direct_naive.py`
- Per-observable basis rotation circuits
- Equal shot allocation
- Sample mean estimator with variance/SE

**1.2 Direct with commuting grouping (§4.1B)**
- File: `src/quartumse/protocols/direct_grouped.py`
- Commutation graph construction
- Graph coloring for minimum groups
- Shared basis construction per group
- Unit tests: commutation verification, basis correctness

**1.3 Direct with optimized allocation (§4.1C)**
- File: `src/quartumse/protocols/direct_optimized.py`
- Variance-proportional allocation
- Optimization solver for target precision
- Record optimization objective in manifest

**1.4 Refactor existing shadows**
- Files: `src/quartumse/protocols/shadows_local.py`, `shadows_local_mem.py`
- Wrap v0/v1 implementations in Protocol ABC
- Backward compatibility layer

#### Phase 2: Statistical infrastructure (estimated: 2 weeks)

**2.1 CI methodology (§6)**
```
src/quartumse/estimators/
├── mean.py           # Standard mean estimator
├── robust.py         # Median-of-means, trimmed mean
├── ci.py             # CI construction (normal, bootstrap, bounded)
├── diagnostics.py    # Heavy-tail detection, effective sample size
├── selector.py       # Automatic CI method selection (§6.2)
└── __init__.py
```

Key deliverables:
- `CIMethod` enum and `CIResult` with raw/clamped bounds
- Heavy-tail diagnostics (§6.3)
- Automatic CI selection policy (§6.2)

**2.2 Multiple comparisons control (§7)**
- File: `src/quartumse/estimators/multiple_comparisons.py`
- Bonferroni correction (required)
- Šidák correction (optional)
- Holm-Bonferroni step-down (optional)
- Integration with stopping rules (§7.3)

**2.3 Coverage evaluation**
- File: `src/quartumse/estimators/coverage.py`
- Per-observable and family-wise coverage computation
- Under/over-coverage diagnosis

#### Phase 3: Benchmark tasks (estimated: 2 weeks)

**3.1 Task framework**
- File: `src/quartumse/benchmarks/tasks/base.py`
- `BenchmarkTask` ABC with `criterion_met()` and `compute_result()`

**3.2 Individual tasks (§8)**
```
src/quartumse/benchmarks/tasks/
├── base.py
├── task1_worstcase.py    # Worst-case guarantee (FWER)
├── task2_average.py      # Average/weighted accuracy
├── task3_distribution.py # Fixed-budget distribution
├── task4_dominance.py    # Dominance and crossover
├── task5_pilot.py        # Pilot-based selection
├── task6_biasvar.py      # Bias-variance decomposition
├── task7_noise.py        # Noise sensitivity
├── task8_adaptive.py     # Adaptive protocol efficiency
└── __init__.py
```

**3.3 Sweep orchestrator**
- File: `src/quartumse/benchmarks/sweep.py`
- Shot schedule generation (§9.1)
- Repetition management with seed tracking (§9.2)
- Long-form output generation
- Task result computation

#### Phase 4: Noise and hardware (estimated: 1 week)

**4.1 Canonical noise profiles (§9.4)**
- File: `src/quartumse/backends/noise_profiles.py`
- `IdealProfile`, `ReadoutBitflipProfile`, `DepolarizingProfile`
- Profile registry with ID lookup

**4.2 Hardware execution guidelines (§9.5)**
- File: `src/quartumse/backends/hardware.py`
- Queue time tracking
- Calibration drift detection
- Job status tracking

#### Phase 5: Visualization and reporting (estimated: 1-2 weeks)

**5.1 Required plots (§10.4)**
- File: `src/quartumse/benchmarks/plotting.py`
- Attainment vs N curves
- Shots-to-target comparisons
- CDF plots, coverage plots
- Regime maps (SSF heatmaps)

**5.2 Report generator**
- File: `src/quartumse/benchmarks/report.py`
- Markdown/HTML report template
- Claims checklist (§13.2) auto-population
- Negative results section (§13.1)

**5.3 Cost model (§15)**
- File: `src/quartumse/benchmarks/cost_model.py`
- Pluggable `CostModel` ABC
- `IBMRuntimeCostModel` implementation

#### Phase 6: Notebooks (estimated: 2 weeks)

Required notebooks per §12:
```
notebooks/
├── A_protocol_smoke_tests.ipynb
├── B_ground_truth_validation.ipynb
├── C_commuting_grouping_study.ipynb
├── D_scaling_observables.ipynb
├── E_scaling_locality.ipynb
├── F_fixed_budget_distribution.ipynb
├── G_uncertainty_calibration.ipynb
├── H_pilot_selection.ipynb
├── I_noise_hardware.ipynb
└── J_multiple_comparisons.ipynb
```

### 18.3 Dependency graph

```
Phase 0 (Foundation) ──┬──► Phase 1 (Baselines) ──┐
                       │                          │
                       └──► Phase 2 (Statistics) ─┼──► Phase 3 (Tasks)
                                                  │         │
                                                  │    ┌────┴────┐
                                                  │    ▼         ▼
                                                Phase 4    Phase 5
                                                (Noise)   (Reporting)
                                                  │            │
                                                  └─────┬──────┘
                                                        ▼
                                                  Phase 6 (Notebooks)
```

### 18.4 Minimum viable for publication

Before any scientific claims can be made:

1. At least 2 direct-measurement baselines (grouped + optimized)
2. Tasks 1 and 3 operational (worst-case guarantee, distribution)
3. FWER control (Bonferroni minimum)
4. Notebooks A, B, J complete and passing
5. Long-form Parquet output with validated schema
6. At least one documented "negative result" regime (where shadows lose)

### 18.5 Success criteria

**Full Bible compliance requires:**
- [ ] All 8 tasks operational
- [ ] All 10 notebooks complete and passing
- [ ] Canonical noise profile library
- [ ] Hardware execution guidelines implemented
- [ ] Cost model integrated
- [ ] Report generator producing publication-ready output
- [ ] All §17 checklist items satisfied

### 18.6 Estimated effort

| Phase | Duration | New code (LOC) |
|-------|----------|----------------|
| 0. Foundation | 2 weeks | 1,200-1,500 |
| 1. Baselines | 2 weeks | 800-1,000 |
| 2. Statistics | 2 weeks | 800-1,000 |
| 3. Tasks | 2 weeks | 1,000-1,200 |
| 4. Noise/Hardware | 1 week | 400-500 |
| 5. Reporting | 1-2 weeks | 800-1,000 |
| 6. Notebooks | 2 weeks | 3,500 (notebook lines) |
| **Total** | **10-13 weeks** | **~8,500-9,700** |
