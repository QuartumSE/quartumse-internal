"""Notebook F: Fixed-budget distribution analysis (CDFs/percentiles)."""
# %% [markdown]
# # Notebook F: Fixed-Budget Distribution Analysis
#
# Compare CDFs, percentiles, and attainment curves at a fixed shot budget.

# %%
from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from quartumse.benchmarking import simulate_protocol_execution
from quartumse.io import LongFormResultBuilder, LongFormResultSet
from quartumse.io.schemas import TaskResult
from quartumse.observables import generate_observable_set
from quartumse.protocols import DirectGroupedProtocol, DirectNaiveProtocol, DirectOptimizedProtocol
from quartumse.stats.confidence import normal_ci

sys.path.insert(0, str(Path(__file__).resolve().parent))
from notebook_utils import NotebookRunContext, finalize_notebook_run

# %% [markdown]
# ## 1. Configuration

# %%
SEED = 29
rng = np.random.default_rng(SEED)
N_QUBITS = 5
N_OBSERVABLES = 40
N_SHOTS = 1500
N_REPLICATES = 5
CONFIDENCE_LEVEL = 0.95

observable_set = generate_observable_set(
    generator_id="random_pauli",
    n_qubits=N_QUBITS,
    n_observables=N_OBSERVABLES,
    seed=SEED,
    max_weight=4,
)

true_expectations = {
    obs.observable_id: rng.uniform(-0.6, 0.6) for obs in observable_set.observables
}

protocols = [
    DirectNaiveProtocol(),
    DirectGroupedProtocol(),
    DirectOptimizedProtocol(),
]

# %% [markdown]
# ## 2. Simulated fixed-budget runs

# %%
result_set = LongFormResultSet()
run_id = "notebook_f_fixed_budget"

for replicate in range(N_REPLICATES):
    for protocol in protocols:
        estimates = simulate_protocol_execution(
            protocol=protocol,
            observable_set=observable_set,
            n_shots=N_SHOTS,
            seed=SEED + replicate,
            true_expectations=true_expectations,
        )

        for estimate in estimates.estimates:
            truth = true_expectations[estimate.observable_id]
            ci = normal_ci(
                estimate=estimate.estimate,
                se=estimate.se,
                confidence_level=CONFIDENCE_LEVEL,
            )

            row = (
                LongFormResultBuilder()
                .with_run_id(run_id)
                .with_methodology_version("3.0.0")
                .with_circuit("synthetic_circuit", n_qubits=N_QUBITS, depth=4)
                .with_observable(
                    observable_id=estimate.observable_id,
                    observable_type="pauli_string",
                    locality=estimate.metadata.get("locality", 1),
                    observable_set_id="random_pauli_fixed",
                    M_total=N_OBSERVABLES,
                )
                .with_protocol(protocol.protocol_id, protocol.protocol_version)
                .with_backend("synthetic", noise_profile_id="ideal")
                .with_replicate(replicate)
                .with_seeds(
                    seed_policy="seed+replicate",
                    seed_protocol=SEED,
                    seed_acquire=SEED + replicate,
                )
                .with_budget(N_total=N_SHOTS, n_settings=estimate.n_settings)
                .with_estimate(
                    estimate=estimate.estimate,
                    se=estimate.se,
                    ci_low=ci.ci_low,
                    ci_high=ci.ci_high,
                    ci_low_raw=ci.ci_low_raw,
                    ci_high_raw=ci.ci_high_raw,
                    ci_method_id=ci.method.value,
                    confidence_level=CONFIDENCE_LEVEL,
                )
                .with_truth(truth_value=truth, mode="synthetic")
                .build()
            )
            result_set.add(row)

# %% [markdown]
# ## 3. Distribution summaries

# %%
rows = pd.DataFrame(result_set.to_dicts())
rows["abs_error"] = rows["abs_err"]

percentiles = (
    rows.groupby("protocol_id")["abs_error"]
    .quantile([0.5, 0.9, 0.95])
    .unstack()
    .rename(columns={0.5: "p50", 0.9: "p90", 0.95: "p95"})
)
print(percentiles)

# %% [markdown]
# ## 4. CDF + attainment plots

# %%
plots_dir = Path("notebook_data/notebook_f_fixed_budget/plots")
plots_dir.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(7, 4))
for protocol_id, group in rows.groupby("protocol_id"):
    values = np.sort(group["abs_error"].values)
    cdf = np.arange(1, len(values) + 1) / len(values)
    ax.plot(values, cdf, label=protocol_id)

ax.set_xlabel("Absolute error")
ax.set_ylabel("CDF")
ax.set_title("Fixed-budget error CDF")
ax.legend()
fig.tight_layout()
fig.savefig(plots_dir / "error_cdf.png", dpi=160)

fig, ax = plt.subplots(figsize=(7, 4))

epsilon_grid = np.linspace(0.02, 0.4, 15)
for protocol_id, group in rows.groupby("protocol_id"):
    attainment = [np.mean(group["abs_error"] <= eps) for eps in epsilon_grid]
    ax.plot(epsilon_grid, attainment, marker="o", label=protocol_id)

ax.set_xlabel("Error target ε")
ax.set_ylabel("Attainment fraction")
ax.set_title("Attainment curves at fixed budget")
ax.legend()
fig.tight_layout()
fig.savefig(plots_dir / "attainment_curve.png", dpi=160)

# %% [markdown]
# ## 5. Task results + manifest

# %%
task_results = []
for protocol_id, row in percentiles.iterrows():
    task_results.append(
        TaskResult(
            task_id="task_fixed_budget_distribution",
            task_name="Fixed-budget CDF/percentiles",
            run_id=run_id,
            circuit_id="synthetic_circuit",
            protocol_id=protocol_id,
            outputs={
                "p50": float(row["p50"]),
                "p90": float(row["p90"]),
                "p95": float(row["p95"]),
            },
        )
    )

context = NotebookRunContext(
    run_id=run_id,
    output_dir=Path("notebook_data/notebook_f_fixed_budget"),
    methodology_version="3.0.0",
    config={"seeds": {"master": SEED}, "confidence_level": CONFIDENCE_LEVEL},
    circuits=["synthetic_circuit"],
    observable_sets=["random_pauli_fixed"],
    protocols=[p.protocol_id for p in protocols],
    N_grid=[N_SHOTS],
    n_replicates=N_REPLICATES,
    noise_profiles=["ideal"],
)

artifacts = finalize_notebook_run(
    context=context,
    result_set=result_set,
    task_results=task_results,
)

print("Artifacts written:")
for key, path in artifacts.items():
    print(f"  {key}: {path}")
