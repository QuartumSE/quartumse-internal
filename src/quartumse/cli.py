"""
QuartumSE CLI.

Command-line interface for running experiments, generating reports, etc.
"""

from pathlib import Path
from typing import Any, Dict, Optional

import typer
import yaml
from pydantic import BaseModel, Field, ValidationError, model_validator
from rich.console import Console

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


if __name__ == "__main__":
    app()
