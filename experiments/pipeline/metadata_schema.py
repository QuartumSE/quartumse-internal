"""Pydantic models for experiment metadata definitions."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class CalibrationBudget(BaseModel):
    """Resource allocation for calibration routines."""

    shots_per_state: int
    total: int

    model_config = ConfigDict(extra="forbid")


class PhaseOneBudget(BaseModel):
    """Budget information for the Phase-1 execution of an experiment."""

    total_shots: int
    calibration: CalibrationBudget
    v0_shadow_size: int
    v1_shadow_size: int

    model_config = ConfigDict(extra="forbid")


class ExperimentMetadata(BaseModel):
    """Schema describing experiment metadata for the pipeline."""

    experiment: str
    context: str
    aims: List[str]
    success_criteria: List[str]
    methods: List[str]
    budget: PhaseOneBudget
    device: str
    discussion_template: str
    targets: Optional[Dict[str, float]] = None
    ground_truth: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="forbid")
