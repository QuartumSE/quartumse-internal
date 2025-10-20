"""
Report generation for quantum experiments.

Generates human-readable HTML and PDF reports from provenance manifests.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from jinja2 import Template

from quartumse.reporting.manifest import ProvenanceManifest
from quartumse.reporting.shot_data import ShotDataDiagnostics, ShotDataWriter


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>QuartumSE Experiment Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 1200px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .section {
            background: white;
            padding: 25px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 { margin: 0; font-size: 32px; }
        h2 { color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
        h3 { color: #555; }
        .metadata { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .metric { background: #f8f9fa; padding: 15px; border-radius: 5px; }
        .metric-label { font-size: 12px; color: #666; text-transform: uppercase; }
        .metric-value { font-size: 24px; font-weight: bold; color: #667eea; margin-top: 5px; }
        .tag { background: #667eea; color: white; padding: 4px 12px; border-radius: 12px;
               display: inline-block; margin: 4px; font-size: 12px; }
        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: 'Courier New', monospace; }
        .footer { text-align: center; color: #999; margin-top: 40px; font-size: 12px; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f8f9fa; font-weight: 600; }
    </style>
</head>
<body>
    <div class="header">
        <h1>QuartumSE Experiment Report</h1>
        <p>{{ manifest.experiment_name or manifest.experiment_id }}</p>
        <p style="opacity: 0.9; font-size: 14px;">Generated: {{ now }}</p>
    </div>

    <div class="section">
        <h2>Summary</h2>
        <div class="metadata">
            <div class="metric">
                <div class="metric-label">Backend</div>
                <div class="metric-value">{{ manifest.backend.backend_name }}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Total Shots</div>
                <div class="metric-value">{{ "{:,}".format(manifest.resource_usage.total_shots) }}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Execution Time</div>
                <div class="metric-value">{{ "%.2f"|format(manifest.resource_usage.execution_time_seconds) }}s</div>
            </div>
            <div class="metric">
                <div class="metric-label">QuartumSE Version</div>
                <div class="metric-value" style="font-size: 18px;">{{ manifest.quartumse_version }}</div>
            </div>
        </div>
        {% if manifest.tags %}
        <div style="margin-top: 20px;">
            {% for tag in manifest.tags %}
            <span class="tag">{{ tag }}</span>
            {% endfor %}
        </div>
        {% endif %}
    </div>

    <div class="section">
        <h2>Circuit Details</h2>
        <table>
            <tr><th>Property</th><th>Value</th></tr>
            <tr><td>Qubits</td><td>{{ manifest.circuit.num_qubits }}</td></tr>
            <tr><td>Depth</td><td>{{ manifest.circuit.depth }}</td></tr>
            <tr><td>Circuit Hash</td><td><code>{{ manifest.circuit.circuit_hash }}</code></td></tr>
        </table>
        <h3>Gate Composition</h3>
        <table>
            <tr><th>Gate</th><th>Count</th></tr>
            {% for gate, count in manifest.circuit.gate_counts.items() %}
            <tr><td><code>{{ gate }}</code></td><td>{{ count }}</td></tr>
            {% endfor %}
        </table>
    </div>

    <div class="section">
        <h2>Error Mitigation</h2>
        <p><strong>Techniques Applied:</strong>
        {% if manifest.mitigation.techniques %}
            {% for tech in manifest.mitigation.techniques %}
            <code>{{ tech }}</code>{% if not loop.last %}, {% endif %}
            {% endfor %}
        {% else %}
            <em>None</em>
        {% endif %}
        </p>
        {% if manifest.mitigation.parameters %}
        <h3>Parameters</h3>
        <table>
            <tr><th>Parameter</th><th>Value</th></tr>
            {% for key, value in manifest.mitigation.parameters.items() %}
            <tr><td>{{ key }}</td><td>{{ value }}</td></tr>
            {% endfor %}
        </table>
        {% endif %}
    </div>

    {% if manifest.shadows %}
    <div class="section">
        <h2>Classical Shadows</h2>
        <table>
            <tr><th>Property</th><th>Value</th></tr>
            <tr><td>Version</td><td><code>{{ manifest.shadows.version }}</code></td></tr>
            <tr><td>Shadow Size</td><td>{{ manifest.shadows.shadow_size }}</td></tr>
            <tr><td>Ensemble</td><td>{{ manifest.shadows.measurement_ensemble }}</td></tr>
            <tr><td>Noise-Aware</td><td>{{ "Yes" if manifest.shadows.inverse_channel_applied else "No" }}</td></tr>
            <tr><td>Adaptive</td><td>{{ "Yes" if manifest.shadows.adaptive else "No" }}</td></tr>
        </table>
    </div>
    {% endif %}

    <div class="section">
        <h2>Results</h2>
        <table>
            <tr><th>Observable</th><th>Value</th></tr>
            {% for key, value in manifest.results_summary.items() %}
            <tr><td>{{ key }}</td><td>{{ value }}</td></tr>
            {% endfor %}
        </table>
    </div>

    {% if shot_diagnostics %}
    <div class="section">
        <h2>Shot Diagnostics</h2>
        <p><strong>Total Shots:</strong> {{ shot_diagnostics.total_shots }}</p>
        <h3>Measurement Basis Distribution</h3>
        <table>
            <tr><th>Basis String</th><th>Count</th></tr>
            {% for basis, count in shot_diagnostics.measurement_basis_distribution.items() %}
            <tr><td>{{ basis }}</td><td>{{ count }}</td></tr>
            {% endfor %}
        </table>
        <h3>Top Bitstrings</h3>
        <table>
            <tr><th>Bitstring</th><th>Count</th></tr>
            {% for bitstring, count in shot_diagnostics.bitstring_histogram.items() %}
            <tr><td>{{ bitstring }}</td><td>{{ count }}</td></tr>
            {% endfor %}
        </table>
        <h3>Marginal Probabilities</h3>
        <table>
            <tr><th>Qubit</th><th>P(0)</th><th>P(1)</th></tr>
            {% for qubit, probs in shot_diagnostics.qubit_marginals.items() %}
            <tr><td>{{ qubit }}</td><td>{{ "{:.3f}".format(probs['0']) }}</td><td>{{ "{:.3f}".format(probs['1']) }}</td></tr>
            {% endfor %}
        </table>
    </div>
    {% endif %}

    <div class="section">
        <h2>Backend Calibration Snapshot</h2>
        <p><strong>Timestamp:</strong> {{ manifest.backend.calibration_timestamp }}</p>
        {% if manifest.backend.t1_times %}
        <h3>T1 Times (μs)</h3>
        <p>{{ manifest.backend.t1_times }}</p>
        {% endif %}
        {% if manifest.backend.readout_errors %}
        <h3>Readout Errors</h3>
        <p>{{ manifest.backend.readout_errors }}</p>
        {% endif %}
    </div>

    <div class="section">
        <h2>Reproducibility</h2>
        <table>
            <tr><th>Component</th><th>Version</th></tr>
            <tr><td>QuartumSE</td><td><code>{{ manifest.quartumse_version }}</code></td></tr>
            <tr><td>Qiskit</td><td><code>{{ manifest.qiskit_version }}</code></td></tr>
            <tr><td>Python</td><td><code>{{ manifest.python_version }}</code></td></tr>
        </table>
        <p><strong>Random Seed:</strong> <code>{{ manifest.random_seed or "Not set" }}</code></p>
        <p><strong>Shot Data:</strong> <code>{{ manifest.shot_data_path }}</code></p>
        <p><strong>Manifest ID:</strong> <code>{{ manifest.experiment_id }}</code></p>
    </div>

    <div class="footer">
        <p>Generated with QuartumSE v{{ manifest.quartumse_version }}</p>
        <p>🤖 Open-source quantum measurement optimization</p>
    </div>
</body>
</html>
"""


class Report:
    """Container for experiment report data."""

    def __init__(
        self,
        manifest: ProvenanceManifest,
        plots: Optional[Dict[str, Any]] = None,
        shot_diagnostics: Optional[ShotDataDiagnostics] = None,
    ):
        self.manifest = manifest
        self.plots = plots or {}
        self.shot_diagnostics = shot_diagnostics

    def to_html(self, output_path: Optional[Union[str, Path]] = None) -> str:
        """Generate HTML report."""
        template = Template(HTML_TEMPLATE)
        html = template.render(
            manifest=self.manifest.schema,
            now=datetime.utcnow().isoformat(),
            shot_diagnostics=self.shot_diagnostics.to_dict() if self.shot_diagnostics else None,
        )

        if output_path:
            Path(output_path).write_text(html)

        return html

    def to_pdf(self, output_path: Union[str, Path]) -> None:
        """Generate PDF report (requires weasyprint)."""
        try:
            from weasyprint import HTML

            html_content = self.to_html()
            HTML(string=html_content).write_pdf(output_path)
        except ImportError:
            raise ImportError(
                "PDF generation requires weasyprint. Install with: pip install weasyprint"
            )


class ReportGenerator:
    """Utility class for generating reports from manifests."""

    @staticmethod
    def from_manifest_file(manifest_path: Union[str, Path]) -> Report:
        """Create a report from a manifest JSON file."""
        manifest = ProvenanceManifest.from_json(manifest_path)

        shot_diagnostics = None
        try:
            shot_diagnostics = ShotDataWriter.summarize_parquet(manifest.schema.shot_data_path)
        except FileNotFoundError:
            shot_diagnostics = None

        return Report(manifest, shot_diagnostics=shot_diagnostics)

    @staticmethod
    def batch_generate(
        manifest_paths: List[Union[str, Path]], output_dir: Union[str, Path]
    ) -> None:
        """Generate reports for multiple manifests."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for manifest_path in manifest_paths:
            manifest = ProvenanceManifest.from_json(manifest_path)
            report = Report(manifest)

            output_name = Path(manifest_path).stem + "_report.html"
            report.to_html(output_dir / output_name)
