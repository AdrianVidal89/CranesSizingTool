"""Pydantic schemas for the projects endpoints.

A project is created in one step with its crane movements (business flow:
the user first describes the crane — how many hoists and travel movements
it has and what each is called — before any calculation).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

MovementKind = Literal["hoist", "travel"]

MAX_MOVEMENTS_PER_KIND = 3


class MovementCreateSchema(BaseModel):
    kind: MovementKind
    name: str = Field(..., min_length=1, max_length=200)


class ProjectCreateRequestSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    crane_configuration_name: str = Field(
        "Main configuration", min_length=1, max_length=200
    )
    movements: tuple[MovementCreateSchema, ...] = Field(
        default=(), max_length=2 * MAX_MOVEMENTS_PER_KIND
    )

    @model_validator(mode="after")
    def _check_movement_counts(self) -> "ProjectCreateRequestSchema":
        for kind in ("hoist", "travel"):
            count = sum(1 for m in self.movements if m.kind == kind)
            if count > MAX_MOVEMENTS_PER_KIND:
                raise ValueError(
                    f"At most {MAX_MOVEMENTS_PER_KIND} {kind} movements per crane"
                )
        return self


class MovementResponseSchema(BaseModel):
    id: UUID
    kind: str
    name: str


class ProjectResponseSchema(BaseModel):
    id: UUID
    name: str
    movements: tuple[MovementResponseSchema, ...] = ()
    created_at: datetime
    updated_at: datetime
