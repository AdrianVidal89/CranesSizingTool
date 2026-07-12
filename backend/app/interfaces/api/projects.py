"""Project endpoints. Every read/write requires an authenticated user and
filters by owner_id at the repository level (CLAUDE.md isolation rule).

A project is created together with its movements (named hoists and travel
movements, at most 3 of each), stored under a single crane configuration.
Crane configurations and movements are only ever traversed after the
parent project's ownership has been verified.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.dto import MovementDTO, ProjectDTO, UserDTO
from app.infrastructure.db.repositories import (
    SqlAlchemyCraneConfigurationRepository,
    SqlAlchemyMovementRepository,
    SqlAlchemyProjectRepository,
)
from app.infrastructure.db.session import get_db
from app.interfaces.api.auth import get_current_user, require_csrf
from app.interfaces.schemas.projects import (
    MovementResponseSchema,
    ProjectCreateRequestSchema,
    ProjectResponseSchema,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _movements_for_project(db: Session, project_id) -> list[MovementDTO]:
    configurations = SqlAlchemyCraneConfigurationRepository(db).list_by_project(project_id)
    movement_repo = SqlAlchemyMovementRepository(db)
    movements: list[MovementDTO] = []
    for configuration in configurations:
        movements.extend(movement_repo.list_by_crane_configuration(configuration.id))
    return movements


def _to_response(project: ProjectDTO, movements: list[MovementDTO]) -> ProjectResponseSchema:
    return ProjectResponseSchema(
        id=project.id,
        name=project.name,
        movements=tuple(
            MovementResponseSchema(id=m.id, kind=m.kind, name=m.name) for m in movements
        ),
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post("", response_model=ProjectResponseSchema, status_code=201)
def create_project(
    payload: ProjectCreateRequestSchema,
    user: UserDTO = Depends(get_current_user),
    db: Session = Depends(get_db),
    _csrf: None = Depends(require_csrf),
) -> ProjectResponseSchema:
    project = SqlAlchemyProjectRepository(db).create(owner_id=user.id, name=payload.name)

    movements: list[MovementDTO] = []
    if payload.movements:
        configuration = SqlAlchemyCraneConfigurationRepository(db).create(
            project_id=project.id, name=payload.crane_configuration_name
        )
        movement_repo = SqlAlchemyMovementRepository(db)
        movements = [
            movement_repo.create(
                crane_configuration_id=configuration.id, kind=m.kind, name=m.name
            )
            for m in payload.movements
        ]

    db.commit()
    return _to_response(project, movements)


@router.get("", response_model=list[ProjectResponseSchema])
def list_projects(
    user: UserDTO = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ProjectResponseSchema]:
    projects = SqlAlchemyProjectRepository(db).list_by_owner(user.id)
    return [_to_response(p, _movements_for_project(db, p.id)) for p in projects]
