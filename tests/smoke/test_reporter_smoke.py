from __future__ import annotations

from pathlib import Path

from experiments.pipeline.metadata_schema import (
    CalibrationBudget,
    ExperimentMetadata,
    PhaseOneBudget,
)
from experiments.pipeline.reporter import generate_report


def _example_metadata() -> ExperimentMetadata:
    return ExperimentMetadata(
        experiment="Example Benchmark",
        context="Synthetic context for smoke testing the reporter pipeline.",
        aims=["Validate reporting stack", "Demonstrate formatting"],
        success_criteria=["SSR above 1.0", "CI coverage above 95%"],
        methods=["Baseline Pauli estimation", "Shadow estimation"],
        budget=PhaseOneBudget(
            total_shots=4096,
            calibration=CalibrationBudget(shots_per_state=128, total=1024),
            v0_shadow_size=2048,
            v1_shadow_size=1024,
        ),
        device="ibm_fake_provider",
        discussion_template="Observed MAE {mae:.3f} with CI coverage {ci_coverage:.2%} and SSR {ssr_average:.2f}.",
    )


def test_generate_report_smoke(tmp_path: Path) -> None:
    metadata = _example_metadata()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")

    artifacts = {
        "manifest_v1": manifest_path,
        "result_hash": "deadbeef" * 8,
    }

    analysis = {
        "summary_metrics": {
            "mae": 0.0123,
            "ci_coverage": 0.97,
            "ssr_average": 1.2,
        },
        "per_observable": {
            "v1": {
                "ZIII": {
                    "baseline": {"expectation": 0.1},
                    "approach": {"expectation": 0.11},
                    "ssr": 1.4,
                    "in_ci": True,
                    "variance_ratio": 1.2,
                }
            }
        },
        "plots_data": {
            "observables": ["ZIII"],
            "baseline_errors": [0.1],
            "v0_errors": [0.08],
            "v1_errors": [0.05],
        },
        "references": ["QuartumSE Team (2024). Reporter pipeline specification."],
    }

    verification = {
        "manifest_path": str(manifest_path),
        "manifest_exists": True,
        "manifest_valid": True,
        "shot_data_exists": True,
        "mem_confusion_matrix_exists": True,
        "replay_matches": True,
        "errors": [],
    }

    output_path = tmp_path / "report.html"
    html_path = generate_report(metadata, artifacts, analysis, verification, output_path)

    assert html_path.exists()
    html = html_path.read_text(encoding="utf-8")

    # Sections rendered
    assert "Executive Summary" in html
    assert "Context and Literature" in html
    assert "Reproducibility Appendix" in html
    assert "quartumse replay --manifest" in html
    assert str(manifest_path) not in html
    assert "manifest.json" in html

    # Status tiles
    assert 'data-metric="ci_coverage"' in html
    assert 'data-metric="ssr_average"' in html

    # Discussion template formatted values
    assert "MAE 0.012" in html
    assert "CI coverage 97.00%" in html
    assert "SSR 1.20" in html

    # Figures saved with relative paths referenced in HTML
    figures_dir = tmp_path / "figures"
    assert (figures_dir / "observable_errors.png").exists()
    assert "figures/observable_errors.png" in html

    # HTML should be generated regardless of PDF support
    assert html_path.exists()
