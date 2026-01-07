"""Shared helpers for Measurements Bible notebooks."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import subprocess
import sys
from typing import Any

from quartumse import __version__
from quartumse.io import LongFormResultSet, ParquetWriter, SummaryAggregator
from quartumse.io.schemas import RunManifest, TaskResult


@dataclass
class NotebookRunContext:
    """Bundle run metadata for notebook outputs."""

    run_id: str
    output_dir: Path
    methodology_version: str
    config: dict[str, Any]
    circuits: list[str]
    observable_sets: list[str]
    protocols: list[str]
    N_grid: list[int]
    n_replicates: int
    noise_profiles: list[str]


def _safe_run_command(cmd: list[str]) -> str | None:
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def resolve_git_commit() -> str | None:
    return _safe_run_command(["git", "rev-parse", "HEAD"])


def resolve_environment_lock() -> str | None:
    return _safe_run_command([sys.executable, "-m", "pip", "freeze"])


def build_run_manifest(context: NotebookRunContext) -> RunManifest:
    """Create a RunManifest for notebook outputs."""
    return RunManifest(
        run_id=context.run_id,
        methodology_version=context.methodology_version,
        created_at=datetime.utcnow(),
        git_commit_hash=resolve_git_commit(),
        quartumse_version=__version__,
        python_version=sys.version.split()[0],
        environment_lock=resolve_environment_lock(),
        config=context.config,
        circuits=context.circuits,
        observable_sets=context.observable_sets,
        protocols=context.protocols,
        N_grid=context.N_grid,
        n_replicates=context.n_replicates,
        noise_profiles=context.noise_profiles,
    )


def ensure_output_dirs(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "plots").mkdir(parents=True, exist_ok=True)
    return output_dir


def finalize_notebook_run(
    context: NotebookRunContext,
    result_set: LongFormResultSet,
    task_results: list[TaskResult],
    epsilon: float | None = None,
) -> dict[str, Path]:
    """Write long-form, summary, task results, and manifest artifacts."""
    output_dir = ensure_output_dirs(context.output_dir)
    writer = ParquetWriter(output_dir)
    long_form_path = writer.write_long_form(result_set)
    summary_rows = SummaryAggregator(result_set, epsilon=epsilon).compute_summaries()
    summary_path = writer.write_summary(summary_rows)
    task_results_path = writer.write_task_results(task_results) if task_results else None

    manifest = build_run_manifest(context)
    manifest.long_form_path = str(long_form_path)
    manifest.summary_path = str(summary_path)
    manifest.task_results_path = str(task_results_path) if task_results_path else None
    manifest.plots_dir = str(output_dir / "plots")
    manifest.status = "completed"
    manifest.completed_at = datetime.utcnow()

    manifest_path = writer.write_manifest(manifest)

    return {
        "long_form": Path(long_form_path),
        "summary": Path(summary_path),
        "task_results": Path(task_results_path) if task_results_path else None,
        "manifest": Path(manifest_path),
        "plots": output_dir / "plots",
    }
