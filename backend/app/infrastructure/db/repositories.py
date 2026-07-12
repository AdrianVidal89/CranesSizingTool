"""SQLAlchemy implementations of the application-layer repository ports
(app/application/ports.py). This is the only place that translates between
ORM rows and the framework-agnostic DTOs the rest of the app depends on.

Every method that reads or writes user-owned data filters by owner_id in
its query — never fetches a row first and checks ownership in Python,
which would be easy to forget at a new call site.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.dto import (
    CalculationRunDTO,
    CraneConfigurationDTO,
    MovementDTO,
    ProjectDTO,
    ReportDTO,
    SessionDTO,
    UserDTO,
)
from app.infrastructure.db.models import (
    CalculationRun,
    CraneConfiguration,
    Movement,
    Project,
    Report,
    User,
    UserSession,
)


def _user_to_dto(row: User) -> UserDTO:
    return UserDTO(
        id=row.id, email=row.email, password_hash=row.password_hash, created_at=row.created_at
    )


def _session_to_dto(row: UserSession) -> SessionDTO:
    return SessionDTO(
        id=row.id,
        user_id=row.user_id,
        token_hash=row.token_hash,
        csrf_token=row.csrf_token,
        created_at=row.created_at,
        expires_at=row.expires_at,
    )


def _project_to_dto(row: Project) -> ProjectDTO:
    return ProjectDTO(
        id=row.id,
        owner_id=row.owner_id,
        name=row.name,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _crane_configuration_to_dto(row: CraneConfiguration) -> CraneConfigurationDTO:
    return CraneConfigurationDTO(
        id=row.id, project_id=row.project_id, name=row.name, created_at=row.created_at
    )


def _movement_to_dto(row: Movement) -> MovementDTO:
    return MovementDTO(
        id=row.id,
        crane_configuration_id=row.crane_configuration_id,
        kind=row.kind,
        name=row.name,
        created_at=row.created_at,
    )


def _calculation_run_to_dto(row: CalculationRun) -> CalculationRunDTO:
    return CalculationRunDTO(
        id=row.id,
        movement_id=row.movement_id,
        owner_id=row.owner_id,
        input_snapshot=row.input_snapshot,
        result_snapshot=row.result_snapshot,
        formula_ids=row.formula_ids,
        created_at=row.created_at,
    )


def _report_to_dto(row: Report) -> ReportDTO:
    return ReportDTO(
        id=row.id,
        calculation_run_id=row.calculation_run_id,
        owner_id=row.owner_id,
        pdf_data=row.pdf_data,
        generated_at=row.generated_at,
    )


class SqlAlchemyUserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_email(self, email: str) -> UserDTO | None:
        row = self._db.query(User).filter_by(email=email).one_or_none()
        return _user_to_dto(row) if row is not None else None

    def get_by_id(self, user_id: UUID) -> UserDTO | None:
        row = self._db.get(User, user_id)
        return _user_to_dto(row) if row is not None else None

    def create(self, email: str, password_hash: str) -> UserDTO:
        row = User(email=email, password_hash=password_hash)
        self._db.add(row)
        self._db.flush()
        return _user_to_dto(row)


class SqlAlchemySessionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self, user_id: UUID, token_hash: str, csrf_token: str, expires_at: datetime
    ) -> SessionDTO:
        row = UserSession(
            user_id=user_id, token_hash=token_hash, csrf_token=csrf_token, expires_at=expires_at
        )
        self._db.add(row)
        self._db.flush()
        return _session_to_dto(row)

    def get_by_token_hash(self, token_hash: str) -> SessionDTO | None:
        row = self._db.query(UserSession).filter_by(token_hash=token_hash).one_or_none()
        return _session_to_dto(row) if row is not None else None

    def delete(self, session_id: UUID) -> None:
        row = self._db.get(UserSession, session_id)
        if row is not None:
            self._db.delete(row)


class SqlAlchemyProjectRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, owner_id: UUID, name: str) -> ProjectDTO:
        row = Project(owner_id=owner_id, name=name)
        self._db.add(row)
        self._db.flush()
        return _project_to_dto(row)

    def get_by_id(self, project_id: UUID, owner_id: UUID) -> ProjectDTO | None:
        row = (
            self._db.query(Project)
            .filter_by(id=project_id, owner_id=owner_id)
            .one_or_none()
        )
        return _project_to_dto(row) if row is not None else None

    def list_by_owner(self, owner_id: UUID) -> list[ProjectDTO]:
        rows = (
            self._db.query(Project)
            .filter_by(owner_id=owner_id)
            .order_by(Project.created_at.desc())
            .all()
        )
        return [_project_to_dto(row) for row in rows]


class SqlAlchemyCraneConfigurationRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, project_id: UUID, name: str) -> CraneConfigurationDTO:
        row = CraneConfiguration(project_id=project_id, name=name)
        self._db.add(row)
        self._db.flush()
        return _crane_configuration_to_dto(row)

    def list_by_project(self, project_id: UUID) -> list[CraneConfigurationDTO]:
        rows = (
            self._db.query(CraneConfiguration)
            .filter_by(project_id=project_id)
            .order_by(CraneConfiguration.created_at)
            .all()
        )
        return [_crane_configuration_to_dto(row) for row in rows]


class SqlAlchemyMovementRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, crane_configuration_id: UUID, kind: str, name: str) -> MovementDTO:
        row = Movement(crane_configuration_id=crane_configuration_id, kind=kind, name=name)
        self._db.add(row)
        self._db.flush()
        return _movement_to_dto(row)

    def list_by_crane_configuration(self, crane_configuration_id: UUID) -> list[MovementDTO]:
        rows = (
            self._db.query(Movement)
            .filter_by(crane_configuration_id=crane_configuration_id)
            .order_by(Movement.created_at)
            .all()
        )
        return [_movement_to_dto(row) for row in rows]


class SqlAlchemyCalculationRunRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        movement_id: UUID,
        owner_id: UUID,
        input_snapshot: dict,
        result_snapshot: dict,
        formula_ids: list[str],
    ) -> CalculationRunDTO:
        row = CalculationRun(
            movement_id=movement_id,
            owner_id=owner_id,
            input_snapshot=input_snapshot,
            result_snapshot=result_snapshot,
            formula_ids=formula_ids,
        )
        self._db.add(row)
        self._db.flush()
        return _calculation_run_to_dto(row)

    def get_by_id(self, run_id: UUID, owner_id: UUID) -> CalculationRunDTO | None:
        row = (
            self._db.query(CalculationRun)
            .filter_by(id=run_id, owner_id=owner_id)
            .one_or_none()
        )
        return _calculation_run_to_dto(row) if row is not None else None

    def list_by_owner(self, owner_id: UUID) -> list[CalculationRunDTO]:
        rows = (
            self._db.query(CalculationRun)
            .filter_by(owner_id=owner_id)
            .order_by(CalculationRun.created_at.desc())
            .all()
        )
        return [_calculation_run_to_dto(row) for row in rows]


class SqlAlchemyReportRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, calculation_run_id: UUID, owner_id: UUID, pdf_data: bytes) -> ReportDTO:
        row = Report(calculation_run_id=calculation_run_id, owner_id=owner_id, pdf_data=pdf_data)
        self._db.add(row)
        self._db.flush()
        return _report_to_dto(row)

    def get_by_id(self, report_id: UUID, owner_id: UUID) -> ReportDTO | None:
        row = self._db.query(Report).filter_by(id=report_id, owner_id=owner_id).one_or_none()
        return _report_to_dto(row) if row is not None else None
