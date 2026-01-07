"""Notebook H: Pilot-based selection and regret analysis."""
# %% [markdown]
# # Notebook H: Pilot-based selection and regret
#
# Use pilot runs to select protocols and quantify regret vs oracle.

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
SEED = 53
rng = np.random.default_rng(SEED)
N_QUBITS = 4
N_OBSERVABLES = 24
PILOT_SHOTS = 200
FINAL_SHOTS = 1200
N_REPLICATES = 20
CONFIDENCE_LEVEL = 0.95

observable_set = generate_observable_set(
    generator_id="random_pauli",
    n_qubits=N_QUBITS,
    n_observables=N_OBSERVABLES,
    seed=SEED,
    max_weight=3,
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
# ## 2. Pilot-based selection

# %%
result_set = LongFormResultSet()
run_id = "notebook_h_pilot_selection"

selection_records = []

for replicate in range(N_REPLICATES):
    pilot_scores = {}
    full_scores = {}

    for protocol in protocols:
        pilot_estimates = simulate_protocol_execution(
            protocol=protocol,
            observable_set=observable_set,
            n_shots=PILOT_SHOTS,
            seed=SEED + replicate,
            true_expectations=true_expectations,
        )
        pilot_rmse = np.sqrt(
            np.mean(
                [
                    (est.estimate - true_expectations[est.observable_id]) ** 2
                    for est in pilot_estimates.estimates
                ]
            )
        )
        pilot_scores[protocol.protocol_id] = float(pilot_rmse)

        full_estimates = simulate_protocol_execution(
            protocol=protocol,
            observable_set=observable_set,
            n_shots=FINAL_SHOTS,
            seed=SEED + replicate + 100,
            true_expectations=true_expectations,
        )
        full_rmse = np.sqrt(
            np.mean(
                [
                    (est.estimate - true_expectations[est.observable_id]) ** 2
                    for est in full_estimates.estimates
                ]
            )
        )
        full_scores[protocol.protocol_id] = float(full_rmse)

        for estimate in full_estimates.estimates:
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
                    observable_set_id="random_pauli_pilot",
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
                .with_budget(N_total=FINAL_SHOTS, n_settings=estimate.n_settings)
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

    chosen = min(pilot_scores, key=pilot_scores.get)
    oracle = min(full_scores, key=full_scores.get)
    regret = full_scores[chosen] - full_scores[oracle]
    selection_records.append(
        {
            "replicate": replicate,
            "chosen": chosen,
            "oracle": oracle,
            "regret": regret,
            "pilot_rmse": pilot_scores[chosen],
            "oracle_rmse": full_scores[oracle],
        }
    )

# %% [markdown]
# ## 3. Regret analysis

# %%
selection_df = pd.DataFrame(selection_records)
selection_accuracy = float(np.mean(selection_df["chosen"] == selection_df["oracle"]))
mean_regret = float(np.mean(selection_df["regret"]))

print(selection_df.head())
print("Selection accuracy:", selection_accuracy)
print("Mean regret:", mean_regret)

# %% [markdown]
# ## 4. Plot regret distribution

# %%
plots_dir = Path("notebook_data/notebook_h_pilot_selection/plots")
plots_dir.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(7, 4))
ax.hist(selection_df["regret"], bins=10, color="#c44e52")
ax.set_xlabel("Regret (RMSE gap)")
ax.set_ylabel("Count")
ax.set_title("Pilot selection regret distribution")
fig.tight_layout()
fig.savefig(plots_dir / "regret_distribution.png", dpi=160)

# %% [markdown]
# ## 5. Task results + manifest

# %%
task_results = [
    TaskResult(
        task_id="task_pilot_selection",
        task_name="Pilot-based protocol selection",
        run_id=run_id,
        circuit_id="synthetic_circuit",
        protocol_id="pilot_selector",
        selection_accuracy=selection_accuracy,
        regret=mean_regret,
        outputs={
            "pilot_shots": PILOT_SHOTS,
            "final_shots": FINAL_SHOTS,
        },
    )
]

context = NotebookRunContext(
    run_id=run_id,
    output_dir=Path("notebook_data/notebook_h_pilot_selection"),
    methodology_version="3.0.0",
    config={"seeds": {"master": SEED}, "confidence_level": CONFIDENCE_LEVEL},
    circuits=["synthetic_circuit"],
    observable_sets=["random_pauli_pilot"],
    protocols=[p.protocol_id for p in protocols],
    N_grid=[PILOT_SHOTS, FINAL_SHOTS],
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
