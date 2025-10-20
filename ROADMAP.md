
# QuartumSE R&D‑Centric Roadmap (Updated, 2025–2026)

> **Principle:** Front‑load **research & hardware iteration**. Build on IBM Quantum free‑tier devices until we have an **attractive, validated, and patentable** measurement stack. Only then open **Early Access** for design partners.

This roadmap folds in: (i) a **sophisticated classical shadows** program, (ii) concrete **experiments & tests** mapped to each phase, and (iii) clear **publication/patent gates** before external onboarding.

---

## Glossary (metrics & terms)

- **SSR (Shot‑Savings Ratio):** shot‑count (baseline) ÷ shot‑count (QuartumSE) at equal error tolerance.
- **RMSE@$:** cost‑for‑accuracy — dollars (or credits/time) to reach a target RMSE on an observable/metric.
- **CI coverage:** frequency a 95% CI contains ground truth (simulation) or gold standard (hardware cross‑checks).
- **Provenance Manifest:** JSON artifact capturing circuits, calibrations, mitigations, backend, seeds, versions.
- **MEM / M3:** measurement error mitigation (confusion matrices); **ZNE:** zero‑noise extrapolation.
- **PEC:** probabilistic error cancellation; **RC:** randomized compiling.

---

## Program Structure at a Glance

- **Workstream S (Shadows):** Classical Shadows Engine v0→v4 (baseline → noise‑aware → fermionic → adaptive/derandomized → robust Bayesian/bootstrapped).
- **Workstream C (Chemistry/VQE):** Shadow‑VQE for small molecules (H₂, LiH, BeH₂).
- **Workstream O (Optimization/QAOA):** Shot‑frugal QAOA on MAX‑CUT & MIS toy instances.
- **Workstream B (Benchmarking):** RB/XEB/Quantum‑Volume + **Shadow‑Benchmarking** (fidelity/entropy/purity via shadows).
- **Workstream M (Metrology):** Variational entangled probes (GHZ/W states) for phase‑sensing toy tasks.
- **Workstream P (Provenance & Reporting):** Manifest schema, CI pipelines, PDF/HTML reports, reproducibility notebooks.

Each phase below enumerates **Experiments & Tests** with IDs that recur across phases for iteration & scaling.

---

## Phase 1 — Foundation & R&D Sprints (Now → Nov 2025)

**Focus:** Ship scaffolding *and* start real algorithmic experiments immediately (sim + small IBM jobs).

### Objectives
- Solidify repository, CI/CD, SDK skeleton, provenance/reporting.
- Implement **Shadows v0** (random local Clifford) + **v1** (noise‑aware inverse‑channel + MEM).
- Stand up baseline **C**, **O**, **B**, **M** toy pipelines against Aer simulator and at least one IBM free‑tier backend.
- Deliver a tractable **test suite** and benchmarking harness (pytest + notebooks).

### Deliverables
- SDK modules: `Estimator`, `Shadows`, `Report`; **Provenance Manifest v1**; quickstart notebook.
- Mitigation core: **MEM (M3)**, **ZNE**, plugin hooks for **PEC/RC**.
- **Shadows v0–v1** reference implementation with CI. 
- Test harness: datasets, seeds, fixtures; storage: Parquet/DuckDB; PDF/HTML report.
- **Internal whiteboard spec** for patent themes (see Phase 2 gate).

### Experiments & Tests (P1)
- **S‑T01 (Shadows‑Core):** Random local Clifford shadows on GHZ(3–5), Bell pairs; estimate ⟨Zᵢ⟩, ⟨ZᵢZⱼ⟩, purity. *Targets:* CI coverage ≥ 0.9; SSR ≥ 1.2 on sim, ≥ 1.1 on IBM.
- **S‑T02 (Noise‑Aware):** Calibrate per‑qubit inverse channel; compare with/without MEM; compute variance reduction.
- **C‑T01 (H₂@STO‑3G):** Hardware‑efficient VQE (depth ≤ 2) + **Shadows readout** of Hamiltonian terms; energy error ≤ 50 mHa (sim), ≤ 80 mHa (IBM).
- **O‑T01 (MAX‑CUT‑5):** QAOA p∈{1,2} on 5‑node ring; shot‑frugal optimizer; compare cost estimate variance with/without Shadows proxy.
- **B‑T01 (RB/XEB):** 1–3 qubit RB; XEB on depth‑limited random circuits; log into Manifest; compare to IBM backend calibration metadata.
- **M‑T01 (GHZ‑Phase):** Prepare GHZ(3–4), encode small Z‑phase, estimate via optimal readout; CI coverage ≥ 0.8 on sim; explore ZNE for readout bias.

### Exit / Success Criteria
- End‑to‑end run from notebook → manifest → report on Aer + *at least one* IBM free‑tier backend.
- SSR ≥ **1.2×** on Shadows‑Core (sim) and ≥ **1.1×** (IBM).
- CI coverage ≥ 80%, zero critical issues, reproducible seeds & manifests.
- Patent themes shortlist (top‑3) + experiment data to support novelty.

---

## Phase 2 — Hardware‑First Iteration & Patent Drafts (Nov → Dec 2025)

**Focus:** Iterate **on hardware**. Elevate shadows & domain demos; lock initial patent filings; prep first papers.

### Objectives
- Implement **Shadows v2 (Fermionic)** for 2‑RDM estimation; integrate with VQE readout.
- Prototype **Shadows v3 (Adaptive/Derandomized)**: choose measurement ensembles to minimize estimator variance given target observable set.
- Harden error mitigation combinations (**MEM + RC + ZNE**) with ablation studies.
- Run structured **hardware campaigns** (blocked time windows) to control drift.

### Deliverables
- **IBM hardware campaign #1** dataset + full manifests + PDF/HTML reports.
- **Provisional patent** draft(s) for: **Variance‑Aware Adaptive Classical Shadows (VACS)**; **Shadow‑VQE readout** integration; **Shadow‑Benchmarking** workflow.
- Two **arXiv preprints**: (i) Shadows engine on IBM, (ii) Shadow‑VQE for H₂/LiH small‑basis.
- Updated SDK APIs (stabilize experimental flags), plus “replay from manifest” tooling.

### Experiments & Tests (P2)
- **S‑T03 (Fermionic‑Shadows):** Direct 2‑RDM from shadows; H₂/LiH energies within 40–60 mHa on IBM at ≤ baseline shots; **SSR ≥ 1.3×** (IBM).
- **S‑T04 (Adaptive/Derand):** Greedy/importance‑sampled basis selection vs plain random; measure variance ↓ ≥ 25% for fixed shots (IBM).
- **C‑T02 (LiH@Minimal):** VQE with **Shadow‑readout** vs grouped‑Pauli readout; RMSE@$ ↓ by ≥ 30% at matched error bars.
- **O‑T02 (MAX‑CUT‑6/7):** Depth‑aware layout + RC; shot‑allocation per‑iteration; track optimizer steps saved vs fixed‑shot budget.
- **B‑T02 (Shadow‑Benchmarking):** Estimate linear entropy, multi‑qubit purities, and fidelity to GHZ using the same shadows dataset; compare to direct methods; **sample‑efficiency ≥ 2×**.
- **M‑T02 (Variational‑Metrology):** Variational state+measurement co‑optimization for phase sensing; demonstrate > classical shot‑noise scaling on sim, and robust advantage trend on IBM within CI.

### Exit / Success Criteria (Gate to P3)
- **SSR ≥ 1.3× on IBM** for at least one domain test (Shadows‑Core or Fermionic‑Shadows).
- Draft **provisional patent(s) filed**; arXiv preprints ready.
- CI artifacts: reproducible notebooks, manifests, reports for all P2 tests.

---

## Phase 3 — Internal Validation & Publication/Patent Gate (Jan → Mar 2026)

**Focus:** Consolidate results; conduct controlled comparisons; submit publications; finalize patents. No external users yet.

### Objectives
- Build **automated benchmark suite**: GHZ, VQE(H₂, LiH, BeH₂), QAOA(MAX‑CUT‑k), Shadow‑Benchmarking panels.
- Statistical validation: **SSR**, **RMSE@$**, **CI coverage**, **reproducibility** (< 2% drift under re‑runs).
- Implement **Shadows v4 (Robust/Bayesian)**: bootstrap CI, variance debiasing, heteroscedastic weighting by device cal data.
- Prepare **journal submissions** (PRX Quantum/npjQI/Quantum) and **non‑provisional patent filings**.

### Deliverables
- Benchmark suite (pytest + CLI) with **per‑test Manifest templates** and reporting.
- Internal **whitepaper** and slide deck with full ablation matrices.
- Code‑frozen **R&D branch** tagged for archival reproducibility (DOI/Zenodo).

### Experiments & Tests (P3)
- **S‑T05 (Robust‑Shadows):** Bootstrap CI coverage ≥ 0.9 on sim and ≥ 0.85 on IBM across GHZ and small‑chemistry states.
- **C‑T03 (BeH₂@Minimal):** Shadow‑VQE energy within 80–100 mHa on IBM; **RMSE@$** ↓ ≥ 35% vs grouped‑Pauli baseline.
- **O‑T03 (MAX‑CUT‑7)** and **O‑T04 (MIS‑6):** Evaluate solution quality vs shots; show **optimizer steps ↓ ≥ 20%** using shot‑frugal and variance‑aware estimates.
- **B‑T03 (Cross‑Provider Sim):** Aer vs IBM reproducibility; manifest “replay” round‑trip equality.
- **M‑T03 (Sensor‑Tuning):** Variational probe robustness to readout noise; CI width ↓ 15–25% after robust shadows weighting.

### Exit / Success Criteria (Gate to Early Access)
- **SSR ≥ 1.5×** achieved on internal benchmarks; **RMSE@$** consistently better than baselines.
- **At least one paper accepted** (or under strong revise‑&‑resubmit) and **patents filed**.
- **Provenance & replay** validated; CI green across full suite.

> **Only once the above gates are cleared do we begin external onboarding.**

---

## Phase 4 — Early Access (Design Partners) & Multi‑Provider Expansion (Apr → Jun 2026)

**Focus:** Limited Early Access after patents/papers. Add AWS Braket connector. Gather external evidence on real workloads.

### Objectives
- Onboard 2–3 design partners (academia/industry) with NDAs referencing filed IP.
- Implement **AWS Braket connector**; cross‑provider parity and consistency tests.
- Partner‑coauthored case studies; feedback loop into APIs & docs.

### Deliverables
- Partner playbooks; onboarding notebooks; Slack/Discord channels.
- Cross‑provider tests: same circuits on IBM vs AWS; delta analysis reported.
- Case study draft(s) + testimonial(s).

### Experiments & Tests (P4)
- **B‑T04 (Cross‑Provider Parity):** Within 10% agreement on observables post‑mitigation across IBM/AWS for GHZ and VQE(H₂) tasks.
- **C‑T04 (Partner‑Chemistry):** Run partner‑provided small chemistry model; maintain **SSR ≥ 1.5×**.
- **O‑T05 (Partner‑Optimization):** QAOA on a partner toy instance; capture wall‑clock + cost deltas in RMSE@$.
- **S‑T06 (Partner‑Shadows):** Validate adaptive shadows on partner circuits; document any domain‑specific gains.

### Exit / Success Criteria
- ≥3 partners actively running; parity across providers; partner satisfaction survey ≥ 8/10.
- External replication of **SSR ≥ 1.5×**; stable APIs for public beta drafting.

---

## Phase 5 — Public Beta & Pilot Conversion (Jul → Sep 2026)

**Focus:** Stabilize and open up. Convert Early Access into pilots. Prepare commercial posture.

### Objectives
- Public Beta (v1.0) on PyPI + GitHub; full docs; examples; tutorials.
- Secure 2–3 pilot customers/LOIs; webinar/demo using published results.
- Verify **SSR ≥ 2.0×** in multi‑provider benchmarks; publish follow‑ups.

### Deliverables
- v1.0 release; docs portal; community channels; issue triage.
- Pilot SOW templates; pricing experiments around RMSE@$ value metric.
- Public benchmark report with manifests for community reproduction.

### Experiments & Tests (P5)
- **B‑T05 (Public Benchmarks):** Community‑reproducible GHZ/VQE/QAOA panels with manifests and reference CI.
- **C‑T05 (Chemistry‑Scale‑Up):** Largest feasible molecule instance on accessible hardware; publish shot & cost curves.
- **S‑T07 (Shadows‑Ablation Public):** Public ablation notebook isolating contributions from v0→v4 components.

### KPIs
- ≥5 orgs using (3 design partners + ≥2 pilots); ≥2 paying/committed customers.
- Verified **SSR ≥ 2.0×** on multi‑provider suite; community replications reported.

---

## Algorithm & Test Matrix (IDs referenced above)

| ID | Category | Technique | Circuits / Instances | Backends | Primary Metrics | Evidence Artifacts |
|---:|---|---|---|---|---|---|
| S‑T01 | Shadows | v0 (random local Clifford) | Bell, GHZ(3–5) | Aer, IBM free‑tier | SSR, CI coverage | Manifest, notebook, PDF |
| S‑T02 | Shadows | v1 (noise‑aware + MEM) | As above | Aer, IBM | Var. reduction, bias | Manifest, ablation table |
| S‑T03 | Shadows | v2 (fermionic) | H₂/LiH 2‑RDM | Aer, IBM | Energy error, SSR | Manifest, data parquet |
| S‑T04 | Shadows | v3 (adaptive/derand) | Target Pauli sets | Aer, IBM | Variance ↓ | Manifest, policy snapshot |
| S‑T05 | Shadows | v4 (robust/Bayesian) | GHZ + chemistry | Aer, IBM | CI coverage, width | Manifest, bootstrap logs |
| C‑T01 | Chemistry | VQE + Shadow readout | H₂@STO‑3G | Aer, IBM | Energy error, RMSE@$ | Manifest, report |
| C‑T02 | Chemistry | Shadow‑VQE vs grouped | LiH@minimal | Aer, IBM | RMSE@$ ↓ | Notebook, plot |
| C‑T03 | Chemistry | Scale‑up | BeH₂@minimal | Aer, IBM | Energy error, SSR | Manifest, report |
| C‑T04 | Chemistry | Partner task | Partner circuit | IBM/AWS | SSR ≥1.5× | Case study |
| C‑T05 | Chemistry | Public benchmark | Largest feasible | IBM/AWS | Shot & cost curves | Public repo |
| O‑T01 | Optimization | QAOA p≤2 | MAX‑CUT‑5 | Aer, IBM | Cost var., steps | Manifest, runtime logs |
| O‑T02 | Optimization | Shot‑frugal + RC | MAX‑CUT‑6/7 | IBM | Steps ↓, RMSE@$ | Report |
| O‑T03 | Optimization | MIS‑6 | MIS‑6 | IBM | Quality vs shots | Manifest |
| O‑T04 | Optimization | MAX‑CUT‑7 | MAX‑CUT‑7 | IBM | Steps ↓ | Logs |
| O‑T05 | Optimization | Partner task | Partner graph | IBM/AWS | RMSE@$ | Case study |
| B‑T01 | Benchmark | RB/XEB | 1–3q RB; XEB | IBM | Gate error trends | Manifest, plots |
| B‑T02 | Benchmark | Shadow‑Benchmarking | Purity, entropy, GHZ‑Fid | IBM | Sample‑efficiency | Report |
| B‑T03 | Benchmark | Reproducibility | Aer vs IBM | Aer/IBM | Replay fidelity | Replay manifests |
| B‑T04 | Benchmark | Cross‑provider | IBM vs AWS | IBM/AWS | Parity | Report |
| B‑T05 | Benchmark | Public suite | Community panels | All | Replications | Public repo |
| M‑T01 | Metrology | GHZ phase toy | GHZ(3–4) | Aer/IBM | CI cov. | Manifest |
| M‑T02 | Metrology | Variational | GHZ/W | Aer/IBM | Advantage trend | Logs |
| M‑T03 | Metrology | Robust probes | GHZ k‑qubit | Aer/IBM | CI width ↓ | Report |

---

## Governance, Gating & Quality

- **Gates:** P2→P3 requires IBM **SSR ≥ 1.3×**; P3→P4 requires **SSR ≥ 1.5×** + patent(s) filed + ≥1 paper accepted/near‑accept; P4→P5 requires cross‑provider parity and partner replication of SSR.
- **Reproducibility:** Every result ships with a **Manifest**, raw parquet shot data, and a replay notebook.
- **Risk controls:** Time‑boxed hardware campaigns; ablations to isolate mitigation effects; fail‑closed CI (no release if tests or coverage gates fail).

---

## Timeline (target)

| Phase | Focus | Key Milestone | Target Date |
|---|---|---|---|
| P1 | Foundation & R&D sprints | First IBM runs + Shadows v1 | **Nov 2025** |
| P2 | Hardware‑first iteration | IBM campaign #1 + provisional patents + preprints | **Dec 2025** |
| P3 | Internal validation | SSR ≥1.5× + journal submits + non‑provisionals | **Mar 2026** |
| P4 | Early Access & expansion | 2–3 partners + AWS parity | **Jun 2026** |
| P5 | Public Beta | v1.0 + pilots | **Sep 2026** |

---

### Notes for Engineering

- Keep **device‑agnostic connectors**; IBM first, AWS next.
- Prefer **layout‑aware, shallow circuits**; re‑seed experiments; record cal snapshots.
- Implement **manifest replay** (offline) as a first‑class command; integrate with CI.
- Publish small, frequent preprints; convert to journals as results mature.
