"""Smoke tests for the full pipeline CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


def _write_metadata(path: Path) -> None:
    metadata = {
        "experiment": "GHZ-2 Smoke Test",
        "context": "Automated smoke validation for the pipeline CLI.",
        "aims": ["Exercise execution, verification, analysis, and reporting."],
        "success_criteria": [
            "SSR average should be above 0.3",
            "CI coverage should exceed 40%",
        ],
        "methods": ["Execute the Aer simulator baseline and shadows runs."],
        "budget": {
            "total_shots": 64,
            "calibration": {"shots_per_state": 4, "total": 16},
            "v0_shadow_size": 64,
            "v1_shadow_size": 48,
        },
        "device": "aer_simulator",
        "discussion_template": "MAE {mae} CI {ci_coverage} SSR {ssr_average}",
        "targets": {"ssr_average": 0.3, "ci_coverage": 0.4},
        "ground_truth": {
            "observables": {
                "ZI": {"expectation": 0.0},
                "IZ": {"expectation": 0.0},
                "ZZ": {"expectation": 1.0},
            },
            "stabilizers": ["ZZ"],
        },
    }
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(metadata, handle)


@pytest.mark.smoke
def test_run_full_pipeline_cli(tmp_path: Path) -> None:
    metadata_path = tmp_path / "metadata.yaml"
    _write_metadata(metadata_path)

    output_dir = tmp_path / "artifacts"

    command = [
        sys.executable,
        "-m",
        "experiments.pipeline.run_full_pipeline",
        "--metadata",
        str(metadata_path),
        "--backend",
        "aer_simulator",
        "--output",
        str(output_dir),
    ]

    completed = subprocess.run(command, check=False, capture_output=True, text=True)

    if completed.returncode != 0:
        pytest.fail(
            f"Pipeline CLI exited with {completed.returncode}:\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )

    result_hash_files = list(output_dir.glob("result_hash.txt"))
    assert result_hash_files, "Execution did not produce a result hash file"
    digest = result_hash_files[0].read_text(encoding="utf-8").strip()

    analysis_path = output_dir / f"analysis_{digest}.json"
    report_path = output_dir / f"report_{digest}.html"

    assert analysis_path.exists(), "Analysis JSON was not generated"
    assert report_path.exists(), "Report HTML was not generated"

    with analysis_path.open("r", encoding="utf-8") as handle:
        analysis = json.load(handle)

    summary = analysis.get("summary_metrics", {})
    assert "ssr_average" in summary
    assert "ci_coverage" in summary
    targets = analysis.get("targets", {})
    assert targets.get("ssr_average") == pytest.approx(0.3)
    assert targets.get("ci_coverage") == pytest.approx(0.4)
