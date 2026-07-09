"""Pydantic schemas for the travel calculation endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TravelRequirementRequestSchema(BaseModel):
    mass_dead_kg: float = Field(
        ..., gt=0, description="Dead mass of the gantry/trolley mechanism, kg"
    )
    mass_load_kg: float = Field(..., ge=0, description="Mass of the load (SWL), kg")
    mass_tool_kg: float = Field(..., ge=0, description="Mass of the tool/spreader, kg")
    velocity_ms: float = Field(..., gt=0, description="Nominal travel speed, m/s")
    accel_time_s: float = Field(..., gt=0, description="Acceleration ramp time, s")
    wheel_diameter_m: float = Field(..., gt=0, description="Wheel diameter, m")
    gear_ratio: float = Field(..., gt=0, description="Gearbox reduction ratio")
    efficiency: float = Field(
        ..., gt=0, le=1, description="Mechanical efficiency (gearbox + transmission)"
    )
    motors_count: int = Field(
        ..., gt=0, description="Number of motors/drives for this movement"
    )
    rolling_coeff: float = Field(..., gt=0, description="Rolling resistance coefficient")


class FormulaOutputSchema(BaseModel):
    label: str
    value: float
    unit: str
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


class TravelRequirementResponseSchema(BaseModel):
    required_torque_nm: float
    required_speed_rpm: float
    steady_torque_nm: float
    dynamic_torque_nm: float
    components: tuple[FormulaOutputSchema, ...]
