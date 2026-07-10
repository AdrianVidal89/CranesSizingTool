"""Repository ports (interfaces) the application layer depends on.

Implementations live in infrastructure/db/repositories.py. Every method
that touches user-owned data takes and filters by owner_id here, at the
port level, so no call site can accidentally skip the ownership check
(CLAUDE.md: isolation "sin excepción" — without exception).
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.application.dto import (
    CalculationRunDTO,
    CraneConfigurationDTO,
    MovementDTO,
    ProjectDTO,
    ReportDTO,
    SessionDTO,
    UserDTO,
)


class UserRepository(Protocol):
    def get_by_email(self, email: str) -> UserDTO | None: ...
    def get_by_id(self, user_id: UUID) -> UserDTO | None: ...
    def create(self, email: str, password_hash: str) -> UserDTO: ...


class SessionRepository(Protocol):
    def create(
        self, user_id: UUID, token_hash: str, csrf_token: str, expires_at: datetime
    ) -> SessionDTO: ...
    def get_by_token_hash(self, token_hash: str) -> SessionDTO | None: ...
    def delete(self, session_id: UUID) -> None: ...


class ProjectRepository(Protocol):
    def create(self, owner_id: UUID, name: str) -> ProjectDTO: ...
    def get_by_id(self, project_id: UUID, owner_id: UUID) -> ProjectDTO | None: ...
    def list_by_owner(self, owner_id: UUID) -> list[ProjectDTO]: ...


class CraneConfigurationRepository(Protocol):
    """Never queried directly by owner: crane configurations are only ever
    created transactionally right after the parent Project's ownership has
    already been verified (see application/save_calculation_run.py)."""

    def create(self, project_id: UUID, name: str) -> CraneConfigurationDTO: ...


class MovementRepository(Protocol):
    """Same note as CraneConfigurationRepository: created transactionally
    under an already-ownership-verified crane configuration."""

    def create(self, crane_configuration_id: UUID, kind: str, name: str) -> MovementDTO: ...


class CalculationRunRepository(Protocol):
    def create(
        self,
        movement_id: UUID,
        owner_id: UUID,
        input_snapshot: dict,
        result_snapshot: dict,
        formula_ids: list[str],
    ) -> CalculationRunDTO: ...
    def get_by_id(self, run_id: UUID, owner_id: UUID) -> CalculationRunDTO | None: ...
    def list_by_owner(self, owner_id: UUID) -> list[CalculationRunDTO]: ...


class ReportRepository(Protocol):
    def create(self, calculation_run_id: UUID, owner_id: UUID, pdf_data: bytes) -> ReportDTO: ...
    def get_by_id(self, report_id: UUID, owner_id: UUID) -> ReportDTO | None: ...
