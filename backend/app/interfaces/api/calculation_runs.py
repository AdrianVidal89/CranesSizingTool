"""Calculation-run persistence endpoints: save, list, get one.

Every read/write requires an authenticated user and filters by owner_id at
the repository level (infrastructure/db/repositories.py) — that is the
single enforcement point for CLAUDE.md's per-user isolation rule, not
something each endpoint re-implements.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.application.dto import UserDTO
from app.application.save_calculation_run import (
    ProjectNotFoundError,
    SaveCalculationRun,
    SaveCalculationRunRequest,
)
from app.application.validate_candidate import ValidateCandidate
from app.infrastructure.db.repositories import (
    SqlAlchemyCalculationRunRepository,
    SqlAlchemyCraneConfigurationRepository,
    SqlAlchemyMovementRepository,
    SqlAlchemyProjectRepository,
)
from app.infrastructure.db.session import get_db
from app.interfaces.api.auth import get_current_user, require_csrf
from app.interfaces.api.calc import (
    validate_candidate_request_from_payload,
    validate_candidate_response_from_result,
)
from app.interfaces.schemas.calculation_runs import (
    CalculationRunDetailSchema,
    CalculationRunSummarySchema,
    SaveCalculationRunRequestSchema,
)

router = APIRouter(prefix="/api/calculation-runs", tags=["calculation-runs"])

_META_FIELDS = {
    "project_id",
    "new_project_name",
    "crane_configuration_name",
    "movement_kind",
    "movement_name",
}


def _to_detail(run) -> CalculationRunDetailSchema:
    return CalculationRunDetailSchema(
        id=run.id,
        formula_ids=run.formula_ids,
        input_snapshot=run.input_snapshot,
        result_snapshot=run.result_snapshot,
        created_at=run.created_at,
    )


@router.post("", response_model=CalculationRunDetailSchema, status_code=201)
def save_calculation_run(
    payload: SaveCalculationRunRequestSchema,
    user: UserDTO = Depends(get_current_user),
    db: Session = Depends(get_db),
    _csrf: None = Depends(require_csrf),
) -> CalculationRunDetailSchema:
    calc_request = validate_candidate_request_from_payload(payload)
    try:
        result = ValidateCandidate().execute(calc_request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    result_dict = validate_candidate_response_from_result(result).model_dump(mode="json")
    input_dict = payload.model_dump(mode="json", exclude=_META_FIELDS)

    use_case = SaveCalculationRun(
        SqlAlchemyProjectRepository(db),
        SqlAlchemyCraneConfigurationRepository(db),
        SqlAlchemyMovementRepository(db),
        SqlAlchemyCalculationRunRepository(db),
    )
    try:
        run = use_case.execute(
            SaveCalculationRunRequest(
                owner_id=user.id,
                project_id=payload.project_id,
                new_project_name=payload.new_project_name,
                crane_configuration_name=payload.crane_configuration_name,
                movement_kind=payload.movement_kind,
                movement_name=payload.movement_name,
                input_snapshot=input_dict,
                result_snapshot=result_dict,
            )
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Project not found") from exc
    db.commit()

    return _to_detail(run)


@router.get("", response_model=list[CalculationRunSummarySchema])
def list_calculation_runs(
    user: UserDTO = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[CalculationRunSummarySchema]:
    runs = SqlAlchemyCalculationRunRepository(db).list_by_owner(user.id)
    return [
        CalculationRunSummarySchema(id=r.id, formula_ids=r.formula_ids, created_at=r.created_at)
        for r in runs
    ]


@router.get("/{run_id}", response_model=CalculationRunDetailSchema)
def get_calculation_run(
    run_id: UUID, user: UserDTO = Depends(get_current_user), db: Session = Depends(get_db)
) -> CalculationRunDetailSchema:
    run = SqlAlchemyCalculationRunRepository(db).get_by_id(run_id, user.id)
    if run is None:
        raise HTTPException(status_code=404, detail="Calculation run not found")
    return _to_detail(run)
