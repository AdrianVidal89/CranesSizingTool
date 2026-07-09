"""Pydantic schemas for the projects endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreateRequestSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class ProjectResponseSchema(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
