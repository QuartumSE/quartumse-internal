"""Unit tests for the experiment metadata schema."""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from experiments.pipeline.metadata_schema import ExperimentMetadata


def _load_example() -> ExperimentMetadata:
    example_path = (
        Path(__file__).parents[2]
        / "experiments"
        / "shadows"
        / "examples"
        / "extended_ghz"
        / "experiment_metadata.yaml"
    )
    with example_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return ExperimentMetadata.model_validate(data)


def test_example_yaml_validates() -> None:
    """The provided example metadata should validate without errors."""

    metadata = _load_example()

    assert metadata.budget.total_shots == 5000
    assert metadata.budget.calibration.shots_per_state == 256
    assert metadata.budget.v1_shadow_size == 904


def test_unknown_key_raises_validation_error() -> None:
    """Unexpected keys should raise validation errors."""

    with pytest.raises(ValidationError):
        ExperimentMetadata.model_validate(
            {
                "experiment": "GHZ-4 Phase-1 Benchmark",
                "context": "Test context",
                "aims": ["Aim"],
                "success_criteria": ["Success"],
                "methods": ["Method"],
                "budget": {
                    "total_shots": 100,
                    "calibration": {"shots_per_state": 1, "total": 2},
                    "v0_shadow_size": 100,
                    "v1_shadow_size": 10,
                },
                "device": "device",
                "discussion_template": "Discuss",
                "extra_field": "not allowed",
            }
        )
