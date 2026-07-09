"""Pydantic schemas for the reports endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class GenerateReportRequestSchema(BaseModel):
    calculation_run_id: UUID


class ReportResponseSchema(BaseModel):
    id: UUID
    calculation_run_id: UUID
    generated_at: datetime
