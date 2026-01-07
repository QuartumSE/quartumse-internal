"""Data schemas for benchmark outputs (Measurements Bible §10).

This module defines Pydantic models for the long-form results table (§10.1)
and summary tables (§10.3). These schemas ensure consistent, validated
data across all benchmark runs.

The long-form table has one row per:
- repetition
- protocol
- circuit instance
- shot budget
- observable
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job execution status for hardware runs."""

    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"


class LongFormRow(BaseModel):
    """A single row in the long-form results table (§10.1).

    This schema defines all required columns for the tidy long-form output.
    Each row corresponds to one observable estimate from one protocol run.
    """

    # === Identifiers ===
    run_id: str = Field(description="Unique identifier for this benchmark run")
    methodology_version: str = Field(
        description="Version of the Measurements Bible methodology"
    )
    circuit_id: str = Field(description="Identifier for the circuit instance")
    observable_set_id: str = Field(description="Identifier for the observable set")
    observable_id: str = Field(description="Identifier for this specific observable")
    protocol_id: str = Field(description="Protocol identifier")
    protocol_version: str = Field(description="Protocol version")
    backend_id: str = Field(description="Backend identifier")
    noise_profile_id: str = Field(
        default="ideal", description="Noise profile identifier"
    )
    replicate_id: int = Field(description="Replicate number (0-indexed)")

    # === Seeds ===
    seed_policy: str = Field(description="Policy used to derive run seeds")
    seed_protocol: int = Field(description="Seed for protocol planning randomness")
    seed_acquire: int = Field(description="Seed for measurement sampling")
    seed_bootstrap: int | None = Field(
        default=None, description="Seed for bootstrap CI (if used)"
    )

    # === Problem descriptors ===
    n_qubits: int = Field(description="Number of qubits in the circuit")
    circuit_depth: int | None = Field(
        default=None, description="Circuit depth (if meaningful)"
    )
    twoq_gate_count: int | None = Field(
        default=None, description="Number of 2-qubit gates"
    )
    observable_type: str = Field(
        description="Observable type: pauli_string, pauli_sum, matrix"
    )
    locality: int = Field(description="Pauli weight / locality")
    coefficient: float = Field(default=1.0, description="Observable coefficient")
    group_id: str | None = Field(
        default=None, description="Commuting group ID (if grouped)"
    )
    M_total: int = Field(description="Total number of observables in the set")

    # === Budget and resources ===
    N_total: int = Field(description="Total shots used")
    n_settings: int = Field(description="Number of distinct measurement settings")
    time_quantum_s: float | None = Field(
        default=None, description="Quantum execution time in seconds"
    )
    time_classical_s: float | None = Field(
        default=None, description="Classical processing time in seconds"
    )
    memory_bytes: int | None = Field(default=None, description="Peak memory usage")

    # === Cost (optional) ===
    cost_model_id: str | None = Field(default=None, description="Cost model identifier")
    cost_usd_estimate: float | None = Field(
        default=None, description="Estimated cost in USD"
    )

    # === Hardware-specific (optional) ===
    job_status: JobStatus | None = Field(default=None, description="Job execution status")
    queue_time_s: float | None = Field(default=None, description="Queue time in seconds")
    job_submitted_at: datetime | None = Field(
        default=None, description="Job submission timestamp"
    )
    job_started_at: datetime | None = Field(
        default=None, description="Job start timestamp"
    )
    job_completed_at: datetime | None = Field(
        default=None, description="Job completion timestamp"
    )

    # === Estimation results ===
    estimate: float = Field(description="Point estimate of expectation value")
    se: float = Field(description="Standard error of the estimate")
    ci_low_raw: float | None = Field(
        default=None, description="CI lower bound (before clamping)"
    )
    ci_high_raw: float | None = Field(
        default=None, description="CI upper bound (before clamping)"
    )
    ci_low: float | None = Field(
        default=None, description="CI lower bound (after clamping)"
    )
    ci_high: float | None = Field(
        default=None, description="CI upper bound (after clamping)"
    )
    ci_method_id: str | None = Field(default=None, description="CI construction method")
    confidence_level: float = Field(
        default=0.95, description="Confidence level for CI"
    )

    # === Truth (if available) ===
    truth_value: float | None = Field(
        default=None, description="Ground truth expectation value"
    )
    truth_se: float | None = Field(
        default=None, description="SE of truth (if reference truth)"
    )
    truth_mode: str | None = Field(
        default=None,
        description="Truth mode: exact_statevector, exact_density_matrix, reference",
    )

    # === Derived metrics ===
    abs_err: float | None = Field(
        default=None, description="Absolute error |estimate - truth|"
    )
    sq_err: float | None = Field(
        default=None, description="Squared error (estimate - truth)^2"
    )

    # === Additional metadata ===
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    def compute_derived_metrics(self) -> None:
        """Compute derived metrics from truth if available."""
        if self.truth_value is not None:
            self.abs_err = abs(self.estimate - self.truth_value)
            self.sq_err = (self.estimate - self.truth_value) ** 2

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class SummaryRow(BaseModel):
    """Summary statistics for (protocol, circuit, N) combination (§10.3).

    This schema defines aggregated metrics across observables and replicates.
    """

    # === Identifiers ===
    run_id: str
    circuit_id: str
    protocol_id: str
    N_total: int
    noise_profile_id: str = "ideal"

    # === Counts ===
    n_observables: int
    n_replicates: int

    # === SE statistics ===
    se_mean: float
    se_median: float
    se_p90: float
    se_p95: float
    se_max: float

    # === Error statistics (if truth available) ===
    abs_err_mean: float | None = None
    abs_err_median: float | None = None
    abs_err_p90: float | None = None
    abs_err_p95: float | None = None
    abs_err_max: float | None = None
    rmse: float | None = None

    # === Attainment ===
    attainment_epsilon: float | None = None  # The epsilon used
    attainment_fraction: float | None = None  # Fraction with SE <= epsilon

    # === Coverage (if CIs computed) ===
    coverage_per_observable: float | None = None  # Mean per-obs coverage
    coverage_family_wise: float | None = None  # Family-wise coverage

    # === Resource totals ===
    total_quantum_time_s: float | None = None
    total_classical_time_s: float | None = None


class TaskResult(BaseModel):
    """Result for a benchmark task (§8).

    This schema captures the output of running a specific benchmark task.
    """

    # === Task identification ===
    task_id: str = Field(description="Task identifier (e.g., 'task1_worstcase')")
    task_name: str = Field(description="Human-readable task name")

    # === Run identification ===
    run_id: str
    circuit_id: str
    protocol_id: str
    noise_profile_id: str = "ideal"

    # === Task parameters ===
    epsilon: float | None = Field(default=None, description="Target precision")
    delta: float | None = Field(
        default=None, description="Global failure probability"
    )
    fwer_method: str | None = Field(
        default=None, description="FWER control method (e.g., 'bonferroni')"
    )

    # === Primary outputs ===
    N_star: int | None = Field(
        default=None, description="Shots-to-target (minimal N)"
    )
    ssf: float | None = Field(
        default=None, description="Shot-savings factor vs baseline"
    )
    baseline_protocol_id: str | None = Field(
        default=None, description="Baseline protocol for SSF"
    )

    # === Task-specific outputs ===
    worst_observable_id: str | None = Field(
        default=None, description="Observable with worst metric"
    )
    crossover_N: int | None = Field(
        default=None, description="Crossover shot count (Task 4)"
    )
    selection_accuracy: float | None = Field(
        default=None, description="Pilot selection accuracy (Task 5)"
    )
    regret: float | None = Field(
        default=None, description="Regret vs oracle (Task 5)"
    )

    # === Additional outputs ===
    outputs: dict[str, Any] = Field(
        default_factory=dict, description="Task-specific outputs"
    )


class RunManifest(BaseModel):
    """Manifest for a complete benchmark run (§13).

    This captures all metadata needed for reproducibility.
    """

    # === Run identification ===
    run_id: str
    methodology_version: str
    created_at: datetime

    # === Code provenance ===
    git_commit_hash: str | None = None
    quartumse_version: str | None = None
    python_version: str | None = None
    environment_lock: str | None = None  # pip freeze / uv lock output

    # === Configuration ===
    config_file: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)

    # === Sweep parameters ===
    circuits: list[str] = Field(default_factory=list)  # Circuit IDs
    observable_sets: list[str] = Field(default_factory=list)  # ObservableSet IDs
    protocols: list[str] = Field(default_factory=list)  # Protocol IDs
    N_grid: list[int] = Field(default_factory=list)
    n_replicates: int = 1
    noise_profiles: list[str] = Field(default_factory=list)

    # === Output locations ===
    long_form_path: str | None = None
    summary_path: str | None = None
    task_results_path: str | None = None
    plots_dir: str | None = None

    # === Completion status ===
    status: str = "running"  # running, completed, failed
    completed_at: datetime | None = None
    error_message: str | None = None

    def validate_required_fields(self) -> None:
        """Validate required manifest fields from §0.1 and §0.2."""
        missing: list[str] = []

        if not self.methodology_version:
            missing.append("methodology_version")
        if not self.git_commit_hash:
            missing.append("git_commit_hash")
        if not self.quartumse_version:
            missing.append("quartumse_version")
        if not self.python_version:
            missing.append("python_version")
        if not self.environment_lock:
            missing.append("environment_lock")
        if not self.config.get("seeds"):
            missing.append("config.seeds")
        if not self.long_form_path:
            missing.append("long_form_path")
        if not self.summary_path:
            missing.append("summary_path")
        if not self.plots_dir:
            missing.append("plots_dir")

        if missing:
            missing_fields = ", ".join(missing)
            raise ValueError(f"RunManifest missing required fields: {missing_fields}")
