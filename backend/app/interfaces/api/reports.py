"""Report endpoints: generate a PDF from a saved calculation run, download
it. Every read/write requires an authenticated user and filters by
owner_id at the repository level (CLAUDE.md isolation rule)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.application.dto import UserDTO
from app.application.generate_report import (
    CalculationRunNotFoundError,
    GenerateReport,
    GenerateReportRequest,
)
from app.infrastructure.db.repositories import (
    SqlAlchemyCalculationRunRepository,
    SqlAlchemyReportRepository,
)
from app.infrastructure.db.session import get_db
from app.infrastructure.reports.pdf_generator import generate_report_pdf
from app.interfaces.api.auth import get_current_user, require_csrf
from app.interfaces.schemas.reports import GenerateReportRequestSchema, ReportResponseSchema

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("", response_model=ReportResponseSchema, status_code=201)
def create_report(
    payload: GenerateReportRequestSchema,
    user: UserDTO = Depends(get_current_user),
    db: Session = Depends(get_db),
    _csrf: None = Depends(require_csrf),
) -> ReportResponseSchema:
    use_case = GenerateReport(
        SqlAlchemyCalculationRunRepository(db),
        SqlAlchemyReportRepository(db),
        generate_report_pdf,
    )
    try:
        report = use_case.execute(
            GenerateReportRequest(owner_id=user.id, calculation_run_id=payload.calculation_run_id)
        )
    except CalculationRunNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Calculation run not found") from exc
    db.commit()

    return ReportResponseSchema(
        id=report.id, calculation_run_id=report.calculation_run_id, generated_at=report.generated_at
    )


@router.get("/{report_id}/pdf")
def download_report_pdf(
    report_id: UUID, user: UserDTO = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    report = SqlAlchemyReportRepository(db).get_by_id(report_id, user.id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return Response(
        content=report.pdf_data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="report-{report.id}.pdf"'},
    )
