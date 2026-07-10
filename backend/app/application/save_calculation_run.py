"""SaveCalculationRun: persists a requirement+candidate calculation as an
immutable, reproducible snapshot.

CalculationRun never recomputes from mutable references — the exact input
that was sent and the exact result that was computed are stored together,
so an old run reproduces identically even after the calculation engine
evolves (CLAUDE.md: "Un cálculo debe ser determinista, transparente,
auditable, reproducible y versionado").
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.application.dto import CalculationRunDTO
from app.application.ports import (
    CalculationRunRepository,
    CraneConfigurationRepository,
    MovementRepository,
    ProjectRepository,
)


class ProjectNotFoundError(Exception):
    pass


def extract_formula_ids(node: object) -> list[str]:
    """Walk a JSON-like structure and collect every "formula_id" value,
    sorted, for at-a-glance auditing of which calc_versions a run used."""
    found: set[str] = set()
    _walk(node, found)
    return sorted(found)


def _walk(node: object, found: set[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "formula_id" and isinstance(value, str):
                found.add(value)
            else:
                _walk(value, found)
    elif isinstance(node, list):
        for item in node:
            _walk(item, found)


@dataclass(frozen=True)
class SaveCalculationRunRequest:
    owner_id: UUID
    project_id: UUID | None
    new_project_name: str | None
    crane_configuration_name: str
    movement_kind: str
    movement_name: str
    input_snapshot: dict
    result_snapshot: dict


class SaveCalculationRun:
    def __init__(
        self,
        projects: ProjectRepository,
        crane_configurations: CraneConfigurationRepository,
        movements: MovementRepository,
        calculation_runs: CalculationRunRepository,
    ) -> None:
        self._projects = projects
        self._crane_configurations = crane_configurations
        self._movements = movements
        self._calculation_runs = calculation_runs

    def execute(self, request: SaveCalculationRunRequest) -> CalculationRunDTO:
        if request.project_id is not None:
            project = self._projects.get_by_id(request.project_id, request.owner_id)
            if project is None:
                raise ProjectNotFoundError(request.project_id)
        else:
            if not request.new_project_name:
                raise ValueError("new_project_name is required when project_id is not given")
            project = self._projects.create(
                owner_id=request.owner_id, name=request.new_project_name
            )

        crane_configuration = self._crane_configurations.create(
            project_id=project.id, name=request.crane_configuration_name
        )
        movement = self._movements.create(
            crane_configuration_id=crane_configuration.id,
            kind=request.movement_kind,
            name=request.movement_name,
        )

        formula_ids = extract_formula_ids(request.result_snapshot)

        return self._calculation_runs.create(
            movement_id=movement.id,
            owner_id=request.owner_id,
            input_snapshot=request.input_snapshot,
            result_snapshot=request.result_snapshot,
            formula_ids=formula_ids,
        )
