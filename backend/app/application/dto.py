"""Framework-agnostic DTOs returned by repository ports.

Plain dataclasses so application/ never needs to import SQLAlchemy models
directly — only infrastructure/db/repositories.py does that translation
(CLAUDE.md: domain has zero external dependencies; this keeps application/
decoupled from the ORM too).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class UserDTO:
    id: UUID
    email: str
    password_hash: str
    created_at: datetime


@dataclass(frozen=True)
class SessionDTO:
    id: UUID
    user_id: UUID
    token_hash: str
    csrf_token: str
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class ProjectDTO:
    id: UUID
    owner_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class CraneConfigurationDTO:
    id: UUID
    project_id: UUID
    name: str
    created_at: datetime


@dataclass(frozen=True)
class MovementDTO:
    id: UUID
    crane_configuration_id: UUID
    kind: str
    name: str
    created_at: datetime


@dataclass(frozen=True)
class CalculationRunDTO:
    id: UUID
    movement_id: UUID
    owner_id: UUID
    input_snapshot: dict
    result_snapshot: dict
    formula_ids: list[str]
    created_at: datetime


@dataclass(frozen=True)
class ReportDTO:
    id: UUID
    calculation_run_id: UUID
    owner_id: UUID
    pdf_data: bytes
    generated_at: datetime
