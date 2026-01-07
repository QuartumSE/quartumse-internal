"""Notebook C: Commuting Grouping Baseline Study (Measurements Bible §0.2)."""
# %% [markdown]
# # Notebook C: Commuting Grouping Baseline Study
#
# Compare naive vs grouped vs optimized protocols and inspect grouping statistics.

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
from quartumse.observables import generate_observable_set, partition_observable_set
from quartumse.protocols import DirectGroupedProtocol, DirectNaiveProtocol, DirectOptimizedProtocol
from quartumse.stats.confidence import normal_ci

sys.path.insert(0, str(Path(__file__).resolve().parent))
from notebook_utils import NotebookRunContext, finalize_notebook_run

# %% [markdown]
# ## 1. Configuration

# %%
SEED = 11
rng = np.random.default_rng(SEED)
N_QUBITS = 5
N_OBSERVABLES = 30
N_SHOTS = 1200
N_REPLICATES = 4
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
# ## 2. Commuting group stats

# %%
commuting_groups, grouping_stats = partition_observable_set(
    observable_set,
    method="greedy",
)

print("Grouping stats:")
for key, value in grouping_stats.items():
    print(f"  {key}: {value}")

# %% [markdown]
# ## 3. Simulated protocol comparison

# %%
result_set = LongFormResultSet()
run_id = "notebook_c_grouping_baseline"

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
                    observable_set_id="random_pauli_grouped",
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
# ## 4. Summary tables

# %%
rows = pd.DataFrame(result_set.to_dicts())
summary = rows.groupby("protocol_id").agg(
    mean_se=("se", "mean"),
    max_se=("se", "max"),
    rmse=("sq_err", lambda x: float(np.sqrt(np.mean(x)))),
)
print(summary)

# %% [markdown]
# ## 5. Plots

# %%
plots_dir = Path("notebook_data/notebook_c_commuting_grouping/plots")
plots_dir.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(7, 4))
ax.hist([g.size for g in commuting_groups], bins=10, color="#4c72b0")
ax.set_xlabel("Group size")
ax.set_ylabel("Count")
ax.set_title("Commuting group size distribution")
fig.tight_layout()
fig.savefig(plots_dir / "group_size_distribution.png", dpi=160)

fig, ax = plt.subplots(figsize=(7, 4))
ax.bar(summary.index, summary["mean_se"], color="#55a868")
ax.set_ylabel("Mean SE")
ax.set_title("Mean SE by protocol")
fig.tight_layout()
fig.savefig(plots_dir / "mean_se_by_protocol.png", dpi=160)

# %% [markdown]
# ## 6. Task results + manifest

# %%
task_results = []
for protocol_id, row in summary.iterrows():
    task_results.append(
        TaskResult(
            task_id="task_grouping_baseline",
            task_name="Grouped baseline comparison",
            run_id=run_id,
            circuit_id="synthetic_circuit",
            protocol_id=protocol_id,
            outputs={
                "mean_se": float(row["mean_se"]),
                "max_se": float(row["max_se"]),
                "rmse": float(row["rmse"]),
                "group_count": int(grouping_stats["n_groups"]),
            },
        )
    )

context = NotebookRunContext(
    run_id=run_id,
    output_dir=Path("notebook_data/notebook_c_commuting_grouping"),
    methodology_version="3.0.0",
    config={"seeds": {"master": SEED}, "confidence_level": CONFIDENCE_LEVEL},
    circuits=["synthetic_circuit"],
    observable_sets=["random_pauli_grouped"],
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
