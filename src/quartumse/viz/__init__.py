"""Visualization and reporting utilities (Measurements Bible §10.3).

This package provides:
- Standard benchmark plots (attainment, SSF, distribution, coverage)
- Report generation in Markdown and HTML formats
- Configurable plot styling

Usage:
    from quartumse.viz import (
        # Plotting
        plot_attainment_curves,
        plot_ssf_comparison,
        plot_se_distribution,
        plot_convergence,
        plot_crossover,
        plot_coverage,
        plot_bias_variance,
        create_benchmark_report,
        PlotConfig,
        # Reporting
        BenchmarkReport,
        ReportBuilder,
        ReportSection,
    )

    # Create attainment plot
    fig = plot_attainment_curves(
        attainment_data={"shadows": {100: 0.5, 1000: 0.9}, "direct": {100: 0.3, 1000: 0.7}},
        epsilon=0.01,
    )
    fig.savefig("attainment.png")

    # Build report
    report = (
        ReportBuilder(run_id="run_001")
        .add_overview_section(n_protocols=2, n_circuits=1, n_observables=100, n_replicates=10, n_grid=[100, 1000])
        .add_figures_section(["attainment.png"])
        .build()
    )
    report.save("reports/", formats=["md", "html"])
"""

from .plots import (
    PlotConfig,
    create_benchmark_report,
    plot_attainment_curves,
    plot_bias_variance,
    plot_convergence,
    plot_coverage,
    plot_crossover,
    plot_se_distribution,
    plot_ssf_comparison,
)
from .reports import (
    BenchmarkReport,
    ReportBuilder,
    ReportSection,
)

__all__ = [
    # Plot configuration
    "PlotConfig",
    # Standard plots
    "plot_attainment_curves",
    "plot_ssf_comparison",
    "plot_se_distribution",
    "plot_convergence",
    "plot_crossover",
    "plot_coverage",
    "plot_bias_variance",
    "create_benchmark_report",
    # Reporting
    "BenchmarkReport",
    "ReportBuilder",
    "ReportSection",
]
