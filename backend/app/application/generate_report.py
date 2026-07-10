"""GenerateReport: renders a PDF from an already-persisted CalculationRun
and stores it. Never runs a calculation itself — it only reads a frozen
snapshot (CLAUDE.md: report generation formats results, it doesn't compute
them)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from app.application.dto import CalculationRunDTO, ReportDTO
from app.application.ports import CalculationRunRepository, ReportRepository


class CalculationRunNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class GenerateReportRequest:
    owner_id: UUID
    calculation_run_id: UUID


class GenerateReport:
    def __init__(
        self,
        calculation_runs: CalculationRunRepository,
        reports: ReportRepository,
        render_pdf: Callable[[CalculationRunDTO], bytes],
    ) -> None:
        self._calculation_runs = calculation_runs
        self._reports = reports
        self._render_pdf = render_pdf

    def execute(self, request: GenerateReportRequest) -> ReportDTO:
        run = self._calculation_runs.get_by_id(request.calculation_run_id, request.owner_id)
        if run is None:
            raise CalculationRunNotFoundError(request.calculation_run_id)

        pdf_bytes = self._render_pdf(run)
        return self._reports.create(
            calculation_run_id=run.id, owner_id=request.owner_id, pdf_data=pdf_bytes
        )
