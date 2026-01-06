"""Data I/O and schemas for benchmark outputs (Measurements Bible §10).

This package provides:
- Pydantic schemas for long-form results and summary tables (§10.1, §10.3)
- LongFormResultBuilder for constructing result rows
- Partitioned Parquet I/O for efficient storage (§10.2)
- Summary aggregation utilities (§10.3)

Usage:
    from quartumse.io import (
        LongFormRow,
        SummaryRow,
        TaskResult,
        RunManifest,
        LongFormResultBuilder,
        LongFormResultSet,
        ParquetWriter,
        ParquetReader,
        SummaryAggregator,
    )

    # Build result rows
    builder = LongFormResultBuilder()
    row = (
        builder
        .with_run_id("run_001")
        .with_circuit("circuit_001", n_qubits=4, depth=10)
        .with_observable("obs_001", "pauli_string", locality=2)
        .with_protocol("direct_naive", "1.0.0")
        .with_backend("aer_simulator")
        .with_seeds(seed_protocol=42, seed_acquire=43)
        .with_budget(N_total=1000, n_settings=1)
        .with_estimate(0.75, se=0.02)
        .build()
    )

    # Write to Parquet
    result_set = LongFormResultSet([row])
    writer = ParquetWriter("results/run_001")
    writer.write_long_form(result_set)

    # Compute summaries
    aggregator = SummaryAggregator(result_set, epsilon=0.01)
    summaries = aggregator.compute_summaries()
    writer.write_summary(summaries)

    # Read results
    reader = ParquetReader("results/run_001")
    loaded_results = reader.read_long_form()
"""

from .long_form import (
    LongFormResultBuilder,
    LongFormResultSet,
)
from .parquet_io import (
    ParquetReader,
    ParquetWriter,
    merge_results,
)
from .schemas import (
    JobStatus,
    LongFormRow,
    RunManifest,
    SummaryRow,
    TaskResult,
)
from .summary import (
    SummaryAggregator,
    compute_crossover_point,
    compute_shot_savings_factor,
)

__all__ = [
    # Schemas
    "JobStatus",
    "LongFormRow",
    "SummaryRow",
    "TaskResult",
    "RunManifest",
    # Long-form builder
    "LongFormResultBuilder",
    "LongFormResultSet",
    # Parquet I/O
    "ParquetWriter",
    "ParquetReader",
    "merge_results",
    # Summary
    "SummaryAggregator",
    "compute_shot_savings_factor",
    "compute_crossover_point",
]
