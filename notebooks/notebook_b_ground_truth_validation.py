"""Notebook B: Ground Truth Validation + Calibration (Measurements Bible §0.2)."""
# %% [markdown]
# # Notebook B: Ground Truth Validation + Calibration
#
# This notebook evaluates bias/variance/RMSE scaling and coverage calibration
# against ground truth expectations.

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
SEED = 41
rng = np.random.default_rng(SEED)

N_QUBITS = 4
N_OBSERVABLES = 24
N_GRID = [200, 500, 1000, 2000]
N_REPLICATES = 6
CONFIDENCE_LEVEL = 0.95

observable_set = generate_observable_set(
    generator_id="random_pauli",
    n_qubits=N_QUBITS,
    n_observables=N_OBSERVABLES,
    seed=SEED,
    max_weight=3,
)

true_expectations = {
    obs.observable_id: rng.uniform(-0.7, 0.7) for obs in observable_set.observables
}

protocols = [
    DirectNaiveProtocol(),
    DirectGroupedProtocol(),
    DirectOptimizedProtocol(),
]

# %% [markdown]
# ## 2. Simulate protocol runs and build long-form results

# %%
result_set = LongFormResultSet()
run_id = "notebook_b_ground_truth"

for n_shots in N_GRID:
    for replicate in range(N_REPLICATES):
        for protocol in protocols:
            estimates = simulate_protocol_execution(
                protocol=protocol,
                observable_set=observable_set,
                n_shots=n_shots,
                seed=SEED + replicate + n_shots,
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
                        observable_set_id="random_pauli_set",
                        M_total=N_OBSERVABLES,
                    )
                    .with_protocol(protocol.protocol_id, protocol.protocol_version)
                    .with_backend("synthetic", noise_profile_id="ideal")
                    .with_replicate(replicate)
                    .with_seeds(
                        seed_policy="seed+replicate",
                        seed_protocol=SEED + replicate,
                        seed_acquire=SEED + n_shots,
                    )
                    .with_budget(N_total=n_shots, n_settings=estimate.n_settings)
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
# ## 3. Bias/variance/RMSE scaling

# %%
rows = pd.DataFrame(result_set.to_dicts())
rows["error"] = rows["estimate"] - rows["truth_value"]
rows["sq_error"] = rows["error"] ** 2

summary = (
    rows.groupby(["protocol_id", "N_total"])
    .agg(
        bias=("error", "mean"),
        variance=("estimate", "var"),
        rmse=("sq_error", lambda x: float(np.sqrt(np.mean(x)))),
        coverage=(
            "error",
            lambda x: float(
                np.mean(
                    (rows.loc[x.index, "ci_low"] <= rows.loc[x.index, "truth_value"])
                    & (rows.loc[x.index, "ci_high"] >= rows.loc[x.index, "truth_value"])
                )
            ),
        ),
    )
    .reset_index()
)

print(summary)

# %% [markdown]
# ## 4. Calibration plots

# %%
plots_dir = Path("notebook_data/notebook_b_ground_truth_validation/plots")
plots_dir.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(8, 5))
for protocol_id, group in summary.groupby("protocol_id"):
    ax.plot(group["N_total"], group["rmse"], marker="o", label=f"{protocol_id} RMSE")

ax.set_xlabel("Shots (N)")
ax.set_ylabel("RMSE")
ax.set_title("RMSE Scaling vs Shot Budget")
ax.legend()
fig.tight_layout()
fig.savefig(plots_dir / "rmse_scaling.png", dpi=160)

fig, ax = plt.subplots(figsize=(8, 5))
for protocol_id, group in summary.groupby("protocol_id"):
    ax.plot(group["N_total"], group["coverage"], marker="o", label=protocol_id)

ax.axhline(CONFIDENCE_LEVEL, color="black", linestyle="--", label="Target")
ax.set_xlabel("Shots (N)")
ax.set_ylabel("Coverage")
ax.set_title("CI Coverage vs Shot Budget")
ax.legend()
fig.tight_layout()
fig.savefig(plots_dir / "coverage_scaling.png", dpi=160)

# %% [markdown]
# ## 5. Task results + manifest

# %%
results_by_protocol = summary.groupby("protocol_id")

task_results = []
for protocol_id, group in results_by_protocol:
    latest = group.sort_values("N_total").iloc[-1]
    task_results.append(
        TaskResult(
            task_id="task_calibration",
            task_name="Bias/variance/RMSE calibration",
            run_id=run_id,
            circuit_id="synthetic_circuit",
            protocol_id=protocol_id,
            epsilon=None,
            delta=None,
            outputs={
                "rmse": float(latest["rmse"]),
                "bias": float(latest["bias"]),
                "variance": float(latest["variance"]),
                "coverage": float(latest["coverage"]),
            },
        )
    )

context = NotebookRunContext(
    run_id=run_id,
    output_dir=Path("notebook_data/notebook_b_ground_truth_validation"),
    methodology_version="3.0.0",
    config={"seeds": {"master": SEED}, "confidence_level": CONFIDENCE_LEVEL},
    circuits=["synthetic_circuit"],
    observable_sets=["random_pauli_set"],
    protocols=[p.protocol_id for p in protocols],
    N_grid=N_GRID,
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
