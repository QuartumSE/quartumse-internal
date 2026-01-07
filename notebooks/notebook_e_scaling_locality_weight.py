"""Notebook E: Scaling with locality/weight (shadows degradation regimes)."""
# %% [markdown]
# # Notebook E: Scaling with locality/weight
#
# Sweep observable locality to show degradation regimes.

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
from quartumse.protocols import DirectOptimizedProtocol
from quartumse.stats.confidence import normal_ci

sys.path.insert(0, str(Path(__file__).resolve().parent))
from notebook_utils import NotebookRunContext, finalize_notebook_run

# %% [markdown]
# ## 1. Configuration

# %%
SEED = 23
rng = np.random.default_rng(SEED)
N_QUBITS = 6
N_SHOTS = 1500
N_REPLICATES = 4
CONFIDENCE_LEVEL = 0.95
WEIGHT_GRID = [1, 2, 3, 4, 5]

protocol = DirectOptimizedProtocol()

# %% [markdown]
# ## 2. Run locality sweep

# %%
result_set = LongFormResultSet()
run_id = "notebook_e_locality_scaling"

for max_weight in WEIGHT_GRID:
    observable_set = generate_observable_set(
        generator_id="random_pauli",
        n_qubits=N_QUBITS,
        n_observables=32,
        seed=SEED + max_weight,
        max_weight=max_weight,
    )
    true_expectations = {
        obs.observable_id: rng.uniform(-0.5, 0.5)
        for obs in observable_set.observables
    }

    for replicate in range(N_REPLICATES):
        estimates = simulate_protocol_execution(
            protocol=protocol,
            observable_set=observable_set,
            n_shots=N_SHOTS,
            seed=SEED + replicate + max_weight,
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
                    observable_set_id=f"random_pauli_w{max_weight}",
                    M_total=len(observable_set.observables),
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
                .with_metadata(max_weight=max_weight)
                .build()
            )
            result_set.add(row)

# %% [markdown]
# ## 3. Summary tables

# %%
rows = pd.DataFrame(result_set.to_dicts())
rows["max_weight"] = rows["metadata"].apply(lambda payload: payload.get("max_weight"))
summary = (
    rows.groupby(["max_weight", "locality"])
    .agg(mean_se=("se", "mean"), rmse=("sq_err", lambda x: float(np.sqrt(np.mean(x)))))
    .reset_index()
)

print(summary.head())

# %% [markdown]
# ## 4. Plots

# %%
plots_dir = Path("notebook_data/notebook_e_scaling_locality/plots")
plots_dir.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(7, 4))
for max_weight, group in summary.groupby("max_weight"):
    ax.plot(group["locality"], group["mean_se"], marker="o", label=f"w<= {max_weight}")

ax.set_xlabel("Observable locality")
ax.set_ylabel("Mean SE")
ax.set_title("Mean SE vs locality (degradation regimes)")
ax.legend(title="Max weight")
fig.tight_layout()
fig.savefig(plots_dir / "mean_se_vs_locality.png", dpi=160)

# %% [markdown]
# ## 5. Task results + manifest

# %%
task_results = []
for max_weight, group in summary.groupby("max_weight"):
    worst = group.sort_values("mean_se", ascending=False).iloc[0]
    task_results.append(
        TaskResult(
            task_id="task_locality_scaling",
            task_name="Locality degradation",
            run_id=run_id,
            circuit_id="synthetic_circuit",
            protocol_id=protocol.protocol_id,
            outputs={
                "max_weight": int(max_weight),
                "worst_locality": int(worst["locality"]),
                "mean_se": float(worst["mean_se"]),
            },
        )
    )

context = NotebookRunContext(
    run_id=run_id,
    output_dir=Path("notebook_data/notebook_e_scaling_locality"),
    methodology_version="3.0.0",
    config={"seeds": {"master": SEED}, "confidence_level": CONFIDENCE_LEVEL},
    circuits=["synthetic_circuit"],
    observable_sets=[f"random_pauli_w{w}" for w in WEIGHT_GRID],
    protocols=[protocol.protocol_id],
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
