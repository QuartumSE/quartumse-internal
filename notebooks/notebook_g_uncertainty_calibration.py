"""Notebook G: Uncertainty calibration + diagnostics (CI comparison)."""
# %% [markdown]
# # Notebook G: Uncertainty Calibration + Diagnostics
#
# Compare CI methods under heavy-tail noise.

# %%
from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from quartumse.io import LongFormResultBuilder, LongFormResultSet
from quartumse.io.schemas import TaskResult
from quartumse.stats.confidence import bootstrap_percentile_ci, normal_ci

sys.path.insert(0, str(Path(__file__).resolve().parent))
from notebook_utils import NotebookRunContext, finalize_notebook_run

# %% [markdown]
# ## 1. Configuration

# %%
SEED = 37
rng = np.random.default_rng(SEED)
N_SAMPLES = 400
N_REPLICATES = 200
CONFIDENCE_LEVEL = 0.95
TRUE_MEAN = 0.0

# %% [markdown]
# ## 2. Generate heavy-tail samples and CI comparisons

# %%
result_set = LongFormResultSet()
run_id = "notebook_g_uncertainty_calibration"

for replicate in range(N_REPLICATES):
    data = rng.standard_t(df=3, size=N_SAMPLES)
    estimate = float(np.mean(data))
    se = float(np.std(data, ddof=1) / np.sqrt(N_SAMPLES))

    normal = normal_ci(estimate, se, confidence_level=CONFIDENCE_LEVEL)
    bootstrap = bootstrap_percentile_ci(
        data,
        confidence_level=CONFIDENCE_LEVEL,
        n_bootstrap=800,
        seed=SEED + replicate,
    )

    for method_label, ci in [
        ("ci_normal", normal),
        ("ci_bootstrap_percentile", bootstrap),
    ]:
        row = (
            LongFormResultBuilder()
            .with_run_id(run_id)
            .with_methodology_version("3.0.0")
            .with_circuit("synthetic_heavy_tail", n_qubits=1, depth=1)
            .with_observable(
                observable_id="heavy_tail_mean",
                observable_type="scalar",
                locality=1,
                observable_set_id="heavy_tail",
                M_total=1,
            )
            .with_protocol(method_label, "1.0")
            .with_backend("synthetic", noise_profile_id="heavy_tail")
            .with_replicate(replicate)
            .with_seeds(
                seed_policy="seed+replicate",
                seed_protocol=SEED,
                seed_acquire=SEED + replicate,
                seed_bootstrap=SEED + replicate + 1000,
            )
            .with_budget(N_total=N_SAMPLES, n_settings=1)
            .with_estimate(
                estimate=estimate,
                se=ci.se,
                ci_low=ci.ci_low,
                ci_high=ci.ci_high,
                ci_low_raw=ci.ci_low_raw,
                ci_high_raw=ci.ci_high_raw,
                ci_method_id=ci.method.value,
                confidence_level=CONFIDENCE_LEVEL,
            )
            .with_truth(truth_value=TRUE_MEAN, mode="synthetic")
            .build()
        )
        result_set.add(row)

# %% [markdown]
# ## 3. Coverage diagnostics

# %%
rows = pd.DataFrame(result_set.to_dicts())
rows["covered"] = (rows["ci_low"] <= TRUE_MEAN) & (rows["ci_high"] >= TRUE_MEAN)

coverage_summary = rows.groupby("protocol_id").agg(
    coverage=("covered", "mean"),
    mean_width=("ci_high", lambda x: float(np.mean(x - rows.loc[x.index, "ci_low"]))),
)
print(coverage_summary)

# %% [markdown]
# ## 4. Plots

# %%
plots_dir = Path("notebook_data/notebook_g_uncertainty_calibration/plots")
plots_dir.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(coverage_summary.index, coverage_summary["coverage"], color="#4c72b0")
ax.axhline(CONFIDENCE_LEVEL, color="black", linestyle="--", label="Target")
ax.set_ylabel("Coverage")
ax.set_title("CI Coverage under heavy-tail noise")
ax.legend()
fig.tight_layout()
fig.savefig(plots_dir / "ci_coverage.png", dpi=160)

fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(coverage_summary.index, coverage_summary["mean_width"], color="#dd8452")
ax.set_ylabel("Mean CI width")
ax.set_title("CI width comparison")
fig.tight_layout()
fig.savefig(plots_dir / "ci_width.png", dpi=160)

# %% [markdown]
# ## 5. Task results + manifest

# %%
task_results = []
for protocol_id, row in coverage_summary.iterrows():
    task_results.append(
        TaskResult(
            task_id="task_ci_calibration",
            task_name="CI calibration heavy-tail",
            run_id=run_id,
            circuit_id="synthetic_heavy_tail",
            protocol_id=protocol_id,
            outputs={
                "coverage": float(row["coverage"]),
                "mean_width": float(row["mean_width"]),
            },
        )
    )

context = NotebookRunContext(
    run_id=run_id,
    output_dir=Path("notebook_data/notebook_g_uncertainty_calibration"),
    methodology_version="3.0.0",
    config={"seeds": {"master": SEED}, "confidence_level": CONFIDENCE_LEVEL},
    circuits=["synthetic_heavy_tail"],
    observable_sets=["heavy_tail"],
    protocols=["ci_normal", "ci_bootstrap_percentile"],
    N_grid=[N_SAMPLES],
    n_replicates=N_REPLICATES,
    noise_profiles=["heavy_tail"],
)

artifacts = finalize_notebook_run(
    context=context,
    result_set=result_set,
    task_results=task_results,
)

print("Artifacts written:")
for key, path in artifacts.items():
    print(f"  {key}: {path}")
