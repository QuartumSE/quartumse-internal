"""Notebook I: Noise/hardware readiness (noise profile sweeps)."""
# %% [markdown]
# # Notebook I: Noise/Hardware Readiness
#
# Sweep synthetic noise profiles and report readiness signals.

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
SEED = 61
rng = np.random.default_rng(SEED)
N_QUBITS = 4
N_OBSERVABLES = 24
N_SHOTS = 1200
N_REPLICATES = 5
CONFIDENCE_LEVEL = 0.95

noise_profiles = {
    "ideal": {"bias": 0.0, "variance_scale": 1.0},
    "mild_noise": {"bias": 0.02, "variance_scale": 1.3},
    "moderate_noise": {"bias": 0.05, "variance_scale": 1.8},
    "heavy_noise": {"bias": 0.08, "variance_scale": 2.5},
}

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

protocol = DirectOptimizedProtocol()

# %% [markdown]
# ## 2. Noise profile sweep

# %%
result_set = LongFormResultSet()
run_id = "notebook_i_noise_readiness"

for profile_id, noise in noise_profiles.items():
    for replicate in range(N_REPLICATES):
        estimates = simulate_protocol_execution(
            protocol=protocol,
            observable_set=observable_set,
            n_shots=N_SHOTS,
            seed=SEED + replicate,
            true_expectations=true_expectations,
        )

        for estimate in estimates.estimates:
            truth = true_expectations[estimate.observable_id]
            noisy_estimate = estimate.estimate + noise["bias"]
            noisy_se = estimate.se * np.sqrt(noise["variance_scale"])

            ci = normal_ci(
                estimate=noisy_estimate,
                se=noisy_se,
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
                    observable_set_id="random_pauli_noise",
                    M_total=N_OBSERVABLES,
                )
                .with_protocol(protocol.protocol_id, protocol.protocol_version)
                .with_backend("synthetic", noise_profile_id=profile_id)
                .with_replicate(replicate)
                .with_seeds(
                    seed_policy="seed+replicate",
                    seed_protocol=SEED,
                    seed_acquire=SEED + replicate,
                )
                .with_budget(N_total=N_SHOTS, n_settings=estimate.n_settings)
                .with_estimate(
                    estimate=noisy_estimate,
                    se=noisy_se,
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
# ## 3. Noise profile summary

# %%
rows = pd.DataFrame(result_set.to_dicts())
summary = (
    rows.groupby("noise_profile_id")
    .agg(rmse=("sq_err", lambda x: float(np.sqrt(np.mean(x)))))
    .reset_index()
)
print(summary)

# %% [markdown]
# ## 4. Plot readiness sweep

# %%
plots_dir = Path("notebook_data/notebook_i_noise_readiness/plots")
plots_dir.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(summary["noise_profile_id"], summary["rmse"], marker="o")
ax.set_xlabel("Noise profile")
ax.set_ylabel("RMSE")
ax.set_title("Noise profile sweep (readiness indicator)")
fig.tight_layout()
fig.savefig(plots_dir / "noise_profile_rmse.png", dpi=160)

# %% [markdown]
# ## 5. Task results + manifest

# %%
task_results = []
for _, row in summary.iterrows():
    task_results.append(
        TaskResult(
            task_id="task_noise_sweep",
            task_name="Noise profile sweep",
            run_id=run_id,
            circuit_id="synthetic_circuit",
            protocol_id=protocol.protocol_id,
            noise_profile_id=row["noise_profile_id"],
            outputs={"rmse": float(row["rmse"])},
        )
    )

context = NotebookRunContext(
    run_id=run_id,
    output_dir=Path("notebook_data/notebook_i_noise_readiness"),
    methodology_version="3.0.0",
    config={"seeds": {"master": SEED}, "confidence_level": CONFIDENCE_LEVEL},
    circuits=["synthetic_circuit"],
    observable_sets=["random_pauli_noise"],
    protocols=[protocol.protocol_id],
    N_grid=[N_SHOTS],
    n_replicates=N_REPLICATES,
    noise_profiles=list(noise_profiles.keys()),
)

artifacts = finalize_notebook_run(
    context=context,
    result_set=result_set,
    task_results=task_results,
)

print("Artifacts written:")
for key, path in artifacts.items():
    print(f"  {key}: {path}")
