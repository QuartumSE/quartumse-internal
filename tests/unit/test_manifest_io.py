"""Tests for manifest IO helper utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from quartumse.reporting.manifest_io import (
    extract_artifact_paths,
    extract_observable_table,
    load_manifest,
)


def test_load_manifest_reads_json(tmp_path: Path) -> None:
    payload = {"results_summary": {"Z": {"expectation_value": 0.5}}}
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_manifest(manifest_path)

    assert loaded == payload


def test_extract_observable_table_handles_missing_summary() -> None:
    manifest = {"experiment_id": "exp-123"}

    result = extract_observable_table(manifest)

    assert result == {}


def test_extract_observable_table_optional_fields() -> None:
    manifest = {
        "results_summary": {
            "1.0*ZZ": {
                "expectation_value": 0.25,
                # Variance intentionally omitted
                "confidence_interval": {"lower": 0.1, "upper": 0.4},
            }
        }
    }

    table = extract_observable_table(manifest)

    assert table == {
        "1.0*ZZ": {
            "expectation": pytest.approx(0.25),
            "variance": None,
            "ci_lower": pytest.approx(0.1),
            "ci_upper": pytest.approx(0.4),
        }
    }


def test_extract_artifact_paths_handles_missing_keys() -> None:
    manifest = {"experiment_id": "exp-456"}

    paths = extract_artifact_paths(manifest)

    assert paths["shot_data_path"] is None
    assert paths["confusion_matrix_path"] is None
    assert paths["noise_model_path"] is None


def test_extract_artifact_paths_normalizes_values(monkeypatch: pytest.MonkeyPatch) -> None:
    home = Path("/tmp/test-home").resolve()
    monkeypatch.setenv("HOME", str(home))

    manifest = {
        "shot_data_path": "./data/../data/shots.parquet",
        "mitigation": {"confusion_matrix_path": "~/artifacts/confusion.npy"},
        "shadows": {"noise_model_path": "s3://bucket/model.json"},
        "results_summary": {
            "metadata": {"analysis_path": "results/figures/../plots.png"}
        },
    }

    paths = extract_artifact_paths(manifest)

    assert paths["shot_data_path"] == "data/shots.parquet"
    assert paths["confusion_matrix_path"] == str(home / "artifacts" / "confusion.npy")
    assert paths["noise_model_path"] == "s3://bucket/model.json"
    assert paths["analysis_path"] == "results/plots.png"

