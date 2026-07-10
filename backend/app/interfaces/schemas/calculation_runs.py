"""Pydantic schemas for the calculation-runs (save/list/get) endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.interfaces.schemas.validate_candidate import ValidateCandidateRequestSchema


class SaveCalculationRunRequestSchema(ValidateCandidateRequestSchema):
    project_id: UUID | None = Field(
        None, description="Existing project to attach this run to"
    )
    new_project_name: str | None = Field(
        None, min_length=1, max_length=200, description="Create a new project with this name"
    )
    crane_configuration_name: str = Field(..., min_length=1, max_length=200)
    movement_kind: Literal["travel", "hoist"] = "travel"
    movement_name: str = Field(..., min_length=1, max_length=200)


class CalculationRunSummarySchema(BaseModel):
    id: UUID
    formula_ids: list[str]
    created_at: datetime


class CalculationRunDetailSchema(BaseModel):
    id: UUID
    formula_ids: list[str]
    input_snapshot: dict
    result_snapshot: dict
    created_at: datetime
