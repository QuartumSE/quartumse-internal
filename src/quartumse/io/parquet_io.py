"""Partitioned Parquet I/O for benchmark results (Measurements Bible §10).

This module provides utilities for reading and writing benchmark results
in partitioned Parquet format for efficient storage and querying.

Partitioning scheme (§10.2):
    results/
    └── protocol_id=<protocol>/
        └── circuit_id=<circuit>/
            └── N_total=<shots>/
                └── data.parquet
"""

from __future__ import annotations

import json
import platform
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from .long_form import LongFormResultSet
from .schemas import LongFormRow, RunManifest, SummaryRow, TaskResult

# Windows has path length issues with Hive-style partitioning
IS_WINDOWS = platform.system() == "Windows"

# Try to import pyarrow/pandas, but provide fallback
try:
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq

    HAS_PARQUET = True
except ImportError:
    HAS_PARQUET = False


def _check_parquet_available() -> None:
    """Check if parquet dependencies are available."""
    if not HAS_PARQUET:
        raise ImportError(
            "Parquet I/O requires pyarrow and pandas. "
            "Install with: pip install pyarrow pandas"
        )


class ParquetWriter:
    """Writer for partitioned Parquet output.

    Example:
        writer = ParquetWriter("results/run_001")
        writer.write_long_form(result_set)
        writer.write_summary(summary_rows)
        writer.write_manifest(manifest)
    """

    def __init__(self, output_dir: str | Path) -> None:
        """Initialize writer.

        Args:
            output_dir: Root output directory for this run.
        """
        _check_parquet_available()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_long_form(
        self,
        result_set: LongFormResultSet,
        partitioned: bool | None = None,
    ) -> Path:
        """Write long-form results to Parquet.

        Args:
            result_set: Collection of LongFormRow objects.
            partitioned: If True, partition by protocol/circuit/N_total.
                        If None, auto-detect (disabled on Windows due to path length limits).

        Returns:
            Path to the written file or directory.
        """
        if len(result_set) == 0:
            raise ValueError("Cannot write empty result set")

        # Auto-detect: disable partitioning on Windows to avoid path length issues
        if partitioned is None:
            partitioned = not IS_WINDOWS

        # Convert to DataFrame
        df = pd.DataFrame(result_set.to_dicts())

        # Convert datetime columns
        datetime_cols = [
            "job_submitted_at",
            "job_started_at",
            "job_completed_at",
        ]
        for col in datetime_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])

        # Serialize dict columns to JSON strings (Arrow can't handle empty structs)
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, dict)).any():
                df[col] = df[col].apply(
                    lambda x: json.dumps(x) if isinstance(x, dict) else x
                )

        long_form_dir = self.output_dir / "long_form"

        if partitioned:
            # Write partitioned dataset
            partition_cols = ["protocol_id", "circuit_id", "N_total"]
            pq.write_to_dataset(
                pa.Table.from_pandas(df),
                root_path=str(long_form_dir),
                partition_cols=partition_cols,
            )
            return long_form_dir
        else:
            # Write single file
            output_path = long_form_dir / "data.parquet"
            long_form_dir.mkdir(parents=True, exist_ok=True)
            pq.write_table(pa.Table.from_pandas(df), str(output_path))
            return output_path

    def write_summary(self, summary_rows: list[SummaryRow]) -> Path:
        """Write summary table to Parquet.

        Args:
            summary_rows: List of SummaryRow objects.

        Returns:
            Path to the written file.
        """
        if not summary_rows:
            raise ValueError("Cannot write empty summary")

        df = pd.DataFrame([row.model_dump() for row in summary_rows])

        # Serialize dict columns to JSON strings (Arrow can't handle empty structs)
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, dict)).any():
                df[col] = df[col].apply(
                    lambda x: json.dumps(x) if isinstance(x, dict) else x
                )

        output_path = self.output_dir / "summary.parquet"
        pq.write_table(pa.Table.from_pandas(df), str(output_path))
        return output_path

    def write_task_results(self, task_results: list[TaskResult]) -> Path:
        """Write task results to Parquet.

        Args:
            task_results: List of TaskResult objects.

        Returns:
            Path to the written file.
        """
        if not task_results:
            raise ValueError("Cannot write empty task results")

        # Flatten the outputs dict into the main record
        records = []
        for result in task_results:
            record = result.model_dump()
            # Keep outputs as JSON string for flexibility
            record["outputs"] = json.dumps(record["outputs"])
            records.append(record)

        df = pd.DataFrame(records)
        output_path = self.output_dir / "task_results.parquet"
        pq.write_table(pa.Table.from_pandas(df), str(output_path))
        return output_path

    def write_manifest(self, manifest: RunManifest) -> Path:
        """Write run manifest to JSON.

        Args:
            manifest: RunManifest object.

        Returns:
            Path to the written file.
        """
        output_path = self.output_dir / "manifest.json"

        self._populate_manifest_paths(manifest)
        manifest.validate_required_fields()

        # Convert to dict and handle datetime
        data = manifest.model_dump()
        for key in ["created_at", "completed_at"]:
            if data[key] is not None:
                data[key] = data[key].isoformat()

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        return output_path

    def _populate_manifest_paths(self, manifest: RunManifest) -> None:
        long_form_dir = self.output_dir / "long_form"
        summary_path = self.output_dir / "summary.parquet"
        task_results_path = self.output_dir / "task_results.parquet"
        plots_dir = self.output_dir / "plots"

        if manifest.long_form_path is None and long_form_dir.exists():
            manifest.long_form_path = str(long_form_dir)
        if manifest.summary_path is None and summary_path.exists():
            manifest.summary_path = str(summary_path)
        if manifest.task_results_path is None and task_results_path.exists():
            manifest.task_results_path = str(task_results_path)
        if manifest.plots_dir is None and plots_dir.exists():
            manifest.plots_dir = str(plots_dir)


class ParquetReader:
    """Reader for partitioned Parquet results.

    Example:
        reader = ParquetReader("results/run_001")
        result_set = reader.read_long_form()
        summary = reader.read_summary()
        manifest = reader.read_manifest()
    """

    def __init__(self, input_dir: str | Path) -> None:
        """Initialize reader.

        Args:
            input_dir: Root directory for this run's results.
        """
        _check_parquet_available()
        self.input_dir = Path(input_dir)

    def read_long_form(
        self,
        filters: list[tuple[str, str, Any]] | None = None,
    ) -> LongFormResultSet:
        """Read long-form results from Parquet.

        Args:
            filters: Optional pyarrow filters, e.g.,
                [("protocol_id", "=", "direct_naive")]

        Returns:
            LongFormResultSet containing the results.
        """
        long_form_dir = self.input_dir / "long_form"

        if not long_form_dir.exists():
            raise FileNotFoundError(f"Long-form results not found: {long_form_dir}")

        # Read dataset with optional filters
        dataset = pq.ParquetDataset(str(long_form_dir), filters=filters)
        df = dataset.read().to_pandas()

        # Convert to LongFormRow objects
        rows = []
        for _, record in df.iterrows():
            # Convert NaN to None
            record_dict = {
                k: (None if pd.isna(v) else v) for k, v in record.to_dict().items()
            }
            rows.append(LongFormRow(**record_dict))

        return LongFormResultSet(rows)

    def read_long_form_df(
        self,
        filters: list[tuple[str, str, Any]] | None = None,
    ) -> pd.DataFrame:
        """Read long-form results as DataFrame.

        Args:
            filters: Optional pyarrow filters.

        Returns:
            pandas DataFrame with results.
        """
        long_form_dir = self.input_dir / "long_form"

        if not long_form_dir.exists():
            raise FileNotFoundError(f"Long-form results not found: {long_form_dir}")

        dataset = pq.ParquetDataset(str(long_form_dir), filters=filters)
        return dataset.read().to_pandas()

    def read_summary(self) -> list[SummaryRow]:
        """Read summary table from Parquet.

        Returns:
            List of SummaryRow objects.
        """
        summary_path = self.input_dir / "summary.parquet"

        if not summary_path.exists():
            raise FileNotFoundError(f"Summary not found: {summary_path}")

        df = pq.read_table(str(summary_path)).to_pandas()

        rows = []
        for _, record in df.iterrows():
            record_dict = {
                k: (None if pd.isna(v) else v) for k, v in record.to_dict().items()
            }
            rows.append(SummaryRow(**record_dict))

        return rows

    def read_summary_df(self) -> pd.DataFrame:
        """Read summary table as DataFrame.

        Returns:
            pandas DataFrame with summary.
        """
        summary_path = self.input_dir / "summary.parquet"

        if not summary_path.exists():
            raise FileNotFoundError(f"Summary not found: {summary_path}")

        return pq.read_table(str(summary_path)).to_pandas()

    def read_task_results(self) -> list[TaskResult]:
        """Read task results from Parquet.

        Returns:
            List of TaskResult objects.
        """
        task_path = self.input_dir / "task_results.parquet"

        if not task_path.exists():
            raise FileNotFoundError(f"Task results not found: {task_path}")

        df = pq.read_table(str(task_path)).to_pandas()

        rows = []
        for _, record in df.iterrows():
            record_dict = {
                k: (None if pd.isna(v) else v) for k, v in record.to_dict().items()
            }
            # Parse outputs JSON
            if "outputs" in record_dict and record_dict["outputs"]:
                record_dict["outputs"] = json.loads(record_dict["outputs"])
            rows.append(TaskResult(**record_dict))

        return rows

    def read_manifest(self) -> RunManifest:
        """Read run manifest from JSON.

        Returns:
            RunManifest object.
        """
        manifest_path = self.input_dir / "manifest.json"

        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        with open(manifest_path) as f:
            data = json.load(f)

        # Parse datetime fields
        for key in ["created_at", "completed_at"]:
            if data[key] is not None:
                data[key] = datetime.fromisoformat(data[key])

        return RunManifest(**data)

    def list_protocols(self) -> list[str]:
        """List available protocols in the dataset.

        Returns:
            List of protocol IDs.
        """
        long_form_dir = self.input_dir / "long_form"

        if not long_form_dir.exists():
            return []

        # List protocol_id=* directories
        protocols = []
        for path in long_form_dir.iterdir():
            if path.is_dir() and path.name.startswith("protocol_id="):
                protocols.append(path.name.split("=", 1)[1])

        return sorted(protocols)

    def list_circuits(self, protocol_id: str | None = None) -> list[str]:
        """List available circuits in the dataset.

        Args:
            protocol_id: Optional filter by protocol.

        Returns:
            List of circuit IDs.
        """
        long_form_dir = self.input_dir / "long_form"

        if not long_form_dir.exists():
            return []

        circuits = set()

        if protocol_id:
            protocol_dir = long_form_dir / f"protocol_id={protocol_id}"
            if protocol_dir.exists():
                for path in protocol_dir.iterdir():
                    if path.is_dir() and path.name.startswith("circuit_id="):
                        circuits.add(path.name.split("=", 1)[1])
        else:
            for protocol_path in long_form_dir.iterdir():
                if protocol_path.is_dir():
                    for path in protocol_path.iterdir():
                        if path.is_dir() and path.name.startswith("circuit_id="):
                            circuits.add(path.name.split("=", 1)[1])

        return sorted(circuits)


def merge_results(
    output_dir: str | Path,
    input_dirs: list[str | Path],
) -> Path:
    """Merge multiple result directories into one.

    Useful for combining results from distributed runs.

    Args:
        output_dir: Output directory for merged results.
        input_dirs: List of input directories to merge.

    Returns:
        Path to merged output directory.
    """
    _check_parquet_available()

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    all_rows: list[LongFormRow] = []
    all_summaries: list[SummaryRow] = []
    all_tasks: list[TaskResult] = []

    for input_dir in input_dirs:
        reader = ParquetReader(input_dir)

        try:
            result_set = reader.read_long_form()
            all_rows.extend(result_set.rows)
        except FileNotFoundError:
            pass

        try:
            summaries = reader.read_summary()
            all_summaries.extend(summaries)
        except FileNotFoundError:
            pass

        try:
            tasks = reader.read_task_results()
            all_tasks.extend(tasks)
        except FileNotFoundError:
            pass

    writer = ParquetWriter(output_path)

    if all_rows:
        writer.write_long_form(LongFormResultSet(all_rows))

    if all_summaries:
        writer.write_summary(all_summaries)

    if all_tasks:
        writer.write_task_results(all_tasks)

    return output_path
