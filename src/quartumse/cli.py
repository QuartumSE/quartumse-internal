"""
QuartumSE CLI.

Command-line interface for running experiments, generating reports, etc.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="quartumse", help="Quantum measurement optimization toolkit")
console = Console()


class BackendConfig(BaseModel):
    """Backend configuration parsed from YAML or CLI overrides."""

    provider: str = Field(default="local", description="Backend provider namespace")
    name: str = Field(description="Backend identifier")

    @model_validator(mode="before")
    @classmethod
    def _parse_descriptor(cls, value: Any) -> Dict[str, Any]:
        if isinstance(value, str):
            provider, sep, name = value.partition(":")
            if sep:
                return {"provider": provider or "local", "name": name}
            return {"provider": "local", "name": value}
        return value

    @property
    def descriptor(self) -> str:
        """Return provider-qualified descriptor."""

        if self.provider and self.provider != "local":
            return f"{self.provider}:{self.name}"
        return self.name


class ExperimentConfig(BaseModel):
    """Top-level experiment configuration schema."""

    backend: BackendConfig = Field(default_factory=lambda: BackendConfig(name="aer_simulator"))
    num_qubits: Optional[list[int]] = Field(default=None, description="Target qubit counts")
    shadow_size: Optional[int] = Field(default=None, ge=1, description="Shadows per circuit")
    baseline_shots: Optional[int] = Field(default=None, ge=1, description="Baseline shot count")
    random_seed: Optional[int] = Field(default=None, description="Random seed override")


def _load_yaml_config(path: Path) -> Dict[str, Any]:
    """Load YAML configuration from disk."""

    if not path.exists():
        raise typer.BadParameter(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise typer.BadParameter("Experiment config must be a mapping at the top level")

    return data


def _parse_experiment_config(data: Dict[str, Any]) -> ExperimentConfig:
    """Validate YAML payload into :class:`ExperimentConfig`."""

    try:
        return ExperimentConfig.model_validate(data)
    except ValidationError as exc:
        console.print("[red]Invalid experiment configuration:[/red]")
        console.print(exc, style="red")
        raise typer.Exit(code=1)


@app.command()
def version():
    """Show QuartumSE version."""
    from quartumse import __version__

    console.print(f"QuartumSE version {__version__}", style="bold green")


@app.command()
def run(
    config: str = typer.Option(..., help="Path to experiment config YAML"),
    backend: Optional[str] = typer.Option(
        None,
        help="Override backend descriptor (e.g., ibm:ibmq_qasm_simulator)",
    ),
):
    """Validate configuration and resolve experiment backend."""

    config_path = Path(config)
    raw_config = _load_yaml_config(config_path)
    experiment_config = _parse_experiment_config(raw_config)

    backend_descriptor = backend or experiment_config.backend.descriptor

    console.print(f"[cyan]Configuration loaded from {config_path}[/cyan]")
    console.print(f"[cyan]Resolved backend descriptor: {backend_descriptor}[/cyan]")

    if backend_descriptor.startswith("ibm:"):
        console.print(
            "[green]IBM Quantum backend selected. Configure credentials via "
            "QISKIT_IBM_TOKEN/QISKIT_RUNTIME_API_TOKEN or saved Qiskit Runtime accounts.[/green]"
        )

    from quartumse import ShadowEstimator

    estimator = ShadowEstimator(backend=backend_descriptor)
    snapshot = getattr(estimator, "_backend_snapshot", None)

    if snapshot is not None:
        console.print(
            f"[green]Calibration snapshot captured at {snapshot.calibration_timestamp.isoformat()} "
            f"(hash={snapshot.properties_hash[:8] if snapshot.properties_hash else 'n/a'})[/green]"
        )
    else:
        console.print(
            "[yellow]Backend did not expose calibration data at instantiation. "
            "It will be captured during execution if available.[/yellow]"
        )

    console.print(
        "[yellow]Experiment execution via CLI is under development. "
        "Use experiments/shadows/S_T01_ghz_baseline.py or notebooks to run circuits.[/yellow]"
    )


@app.command("calibrate-readout")
def calibrate_readout(
    backend: str = typer.Option(
        ..., "--backend", "-b", help="Backend descriptor (e.g., ibm:ibm_brisbane)"
    ),
    qubit: List[int] = typer.Option(
        ..., "--qubit", "-q", help="Qubit index to include; repeat for multiple qubits"
    ),
    shots: int = typer.Option(4096, help="Shots per computational basis state"),
    output_dir: Path = typer.Option(
        Path("validation_data/calibrations"),
        "--output-dir",
        "-o",
        help="Directory for calibration artifacts",
    ),
    force: bool = typer.Option(
        False, "--force", help="Force recalibration even if a cached artifact exists"
    ),
    max_age_hours: Optional[float] = typer.Option(
        None,
        "--max-age-hours",
        help="Refresh calibration if the cached artifact is older than this many hours",
    ),
):
    """Calibrate readout confusion matrices and persist metadata."""

    if not qubit:
        raise typer.BadParameter("At least one --qubit index must be provided")
    if shots <= 0:
        raise typer.BadParameter("--shots must be a positive integer")

    from quartumse.connectors import resolve_backend
    from quartumse.mitigation import ReadoutCalibrationManager

    backend_instance, _ = resolve_backend(backend)
    manager = ReadoutCalibrationManager(base_dir=output_dir)
    max_age = timedelta(hours=max_age_hours) if max_age_hours is not None else None

    record = manager.ensure_calibration(
        backend_instance,
        qubit,
        shots=shots,
        force=force,
        max_age=max_age,
    )

    mitigation_config = record.to_mitigation_config()
    manifest_payload = {
        "generated_at": datetime.utcnow().isoformat(),
        "backend_descriptor": backend,
        "backend_name": record.backend_name,
        "backend_version": record.backend_version,
        "qubits": list(record.qubits),
        "shots_per_state": record.shots_per_state,
        "total_shots": record.total_shots,
        "reused": record.reused,
        "calibration_created_at": record.created_at.isoformat(),
        "confusion_matrix_path": str(record.path),
        "mitigation": mitigation_config.model_dump(),
    }

    manifest_path = record.path.with_suffix(".manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest_payload, handle, indent=2)
        handle.write("\n")

    status = "reused" if record.reused else "generated"
    console.print(
        f"[green]Calibration {status} for backend {record.backend_name} on qubits {list(record.qubits)}.[/green]"
    )
    console.print(f"[cyan]Confusion matrix:[/cyan] {record.path}")
    console.print(f"[cyan]Manifest snippet:[/cyan] {manifest_path}")
    console.print(
        "[yellow]Reference this path via MitigationConfig.confusion_matrix_path in manifests.[/yellow]"
    )


@app.command()
def report(
    manifest: str = typer.Argument(..., help="Path to manifest JSON"),
    output: str = typer.Option("report.html", help="Output path"),
):
    """Generate report from manifest."""
    from quartumse.reporting import ReportGenerator

    console.print(f"[yellow]Generating report from {manifest}...[/yellow]")
    report = ReportGenerator.from_manifest_file(manifest)
    report.to_html(output)
    console.print(f"[green]Report saved to {output}[/green]")


@app.command()
def benchmark(
    suite: str = typer.Option("all", help="Benchmark suite to run"),
):
    """Run benchmark suite."""
    console.print(f"[yellow]Running benchmark suite: {suite}[/yellow]")
    console.print("[red]Not implemented yet![/red]")


@app.command("runtime-status")
def runtime_status(
    backend: str = typer.Option(
        "ibm:ibmq_qasm_simulator",
        "--backend",
        "-b",
        help="Backend descriptor to query (e.g., ibm:ibm_brisbane)",
    ),
    instance: Optional[str] = typer.Option(
        None,
        "--instance",
        help="IBM Quantum hub/group/project instance override",
        envvar="QISKIT_IBM_INSTANCE",
    ),
    channel: Optional[str] = typer.Option(
        None,
        "--channel",
        help="IBM Quantum channel override",
        envvar="QISKIT_IBM_CHANNEL",
    ),
    token: Optional[str] = typer.Option(
        None,
        "--token",
        help="IBM Quantum API token override",
        envvar="QISKIT_IBM_TOKEN",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Emit machine-readable JSON instead of a formatted table.",
    ),
    slack_webhook: Optional[str] = typer.Option(
        None,
        "--slack-webhook",
        help="Optional Slack-compatible webhook URL (env: QUARTUMSE_SLACK_WEBHOOK).",
        envvar="QUARTUMSE_SLACK_WEBHOOK",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Skip webhook delivery while still printing the notification payload.",
    ),
):
    """Report IBM queue depth and runtime quota usage."""

    from quartumse.utils.runtime_monitor import (
        build_notification_message,
        collect_runtime_status,
        post_to_webhook,
        report_to_dict,
        seconds_to_pretty,
    )

    provider, sep, backend_name = backend.partition(":")
    if sep:
        provider = provider.lower()
        if provider != "ibm":
            console.print(
                f"[red]Unsupported provider '{provider}'. Only 'ibm' descriptors are supported.[/red]"
            )
            raise typer.Exit(code=1)
        if not backend_name:
            console.print("[red]Backend descriptor must include a backend name.[/red]")
            raise typer.Exit(code=1)
    else:
        backend_name = provider

    service_kwargs: Dict[str, str] = {}
    if instance:
        service_kwargs["instance"] = instance
    if channel:
        service_kwargs["channel"] = channel
    if token:
        service_kwargs["token"] = token

    try:
        report = collect_runtime_status(backend_name, service_kwargs=service_kwargs)
    except ImportError as exc:
        console.print(
            "[red]qiskit-ibm-runtime is not installed. Install it via `pip install qiskit-ibm-runtime` or ``quartumse[aws]`` extras.[/red]"
        )
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # pylint: disable=broad-except
        console.print(f"[red]Failed to query runtime status: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    if output_json:
        console.print(json.dumps(report_to_dict(report), indent=2))
    else:
        table = Table(title="IBM Runtime Status", show_header=False)
        table.add_column("Metric", style="cyan", justify="left")
        table.add_column("Value", style="white", justify="left")

        table.add_row("Backend", report.queue.backend_name)
        queue_value = "unknown" if report.queue.pending_jobs is None else str(report.queue.pending_jobs)
        if report.queue.operational is not None:
            queue_value += f" (operational={report.queue.operational})"
        table.add_row("Queue depth", queue_value)
        if report.queue.status_msg:
            table.add_row("Status message", report.queue.status_msg)

        usage_parts = []
        if report.quota.consumed_seconds is not None:
            usage_parts.append(f"used {seconds_to_pretty(report.quota.consumed_seconds)}")
        if report.quota.limit_seconds is not None:
            usage_parts.append(f"limit {seconds_to_pretty(report.quota.limit_seconds)}")
        if report.quota.remaining_seconds is not None:
            usage_parts.append(f"remaining {seconds_to_pretty(report.quota.remaining_seconds)}")
        usage_value = ", ".join(usage_parts) if usage_parts else "unknown"
        table.add_row("Runtime quota", usage_value)

        if report.quota.plan:
            table.add_row("Plan", report.quota.plan)
        if report.quota.max_pending_jobs is not None:
            current = report.quota.current_pending_jobs
            table.add_row(
                "Pending job cap",
                f"{current if current is not None else '?'} / {report.quota.max_pending_jobs}",
            )
        if report.quota.refresh_date is not None:
            table.add_row("Refresh date", report.quota.refresh_date.isoformat())

        table.add_row("Captured", report.collected_at.isoformat())
        console.print(table)

    if slack_webhook:
        message = build_notification_message(report)
        console.print("[cyan]Webhook payload:[/cyan]")
        console.print(message)
        try:
            post_to_webhook(slack_webhook, message, dry_run=dry_run)
        except Exception as exc:  # pylint: disable=broad-except
            console.print(f"[red]Failed to deliver webhook notification: {exc}[/red]")
            raise typer.Exit(code=1) from exc
        else:
            if dry_run:
                console.print("[yellow]Dry-run enabled: webhook delivery skipped.[/yellow]")
            else:
                console.print("[green]Notification delivered successfully.[/green]")


if __name__ == "__main__":
    app()
