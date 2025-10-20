"""
QuartumSE CLI.

Command-line interface for running experiments, generating reports, etc.
"""

import typer
from rich.console import Console

app = typer.Typer(name="quartumse", help="Quantum measurement optimization toolkit")
console = Console()


@app.command()
def version():
    """Show QuartumSE version."""
    from quartumse import __version__

    console.print(f"QuartumSE version {__version__}", style="bold green")


@app.command()
def run(
    config: str = typer.Option(..., help="Path to experiment config YAML"),
    backend: str = typer.Option("aer_simulator", help="Backend name"),
):
    """Run an experiment from config file."""
    console.print(f"[yellow]Running experiment with config: {config}[/yellow]")
    console.print(f"[yellow]Backend: {backend}[/yellow]")
    # TODO: Implement experiment runner
    console.print("[red]Not implemented yet![/red]")


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
    # TODO: Implement benchmark runner
    console.print("[red]Not implemented yet![/red]")


if __name__ == "__main__":
    app()
