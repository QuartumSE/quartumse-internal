"""Notebook D: Scaling with number of observables (M sweep)."""
# %% [markdown]
# # Notebook D: Scaling with number of observables (M sweep)
#
# Sweep the observable count and inspect scaling behavior.

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
from quartumse.protocols import DirectGroupedProtocol, DirectOptimizedProtocol
from quartumse.stats.confidence import normal_ci

sys.path.insert(0, str(Path(__file__).resolve().parent))
from notebook_utils import NotebookRunContext, finalize_notebook_run

# %% [markdown]
# ## 1. Configuration

# %%
SEED = 17
rng = np.random.default_rng(SEED)
N_QUBITS = 4
M_GRID = [10, 20, 40, 80]
N_SHOTS = 1500
N_REPLICATES = 4
CONFIDENCE_LEVEL = 0.95

protocols = [DirectGroupedProtocol(), DirectOptimizedProtocol()]

# %% [markdown]
# ## 2. Simulate M sweep

# %%
result_set = LongFormResultSet()
run_id = "notebook_d_m_scaling"

for m_total in M_GRID:
    observable_set = generate_observable_set(
        generator_id="random_pauli",
        n_qubits=N_QUBITS,
        n_observables=m_total,
        seed=SEED + m_total,
        max_weight=3,
    )
    true_expectations = {
        obs.observable_id: rng.uniform(-0.5, 0.5)
        for obs in observable_set.observables
    }

    for replicate in range(N_REPLICATES):
        for protocol in protocols:
            estimates = simulate_protocol_execution(
                protocol=protocol,
                observable_set=observable_set,
                n_shots=N_SHOTS,
                seed=SEED + replicate + m_total,
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
                    .with_circuit("synthetic_circuit", n_qubits=N_QUBITS, depth=3)
                    .with_observable(
                        observable_id=estimate.observable_id,
                        observable_type="pauli_string",
                        locality=estimate.metadata.get("locality", 1),
                        observable_set_id=f"random_pauli_{m_total}",
                        M_total=m_total,
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
# ## 3. Summary tables

# %%
rows = pd.DataFrame(result_set.to_dicts())
summary = (
    rows.groupby(["protocol_id", "M_total"])
    .agg(mean_se=("se", "mean"), rmse=("sq_err", lambda x: float(np.sqrt(np.mean(x)))))
    .reset_index()
)
print(summary)

# %% [markdown]
# ## 4. Plots

# %%
plots_dir = Path("notebook_data/notebook_d_scaling_observables/plots")
plots_dir.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(7, 4))
for protocol_id, group in summary.groupby("protocol_id"):
    ax.plot(group["M_total"], group["mean_se"], marker="o", label=protocol_id)

ax.set_xlabel("Number of observables (M)")
ax.set_ylabel("Mean SE")
ax.set_title("Mean SE vs number of observables")
ax.legend()
fig.tight_layout()
fig.savefig(plots_dir / "mean_se_vs_m.png", dpi=160)

# %% [markdown]
# ## 5. Task results + manifest

# %%
task_results = []
for protocol_id, group in summary.groupby("protocol_id"):
    last = group.sort_values("M_total").iloc[-1]
    task_results.append(
        TaskResult(
            task_id="task_m_scaling",
            task_name="Observable count scaling",
            run_id=run_id,
            circuit_id="synthetic_circuit",
            protocol_id=protocol_id,
            outputs={
                "max_M": int(last["M_total"]),
                "mean_se": float(last["mean_se"]),
                "rmse": float(last["rmse"]),
            },
        )
    )

context = NotebookRunContext(
    run_id=run_id,
    output_dir=Path("notebook_data/notebook_d_scaling_observables"),
    methodology_version="3.0.0",
    config={"seeds": {"master": SEED}, "confidence_level": CONFIDENCE_LEVEL},
    circuits=["synthetic_circuit"],
    observable_sets=[f"random_pauli_{m}" for m in M_GRID],
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
