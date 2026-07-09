"""Project endpoints. Every read/write requires an authenticated user and
filters by owner_id at the repository level (CLAUDE.md isolation rule)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.dto import UserDTO
from app.infrastructure.db.repositories import SqlAlchemyProjectRepository
from app.infrastructure.db.session import get_db
from app.interfaces.api.auth import get_current_user, require_csrf
from app.interfaces.schemas.projects import ProjectCreateRequestSchema, ProjectResponseSchema

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _to_response(project) -> ProjectResponseSchema:
    return ProjectResponseSchema(
        id=project.id,
        name=project.name,
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
    db.commit()
    return _to_response(project)


@router.get("", response_model=list[ProjectResponseSchema])
def list_projects(
    user: UserDTO = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ProjectResponseSchema]:
    projects = SqlAlchemyProjectRepository(db).list_by_owner(user.id)
    return [_to_response(p) for p in projects]
