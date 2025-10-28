from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

from experiments.pipeline.executor import execute_experiment
from experiments.pipeline.metadata_schema import ExperimentMetadata


@pytest.fixture
def example_metadata() -> ExperimentMetadata:
    metadata_path = (
        Path(__file__).resolve().parents[2]
        / "experiments"
        / "shadows"
        / "examples"
        / "extended_ghz"
        / "experiment_metadata.yaml"
    )
    with metadata_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)

    metadata = ExperimentMetadata.model_validate(payload)
    return metadata.model_copy(update={"device": "aer_simulator", "num_qubits": 4})


def test_execute_experiment_aer(tmp_path: Path, example_metadata: ExperimentMetadata) -> None:
    outputs = execute_experiment(example_metadata, tmp_path, backend="aer_simulator")

    for key in ("manifest_v0", "manifest_v1", "manifest_baseline", "result_hash"):
        assert key in outputs
        assert outputs[key].exists()

    baseline_manifest_path = outputs["manifest_baseline"]
    with baseline_manifest_path.open("r", encoding="utf-8") as handle:
        baseline_manifest = json.load(handle)

    baseline_shot_path = Path(baseline_manifest["shot_data_path"])
    assert baseline_shot_path.exists()
    baseline_df = pd.read_parquet(baseline_shot_path, engine="pyarrow")
    assert baseline_df["shots"].sum() == example_metadata.budget.total_shots
    assert len(baseline_manifest.get("shot_data_checksum", "")) == 64
    assert (
        baseline_manifest["shot_data_checksum"]
        == hashlib.sha256(baseline_shot_path.read_bytes()).hexdigest()
    )

    assert baseline_manifest["resource_usage"]["total_shots"] == example_metadata.budget.total_shots
    assert baseline_manifest["metadata"]["approach"] == "baseline_direct_pauli"

    manifest_v0_path = outputs["manifest_v0"]
    with manifest_v0_path.open("r", encoding="utf-8") as handle:
        manifest_v0 = json.load(handle)
    assert manifest_v0["resource_usage"]["total_shots"] == example_metadata.budget.v0_shadow_size
    assert len(manifest_v0.get("shot_data_checksum", "")) == 64
    v0_shot_path = Path(manifest_v0["shot_data_path"])
    assert (
        manifest_v0["shot_data_checksum"]
        == hashlib.sha256(v0_shot_path.read_bytes()).hexdigest()
    )

    manifest_v1_path = outputs["manifest_v1"]
    with manifest_v1_path.open("r", encoding="utf-8") as handle:
        manifest_v1 = json.load(handle)

    assert manifest_v1["resource_usage"]["total_shots"] == example_metadata.budget.v1_shadow_size
    confusion_path = Path(manifest_v1["mitigation"]["confusion_matrix_path"])
    assert confusion_path.exists()
    assert len(manifest_v1.get("shot_data_checksum", "")) == 64
    assert len(manifest_v1["mitigation"].get("confusion_matrix_checksum", "")) == 64
    assert (
        manifest_v1["mitigation"]["confusion_matrix_checksum"]
        == hashlib.sha256(confusion_path.read_bytes()).hexdigest()
    )
    v1_shot_path = Path(manifest_v1["shot_data_path"])
    assert (
        manifest_v1["shot_data_checksum"]
        == hashlib.sha256(v1_shot_path.read_bytes()).hexdigest()
    )
    assert manifest_v1["mitigation"]["parameters"]["mem_shots"] == example_metadata.budget.calibration.shots_per_state
    assert (
        manifest_v1["resource_usage"]["total_shots"]
        + example_metadata.budget.calibration.total
        == example_metadata.budget.total_shots
    )

    hash_value = outputs["result_hash"].read_text().strip()
    assert len(hash_value) == 64
    int(hash_value, 16)  # raises ValueError if not hex
