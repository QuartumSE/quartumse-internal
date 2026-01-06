"""Visualization utilities for benchmark results (Measurements Bible §10.3).

This module provides standard plots for analyzing and comparing
protocol performance.

Required plots:
- Attainment curves: f(N;ε) vs N for each protocol
- SSF bar charts: Shot-savings factor comparisons
- SE distribution plots: Box/violin plots of SE across observables
- Crossover plots: Where protocols switch dominance
- Coverage plots: Empirical vs nominal coverage
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

# Try to import matplotlib, but provide fallback
try:
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.axes import Axes

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    Figure = Any
    Axes = Any


def _check_matplotlib() -> None:
    """Check if matplotlib is available."""
    if not HAS_MATPLOTLIB:
        raise ImportError(
            "Visualization requires matplotlib. "
            "Install with: pip install matplotlib"
        )


@dataclass
class PlotConfig:
    """Configuration for plots.

    Attributes:
        figsize: Figure size (width, height).
        dpi: Figure DPI.
        style: Matplotlib style.
        palette: Color palette.
        save_format: Format for saving figures.
    """

    figsize: tuple[float, float] = (10, 6)
    dpi: int = 150
    style: str = "seaborn-v0_8-whitegrid"
    palette: list[str] | None = None
    save_format: str = "png"

    def __post_init__(self) -> None:
        if self.palette is None:
            self.palette = [
                "#1f77b4",  # Blue
                "#ff7f0e",  # Orange
                "#2ca02c",  # Green
                "#d62728",  # Red
                "#9467bd",  # Purple
                "#8c564b",  # Brown
            ]


def plot_attainment_curves(
    attainment_data: dict[str, dict[int, float]],
    epsilon: float,
    config: PlotConfig | None = None,
    ax: Axes | None = None,
) -> Figure:
    """Plot attainment curves for multiple protocols.

    f(N;ε) = fraction of observables with SE ≤ ε

    Args:
        attainment_data: Dict mapping protocol_id to {N: attainment}.
        epsilon: Target precision used.
        config: Plot configuration.
        ax: Existing axes to plot on.

    Returns:
        Matplotlib Figure.
    """
    _check_matplotlib()
    config = config or PlotConfig()

    if ax is None:
        fig, ax = plt.subplots(figsize=config.figsize, dpi=config.dpi)
    else:
        fig = ax.get_figure()

    for i, (protocol_id, data) in enumerate(attainment_data.items()):
        ns = sorted(data.keys())
        attainments = [data[n] for n in ns]
        color = config.palette[i % len(config.palette)]
        ax.plot(ns, attainments, "o-", label=protocol_id, color=color, linewidth=2)

    ax.set_xlabel("Shot Budget (N)", fontsize=12)
    ax.set_ylabel(f"Attainment f(N; ε={epsilon})", fontsize=12)
    ax.set_title("Attainment Curves", fontsize=14)
    ax.set_xscale("log")
    ax.set_ylim(0, 1.05)
    ax.axhline(y=1.0, color="gray", linestyle="--", alpha=0.5)
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_ssf_comparison(
    ssf_data: dict[str, float],
    baseline_id: str,
    config: PlotConfig | None = None,
    ax: Axes | None = None,
) -> Figure:
    """Plot shot-savings factor bar chart.

    Args:
        ssf_data: Dict mapping protocol_id to SSF value.
        baseline_id: Baseline protocol ID (SSF=1).
        config: Plot configuration.
        ax: Existing axes to plot on.

    Returns:
        Matplotlib Figure.
    """
    _check_matplotlib()
    config = config or PlotConfig()

    if ax is None:
        fig, ax = plt.subplots(figsize=config.figsize, dpi=config.dpi)
    else:
        fig = ax.get_figure()

    protocols = list(ssf_data.keys())
    ssfs = list(ssf_data.values())
    colors = [
        config.palette[0] if ssf >= 1 else config.palette[3]
        for ssf in ssfs
    ]

    bars = ax.bar(protocols, ssfs, color=colors, edgecolor="black")
    ax.axhline(y=1.0, color="gray", linestyle="--", linewidth=2, label=f"Baseline ({baseline_id})")

    ax.set_xlabel("Protocol", fontsize=12)
    ax.set_ylabel("Shot-Savings Factor (SSF)", fontsize=12)
    ax.set_title(f"Shot-Savings Factor vs {baseline_id}", fontsize=14)
    ax.set_ylim(0, max(ssfs) * 1.2)

    # Add value labels on bars
    for bar, ssf in zip(bars, ssfs):
        height = bar.get_height()
        ax.annotate(
            f"{ssf:.2f}×",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    ax.legend()
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    return fig


def plot_se_distribution(
    se_data: dict[str, list[float]],
    n_total: int,
    epsilon: float | None = None,
    config: PlotConfig | None = None,
    ax: Axes | None = None,
) -> Figure:
    """Plot SE distribution across observables.

    Args:
        se_data: Dict mapping protocol_id to list of SE values.
        n_total: Shot budget.
        epsilon: Target precision (for reference line).
        config: Plot configuration.
        ax: Existing axes to plot on.

    Returns:
        Matplotlib Figure.
    """
    _check_matplotlib()
    config = config or PlotConfig()

    if ax is None:
        fig, ax = plt.subplots(figsize=config.figsize, dpi=config.dpi)
    else:
        fig = ax.get_figure()

    protocols = list(se_data.keys())
    data = [se_data[p] for p in protocols]

    # Box plot
    bp = ax.boxplot(
        data,
        labels=protocols,
        patch_artist=True,
        showfliers=True,
    )

    # Color boxes
    for i, patch in enumerate(bp["boxes"]):
        patch.set_facecolor(config.palette[i % len(config.palette)])
        patch.set_alpha(0.7)

    if epsilon is not None:
        ax.axhline(y=epsilon, color="red", linestyle="--", linewidth=2, label=f"Target ε={epsilon}")

    ax.set_xlabel("Protocol", fontsize=12)
    ax.set_ylabel("Standard Error (SE)", fontsize=12)
    ax.set_title(f"SE Distribution at N={n_total:,}", fontsize=14)
    ax.set_yscale("log")

    if epsilon is not None:
        ax.legend()

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    return fig


def plot_convergence(
    convergence_data: dict[str, dict[int, dict[str, float]]],
    metric: str = "mean_se",
    config: PlotConfig | None = None,
    ax: Axes | None = None,
) -> Figure:
    """Plot convergence of metrics vs shot budget.

    Args:
        convergence_data: Dict mapping protocol_id to {N: {metric: value}}.
        metric: Which metric to plot.
        config: Plot configuration.
        ax: Existing axes to plot on.

    Returns:
        Matplotlib Figure.
    """
    _check_matplotlib()
    config = config or PlotConfig()

    if ax is None:
        fig, ax = plt.subplots(figsize=config.figsize, dpi=config.dpi)
    else:
        fig = ax.get_figure()

    for i, (protocol_id, data) in enumerate(convergence_data.items()):
        ns = sorted(data.keys())
        values = [data[n].get(metric, 0) for n in ns]
        color = config.palette[i % len(config.palette)]
        ax.plot(ns, values, "o-", label=protocol_id, color=color, linewidth=2)

    ax.set_xlabel("Shot Budget (N)", fontsize=12)
    ax.set_ylabel(metric.replace("_", " ").title(), fontsize=12)
    ax.set_title(f"{metric.replace('_', ' ').title()} vs Shot Budget", fontsize=14)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_crossover(
    metrics_a: dict[int, float],
    metrics_b: dict[int, float],
    protocol_a: str,
    protocol_b: str,
    crossover_n: int | None = None,
    config: PlotConfig | None = None,
    ax: Axes | None = None,
) -> Figure:
    """Plot crossover between two protocols.

    Args:
        metrics_a: {N: metric} for protocol A.
        metrics_b: {N: metric} for protocol B.
        protocol_a: Name of protocol A.
        protocol_b: Name of protocol B.
        crossover_n: Crossover point (if known).
        config: Plot configuration.
        ax: Existing axes to plot on.

    Returns:
        Matplotlib Figure.
    """
    _check_matplotlib()
    config = config or PlotConfig()

    if ax is None:
        fig, ax = plt.subplots(figsize=config.figsize, dpi=config.dpi)
    else:
        fig = ax.get_figure()

    common_ns = sorted(set(metrics_a.keys()) & set(metrics_b.keys()))

    ax.plot(
        common_ns,
        [metrics_a[n] for n in common_ns],
        "o-",
        label=protocol_a,
        color=config.palette[0],
        linewidth=2,
    )
    ax.plot(
        common_ns,
        [metrics_b[n] for n in common_ns],
        "s-",
        label=protocol_b,
        color=config.palette[1],
        linewidth=2,
    )

    if crossover_n is not None:
        ax.axvline(
            x=crossover_n,
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Crossover N={crossover_n:,}",
        )

    ax.set_xlabel("Shot Budget (N)", fontsize=12)
    ax.set_ylabel("Metric", fontsize=12)
    ax.set_title(f"Crossover: {protocol_a} vs {protocol_b}", fontsize=14)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_coverage(
    coverage_data: dict[str, dict[int, float]],
    nominal_coverage: float = 0.95,
    config: PlotConfig | None = None,
    ax: Axes | None = None,
) -> Figure:
    """Plot empirical coverage vs shot budget.

    Args:
        coverage_data: Dict mapping protocol_id to {N: coverage}.
        nominal_coverage: Nominal coverage level.
        config: Plot configuration.
        ax: Existing axes to plot on.

    Returns:
        Matplotlib Figure.
    """
    _check_matplotlib()
    config = config or PlotConfig()

    if ax is None:
        fig, ax = plt.subplots(figsize=config.figsize, dpi=config.dpi)
    else:
        fig = ax.get_figure()

    for i, (protocol_id, data) in enumerate(coverage_data.items()):
        ns = sorted(data.keys())
        coverages = [data[n] for n in ns]
        color = config.palette[i % len(config.palette)]
        ax.plot(ns, coverages, "o-", label=protocol_id, color=color, linewidth=2)

    ax.axhline(
        y=nominal_coverage,
        color="red",
        linestyle="--",
        linewidth=2,
        label=f"Nominal ({nominal_coverage:.0%})",
    )

    ax.set_xlabel("Shot Budget (N)", fontsize=12)
    ax.set_ylabel("Empirical Coverage", fontsize=12)
    ax.set_title("Coverage vs Shot Budget", fontsize=14)
    ax.set_xscale("log")
    ax.set_ylim(0.8, 1.02)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_bias_variance(
    bias_data: dict[int, float],
    variance_data: dict[int, float],
    rmse_data: dict[int, float],
    protocol_id: str,
    config: PlotConfig | None = None,
) -> Figure:
    """Plot bias-variance decomposition.

    Args:
        bias_data: {N: mean_abs_bias}.
        variance_data: {N: mean_variance}.
        rmse_data: {N: mean_rmse}.
        protocol_id: Protocol identifier.
        config: Plot configuration.

    Returns:
        Matplotlib Figure.
    """
    _check_matplotlib()
    config = config or PlotConfig()

    fig, ax = plt.subplots(figsize=config.figsize, dpi=config.dpi)

    ns = sorted(set(bias_data.keys()) & set(variance_data.keys()) & set(rmse_data.keys()))

    ax.plot(
        ns,
        [bias_data[n] for n in ns],
        "o-",
        label="Bias",
        color=config.palette[0],
        linewidth=2,
    )
    ax.plot(
        ns,
        [np.sqrt(variance_data[n]) for n in ns],
        "s-",
        label="Std Dev",
        color=config.palette[1],
        linewidth=2,
    )
    ax.plot(
        ns,
        [rmse_data[n] for n in ns],
        "^-",
        label="RMSE",
        color=config.palette[2],
        linewidth=2,
    )

    ax.set_xlabel("Shot Budget (N)", fontsize=12)
    ax.set_ylabel("Error", fontsize=12)
    ax.set_title(f"Bias-Variance Decomposition: {protocol_id}", fontsize=14)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def create_benchmark_report(
    results_summary: dict[str, Any],
    output_dir: str,
    config: PlotConfig | None = None,
) -> list[str]:
    """Generate all standard benchmark plots.

    Args:
        results_summary: Summary of benchmark results.
        output_dir: Directory to save plots.
        config: Plot configuration.

    Returns:
        List of saved plot paths.
    """
    _check_matplotlib()
    import os

    os.makedirs(output_dir, exist_ok=True)
    config = config or PlotConfig()
    saved_paths = []

    # Generate available plots based on data
    if "attainment" in results_summary:
        fig = plot_attainment_curves(
            results_summary["attainment"],
            results_summary.get("epsilon", 0.01),
            config,
        )
        path = os.path.join(output_dir, f"attainment.{config.save_format}")
        fig.savefig(path, dpi=config.dpi)
        plt.close(fig)
        saved_paths.append(path)

    if "ssf" in results_summary:
        fig = plot_ssf_comparison(
            results_summary["ssf"],
            results_summary.get("baseline", "direct_grouped"),
            config,
        )
        path = os.path.join(output_dir, f"ssf.{config.save_format}")
        fig.savefig(path, dpi=config.dpi)
        plt.close(fig)
        saved_paths.append(path)

    if "se_distribution" in results_summary:
        for n, se_data in results_summary["se_distribution"].items():
            fig = plot_se_distribution(
                se_data,
                n,
                results_summary.get("epsilon"),
                config,
            )
            path = os.path.join(output_dir, f"se_dist_N{n}.{config.save_format}")
            fig.savefig(path, dpi=config.dpi)
            plt.close(fig)
            saved_paths.append(path)

    if "coverage" in results_summary:
        fig = plot_coverage(
            results_summary["coverage"],
            results_summary.get("confidence_level", 0.95),
            config,
        )
        path = os.path.join(output_dir, f"coverage.{config.save_format}")
        fig.savefig(path, dpi=config.dpi)
        plt.close(fig)
        saved_paths.append(path)

    return saved_paths
