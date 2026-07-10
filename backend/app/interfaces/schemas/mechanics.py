"""Shared mechanics input fields (Module 1 — MECH.TRAVEL), reused by every
calculation request schema (travel, duty-cycle, validate-candidate,
save-calculation-run) so a validation bound fixed once can never drift
between duplicated copies (CLAUDE.md: strict input validation at the API
edge). Upper bounds are generous engineering sanity limits, not tight
physical plausibility checks — that judgment belongs to the engineer
reading the report, not the API layer.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class MechanicsRequestFieldsSchema(BaseModel):
    mass_dead_kg: float = Field(
        ..., gt=0, le=1_000_000, description="Dead mass of the gantry/trolley mechanism, kg"
    )
    mass_load_kg: float = Field(..., ge=0, le=1_000_000, description="Mass of the load (SWL), kg")
    mass_tool_kg: float = Field(
        ..., ge=0, le=1_000_000, description="Mass of the tool/spreader, kg"
    )
    velocity_ms: float = Field(..., gt=0, le=50, description="Nominal travel speed, m/s")
    accel_time_s: float = Field(..., gt=0, le=300, description="Acceleration ramp time, s")
    wheel_diameter_m: float = Field(..., gt=0, le=10, description="Wheel diameter, m")
    gear_ratio: float = Field(..., gt=0, le=10_000, description="Gearbox reduction ratio")
    efficiency: float = Field(
        ..., gt=0, le=1, description="Mechanical efficiency (gearbox + transmission)"
    )
    motors_count: int = Field(
        ..., gt=0, le=100, description="Number of motors/drives for this movement"
    )
    rolling_coeff: float = Field(..., gt=0, le=1, description="Rolling resistance coefficient")
