"""Calculation endpoints — requirement stage (see CLAUDE.md business flow)."""

from __future__ import annotations

from fastapi import APIRouter

from app.application.calculate_travel_requirement import (
    CalculateTravelRequirement,
    TravelRequirementRequest,
)
from app.interfaces.schemas.travel import (
    FormulaOutputSchema,
    TravelRequirementRequestSchema,
    TravelRequirementResponseSchema,
)

router = APIRouter(prefix="/api/calc", tags=["calculation"])


@router.post("/travel", response_model=TravelRequirementResponseSchema)
def calculate_travel_requirement(
    payload: TravelRequirementRequestSchema,
) -> TravelRequirementResponseSchema:
    use_case = CalculateTravelRequirement()
    result = use_case.execute(
        TravelRequirementRequest(
            mass_dead_kg=payload.mass_dead_kg,
            mass_load_kg=payload.mass_load_kg,
            mass_tool_kg=payload.mass_tool_kg,
            velocity_ms=payload.velocity_ms,
            accel_time_s=payload.accel_time_s,
            wheel_diameter_m=payload.wheel_diameter_m,
            gear_ratio=payload.gear_ratio,
            efficiency=payload.efficiency,
            motors_count=payload.motors_count,
            rolling_coeff=payload.rolling_coeff,
        )
    )
    return TravelRequirementResponseSchema(
        required_torque_nm=result.required_torque_nm,
        required_speed_rpm=result.required_speed_rpm,
        components=tuple(
            FormulaOutputSchema(
                label=c.label,
                value=c.value,
                unit=c.unit,
                formula_id=c.formula_id,
                assumptions=c.assumptions,
                standard_refs=c.standard_refs,
            )
            for c in result.components
        ),
    )
