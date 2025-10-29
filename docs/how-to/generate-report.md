# Generate Experiment Reports

QuartumSE can generate self-contained HTML reports from saved manifests, providing human-readable experiment summaries with full provenance details.

## Overview

**Report contents:**
- Experiment metadata (ID, timestamp, versions)
- Circuit visualization and fingerprint
- Backend calibration snapshot
- Observable estimates with confidence intervals
- Shot data diagnostics (basis distribution, bitstring histogram)
- Mitigation configuration (MEM, ZNE settings)
- Resource usage (shots, execution time)

**Formats:**
- **HTML** (default) - Self-contained, viewable in any browser
- **PDF** (future) - Requires `weasyprint` (not yet implemented)

---

## Quick Start

### Generate HTML Report (CLI)

**Unix/macOS:**
```bash
quartumse report data/manifests/a3f2b1c4-5678-90ab-cdef-1234567890ab.json \
  --output reports/experiment_report.html
```

**Windows:**
```powershell
quartumse report data/manifests/a3f2b1c4-5678-90ab-cdef-1234567890ab.json `
  --output reports/experiment_report.html
```

**Output:**
```
Generating report from data/manifests/a3f2b1c4-5678-90ab-cdef-1234567890ab.json...
Report saved to reports/experiment_report.html
```

**Open in browser:**

**Unix/macOS:**
```bash
open reports/experiment_report.html
```

**Windows:**
```powershell
Start-Process reports/experiment_report.html
```

**Linux:**
```bash
xdg-open reports/experiment_report.html
```

---

## Using Python API

### Basic Report Generation

```python
from quartumse.reporting import ReportGenerator

# Load manifest and generate report
report = ReportGenerator.from_manifest_file(
    "data/manifests/a3f2b1c4-5678-90ab-cdef-1234567890ab.json"
)

# Save as HTML
report.to_html("reports/experiment_report.html")

print("Report generated successfully!")
```

### Customizing Report Content

```python
from quartumse.reporting import ReportGenerator
from pathlib import Path

manifest_path = "data/manifests/a3f2b1c4-5678-90ab-cdef-1234567890ab.json"

# Create report with custom title
report = ReportGenerator.from_manifest_file(manifest_path)
report.title = "GHZ State Validation - Phase 1"
report.description = "Classical shadows v0 baseline on 3-qubit GHZ state"

# Add custom metadata
report.add_metadata("Experiment Group", "Phase 1 Validation")
report.add_metadata("Researcher", "QuartumSE Team")
report.add_metadata("Status", "PASSED ✓")

# Generate output
output_path = Path("reports/ghz_phase1_report.html")
output_path.parent.mkdir(parents=True, exist_ok=True)
report.to_html(str(output_path))

print(f"Custom report saved: {output_path}")
```

---

## Batch Report Generation

Generate reports for all experiments in a directory:

**Unix/macOS:**
```bash
for manifest in data/manifests/*.json; do
  base=$(basename "$manifest" .json)
  quartumse report "$manifest" --output "reports/${base}_report.html"
  echo "Generated: reports/${base}_report.html"
done
```

**Windows (PowerShell):**
```powershell
Get-ChildItem data/manifests/*.json | ForEach-Object {
  $base = $_.BaseName
  quartumse report $_.FullName --output "reports/${base}_report.html"
  Write-Host "Generated: reports/${base}_report.html"
}
```

**Python script:**
```python
from pathlib import Path
from quartumse.reporting import ReportGenerator

manifest_dir = Path("data/manifests")
report_dir = Path("reports")
report_dir.mkdir(parents=True, exist_ok=True)

for manifest_path in sorted(manifest_dir.glob("*.json")):
    try:
        report = ReportGenerator.from_manifest_file(str(manifest_path))

        output_name = f"{manifest_path.stem}_report.html"
        output_path = report_dir / output_name

        report.to_html(str(output_path))
        print(f"✓ Generated: {output_name}")

    except Exception as e:
        print(f"✗ Failed: {manifest_path.name} - {e}")

print(f"\nTotal reports generated: {len(list(report_dir.glob('*.html')))}")
```

---

## Report Structure

### Section 1: Experiment Overview

- **Experiment ID**: Unique UUID for traceability
- **Created**: ISO timestamp
- **Backend**: Device name and qubit count
- **Shadow Version**: v0 (baseline), v1 (noise-aware), etc.
- **Shadow Size**: Number of random measurements
- **Execution Time**: Wall-clock time for quantum execution

### Section 2: Circuit Details

- **Num Qubits**: Circuit width
- **Depth**: Gate depth
- **Gate Counts**: Breakdown by gate type (H, CNOT, etc.)
- **Circuit Hash**: SHA-256 fingerprint for reproducibility
- **Circuit Visualization**: (if available)

### Section 3: Observable Results

Table with columns:
- **Observable**: Pauli string (e.g., `ZII`, `ZZZ`)
- **Expectation Value**: Estimated mean
- **Variance**: Estimation variance
- **95% CI**: Confidence interval bounds
- **CI Width**: Interval width (precision measure)

### Section 4: Shot Data Diagnostics

**Measurement Basis Distribution:**
- Histogram showing X/Y/Z measurement frequencies per qubit
- Should be uniform (~33% each) for random Clifford shadows

**Top Bitstrings:**
- Most frequent measurement outcomes
- Useful for debugging unexpected distributions

**Qubit Marginals:**
- Per-qubit P(|0⟩) probabilities
- Should be ~0.5 for maximally entangled states

### Section 5: Mitigation Configuration

- **Techniques**: MEM, ZNE, etc.
- **MEM Confusion Matrix Path**: (if applicable)
- **MEM Shots per State**: Calibration budget
- **Qubits Calibrated**: Indices of calibrated qubits

### Section 6: Backend Calibration

- **Calibration Timestamp**: When device properties were captured
- **T1 Times**: (if available) Decay times per qubit
- **T2 Times**: (if available) Dephasing times per qubit
- **Readout Errors**: (if available) Measurement error rates
- **Properties Hash**: SHA-256 of full calibration JSON

### Section 7: Provenance

- **QuartumSE Version**: Package version used
- **Qiskit Version**: Qiskit version used
- **Python Version**: Python interpreter version
- **Random Seed**: (if set) For reproducibility
- **Tags**: User-defined searchable tags

---

## Report Output Locations

### Default Behavior

When using the experiment API (`estimator.estimate(save_manifest=True)`), no report is auto-generated. Use the CLI or Python API to generate reports from saved manifests. If you ran experiments with a custom `--data-dir`, substitute that path for the default `data/` directory referenced below.

### Recommended Structure

```
quartumse/
├── data/
│   ├── manifests/           # JSON manifests
│   │   ├── a3f2b1c4-....json
│   │   └── b5e8f9d2-....json
│   ├── shots/               # Parquet shot data
│   │   ├── a3f2b1c4-....parquet
│   │   └── b5e8f9d2-....parquet
│   └── mem/                 # MEM confusion matrices
│       ├── a3f2b1c4-....npz
│       └── b5e8f9d2-....npz
└── reports/                 # HTML reports (gitignored)
    ├── a3f2b1c4-...._report.html
    └── b5e8f9d2-...._report.html
```

---

## Advanced: Programmatic Report Analysis

Extract key metrics from reports for comparison:

```python
import json
from pathlib import Path
import pandas as pd

def extract_metrics_from_manifest(manifest_path):
    """Extract key metrics from manifest JSON."""
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    metrics = {
        'experiment_id': manifest['experiment_id'],
        'backend': manifest['backend']['backend_name'],
        'shadow_size': manifest['shadows']['shadow_size'],
        'shadow_version': manifest['shadows']['version'],
        'num_qubits': manifest['circuit']['num_qubits'],
        'execution_time': manifest.get('resource_usage', {}).get('quantum_execution_seconds', None),
    }

    # Extract observable results
    for obs_str, obs_data in manifest.get('results_summary', {}).items():
        metrics[f'obs_{obs_str}_expectation'] = obs_data.get('expectation_value')
        metrics[f'obs_{obs_str}_ci_width'] = obs_data.get('ci_width')

    return metrics

# Process all manifests
manifest_dir = Path("data/manifests")
all_metrics = [extract_metrics_from_manifest(p) for p in manifest_dir.glob("*.json")]

# Convert to DataFrame for analysis
df = pd.DataFrame(all_metrics)

# Compare by backend
print("\nMetrics by Backend:")
print(df.groupby('backend')['shadow_size'].agg(['mean', 'min', 'max', 'count']))

# Compare by shadow version
print("\nMetrics by Shadow Version:")
print(df.groupby('shadow_version')['execution_time'].agg(['mean', 'median', 'std']))
```

---

## PDF Reports (Future)

PDF generation is planned for Phase 2. It will require the `weasyprint` package:

**Installation (when implemented):**
```bash
pip install quartumse[reporting]
```

**Usage (planned API):**
```python
from quartumse.reporting import ReportGenerator

report = ReportGenerator.from_manifest_file("data/manifests/experiment.json")
report.to_pdf("reports/experiment_report.pdf")  # Not yet implemented
```

**Current workaround:**
1. Generate HTML report
2. Open in browser
3. Print to PDF using browser's print dialog

---

## Troubleshooting

**"Manifest file not found"**
- Check path is correct (absolute or relative)
- Verify experiment completed and saved manifest
- Use `ls data/manifests/` to list available manifests

**"cannot import name 'generate_html_report'"**
- Use `ReportGenerator` class instead (new API)
- Old function name removed in favor of class-based API
- Update code: `ReportGenerator.from_manifest_file(path).to_html(output)`

**"Shot data file not found"**
- Report includes shot diagnostics if shot data exists
- Gracefully degrades if shot data missing (shows warning)
- Check `manifest['shot_data_path']` points to valid Parquet file

**"Template not found"**
- Report templates bundled with package
- If error persists, reinstall: `pip install --force-reinstall quartumse`

**"Report HTML not rendering properly"**
- Open in modern browser (Chrome, Firefox, Safari, Edge)
- Check for JavaScript errors in browser console
- Verify HTML file wasn't corrupted during generation

**"Report generation slow (>5 seconds)"**
- Check shot data file size (should be <10MB for typical experiments)
- Verify no network I/O (all files should be local)
- Report generation should complete in <1 second normally

---

## Related

- [Run S-T01 GHZ](run-st01-ghz.md) - Generate manifests worth reporting
- [Replay from Manifest](replay-from-manifest.md) - Re-analyze before reporting
- [Manifest Schema](../explanation/manifest-schema.md) - Full manifest specification
