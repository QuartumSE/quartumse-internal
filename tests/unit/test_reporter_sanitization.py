from __future__ import annotations

from experiments.pipeline.metadata_schema import (
    CalibrationBudget,
    ExperimentMetadata,
    PhaseOneBudget,
)
from experiments.pipeline.reporter import generate_report


def _metadata() -> ExperimentMetadata:
    return ExperimentMetadata(
        experiment="Sanitization Check",
        context="Ensure secrets and absolute paths are removed.",
        aims=["Keep reports hygienic"],
        success_criteria=["No secrets leaked"],
        methods=["Unit testing"],
        budget=PhaseOneBudget(
            total_shots=1024,
            calibration=CalibrationBudget(shots_per_state=64, total=256),
            v0_shadow_size=512,
            v1_shadow_size=512,
        ),
        device="ibm_fake_provider",
        discussion_template="",
    )


def test_reporter_redacts_environment_and_paths(tmp_path, monkeypatch) -> None:
    secret_value = "super-secret-token"
    monkeypatch.setenv("PIPELINE_API_TOKEN", secret_value)

    metadata = _metadata()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")

    artifacts = {
        "manifest_v1": manifest_path,
        "auth_header": f"Bearer {secret_value}",
    }

    analysis = {}
    verification = {
        "manifest_path": str(manifest_path),
        "auth": secret_value,
    }

    output_dir = tmp_path / "reports"
    html_path = generate_report(
        metadata, artifacts, analysis, verification, output_dir / "report.html"
    )

    html = html_path.read_text(encoding="utf-8")

    assert secret_value not in html
    assert str(manifest_path) not in html
    assert "manifest.json" in html
