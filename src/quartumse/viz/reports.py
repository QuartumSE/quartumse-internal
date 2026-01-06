"""Report generation utilities (Measurements Bible §10).

This module provides utilities for generating comprehensive benchmark
reports in various formats.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ..io.schemas import RunManifest, SummaryRow, TaskResult


@dataclass
class ReportSection:
    """A section of a benchmark report.

    Attributes:
        title: Section title.
        content: Section content (text or data).
        subsections: Nested subsections.
        figures: Associated figure paths.
        tables: Associated table data.
    """

    title: str
    content: str = ""
    subsections: list[ReportSection] = field(default_factory=list)
    figures: list[str] = field(default_factory=list)
    tables: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class BenchmarkReport:
    """A complete benchmark report.

    Attributes:
        title: Report title.
        run_id: Benchmark run identifier.
        created_at: Report creation timestamp.
        methodology_version: Measurements Bible version.
        sections: Report sections.
        manifest: Run manifest.
        metadata: Additional metadata.
    """

    title: str
    run_id: str
    created_at: datetime = field(default_factory=datetime.now)
    methodology_version: str = "3.0.0"
    sections: list[ReportSection] = field(default_factory=list)
    manifest: RunManifest | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_section(self, section: ReportSection) -> None:
        """Add a section to the report."""
        self.sections.append(section)

    def to_markdown(self) -> str:
        """Convert report to Markdown format."""
        lines = []

        # Title and metadata
        lines.append(f"# {self.title}")
        lines.append("")
        lines.append(f"**Run ID:** {self.run_id}")
        lines.append(f"**Created:** {self.created_at.isoformat()}")
        lines.append(f"**Methodology Version:** {self.methodology_version}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Sections
        for section in self.sections:
            lines.extend(self._section_to_markdown(section, level=2))

        return "\n".join(lines)

    def _section_to_markdown(
        self,
        section: ReportSection,
        level: int = 2,
    ) -> list[str]:
        """Convert a section to Markdown lines."""
        lines = []
        prefix = "#" * level

        lines.append(f"{prefix} {section.title}")
        lines.append("")

        if section.content:
            lines.append(section.content)
            lines.append("")

        # Tables
        for table in section.tables:
            lines.extend(self._table_to_markdown(table))
            lines.append("")

        # Figures
        for figure_path in section.figures:
            lines.append(f"![{section.title}]({figure_path})")
            lines.append("")

        # Subsections
        for subsection in section.subsections:
            lines.extend(self._section_to_markdown(subsection, level + 1))

        return lines

    def _table_to_markdown(self, table: dict[str, Any]) -> list[str]:
        """Convert a table dict to Markdown."""
        lines = []

        if "title" in table:
            lines.append(f"**{table['title']}**")
            lines.append("")

        if "headers" in table and "rows" in table:
            headers = table["headers"]
            rows = table["rows"]

            # Header row
            lines.append("| " + " | ".join(str(h) for h in headers) + " |")
            # Separator
            lines.append("| " + " | ".join("---" for _ in headers) + " |")
            # Data rows
            for row in rows:
                lines.append("| " + " | ".join(str(v) for v in row) + " |")

        return lines

    def to_html(self) -> str:
        """Convert report to HTML format."""
        md_content = self.to_markdown()

        # Simple Markdown to HTML conversion
        # In production, use a proper Markdown library
        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{self.title}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }",
            "table { border-collapse: collapse; width: 100%; margin: 20px 0; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #4CAF50; color: white; }",
            "tr:nth-child(even) { background-color: #f2f2f2; }",
            "img { max-width: 100%; height: auto; }",
            "h1 { color: #333; }",
            "h2 { color: #666; border-bottom: 1px solid #ddd; }",
            "</style>",
            "</head>",
            "<body>",
        ]

        # Convert markdown content to basic HTML
        for line in md_content.split("\n"):
            if line.startswith("# "):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("**") and line.endswith("**"):
                html_lines.append(f"<strong>{line[2:-2]}</strong><br>")
            elif line.startswith("!["):
                # Image
                alt_end = line.index("]")
                path_start = line.index("(") + 1
                path_end = line.index(")")
                alt = line[2:alt_end]
                path = line[path_start:path_end]
                html_lines.append(f'<img src="{path}" alt="{alt}">')
            elif line.startswith("|"):
                # Table row - simplified handling
                cells = line.split("|")[1:-1]
                if all(c.strip() == "---" for c in cells):
                    continue  # Skip separator
                tag = "th" if not hasattr(self, "_in_table_body") else "td"
                if tag == "th":
                    html_lines.append("<table><tr>")
                    self._in_table_body = True
                else:
                    html_lines.append("<tr>")
                for cell in cells:
                    html_lines.append(f"<{tag}>{cell.strip()}</{tag}>")
                html_lines.append("</tr>")
            elif line == "---":
                html_lines.append("<hr>")
            elif line:
                html_lines.append(f"<p>{line}</p>")

        html_lines.extend(["</body>", "</html>"])
        return "\n".join(html_lines)

    def save(self, output_dir: str | Path, formats: list[str] = None) -> list[str]:
        """Save report in specified formats.

        Args:
            output_dir: Output directory.
            formats: List of formats ("md", "html", "json").

        Returns:
            List of saved file paths.
        """
        if formats is None:
            formats = ["md", "html"]

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved = []

        if "md" in formats:
            path = output_dir / f"report_{self.run_id}.md"
            path.write_text(self.to_markdown())
            saved.append(str(path))

        if "html" in formats:
            path = output_dir / f"report_{self.run_id}.html"
            path.write_text(self.to_html())
            saved.append(str(path))

        if "json" in formats:
            path = output_dir / f"report_{self.run_id}.json"
            data = {
                "title": self.title,
                "run_id": self.run_id,
                "created_at": self.created_at.isoformat(),
                "methodology_version": self.methodology_version,
                "metadata": self.metadata,
            }
            path.write_text(json.dumps(data, indent=2))
            saved.append(str(path))

        return saved


class ReportBuilder:
    """Builder for constructing benchmark reports."""

    def __init__(self, run_id: str, title: str | None = None) -> None:
        """Initialize report builder.

        Args:
            run_id: Benchmark run identifier.
            title: Report title.
        """
        self.report = BenchmarkReport(
            title=title or f"Benchmark Report: {run_id}",
            run_id=run_id,
        )

    def with_manifest(self, manifest: RunManifest) -> ReportBuilder:
        """Add run manifest."""
        self.report.manifest = manifest
        self.report.methodology_version = manifest.methodology_version
        return self

    def add_overview_section(
        self,
        n_protocols: int,
        n_circuits: int,
        n_observables: int,
        n_replicates: int,
        n_grid: list[int],
    ) -> ReportBuilder:
        """Add overview section."""
        section = ReportSection(
            title="Overview",
            content=f"This report summarizes benchmark results comparing {n_protocols} protocols "
            f"across {n_circuits} circuits with {n_observables} observables.",
            tables=[
                {
                    "title": "Benchmark Configuration",
                    "headers": ["Parameter", "Value"],
                    "rows": [
                        ["Protocols", n_protocols],
                        ["Circuits", n_circuits],
                        ["Observables", n_observables],
                        ["Replicates", n_replicates],
                        ["Shot budgets", f"{min(n_grid):,} - {max(n_grid):,}"],
                    ],
                }
            ],
        )
        self.report.add_section(section)
        return self

    def add_summary_section(
        self,
        summaries: list[SummaryRow],
    ) -> ReportBuilder:
        """Add summary statistics section."""
        # Group by protocol
        by_protocol: dict[str, list[SummaryRow]] = {}
        for s in summaries:
            if s.protocol_id not in by_protocol:
                by_protocol[s.protocol_id] = []
            by_protocol[s.protocol_id].append(s)

        rows = []
        for protocol_id, protocol_summaries in by_protocol.items():
            mean_se = sum(s.se_mean for s in protocol_summaries) / len(protocol_summaries)
            max_se = max(s.se_max for s in protocol_summaries)
            rows.append([protocol_id, f"{mean_se:.4f}", f"{max_se:.4f}"])

        section = ReportSection(
            title="Summary Statistics",
            tables=[
                {
                    "title": "Protocol Performance Summary",
                    "headers": ["Protocol", "Mean SE", "Max SE"],
                    "rows": rows,
                }
            ],
        )
        self.report.add_section(section)
        return self

    def add_task_results_section(
        self,
        task_results: list[TaskResult],
    ) -> ReportBuilder:
        """Add task results section."""
        rows = []
        for result in task_results:
            rows.append([
                result.task_id,
                result.protocol_id,
                result.N_star or "N/A",
                f"{result.ssf:.2f}×" if result.ssf else "N/A",
            ])

        section = ReportSection(
            title="Task Results",
            tables=[
                {
                    "title": "Benchmark Task Outcomes",
                    "headers": ["Task", "Protocol", "N*", "SSF"],
                    "rows": rows,
                }
            ],
        )
        self.report.add_section(section)
        return self

    def add_figures_section(
        self,
        figure_paths: list[str],
        title: str = "Figures",
    ) -> ReportBuilder:
        """Add figures section."""
        section = ReportSection(
            title=title,
            figures=figure_paths,
        )
        self.report.add_section(section)
        return self

    def add_conclusions_section(
        self,
        conclusions: str,
    ) -> ReportBuilder:
        """Add conclusions section."""
        section = ReportSection(
            title="Conclusions",
            content=conclusions,
        )
        self.report.add_section(section)
        return self

    def build(self) -> BenchmarkReport:
        """Build and return the report."""
        return self.report
