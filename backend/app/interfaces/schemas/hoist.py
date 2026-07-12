"""Pydantic schemas for the hoist calculation endpoint (Module 2 — MECH.HOIST).

Same validation philosophy as mechanics.py: generous engineering sanity
bounds at the API edge, physical plausibility judgment stays with the
engineer reading the report.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.interfaces.schemas.travel import FormulaOutputSchema


class HoistRequirementRequestSchema(BaseModel):
    mass_load_kg: float = Field(..., ge=0, le=1_000_000, description="Mass of the load (SWL), kg")
    mass_tool_kg: float = Field(
        ..., ge=0, le=1_000_000, description="Mass of the hook block / lifting tool, kg"
    )
    velocity_ms: float = Field(..., gt=0, le=10, description="Hoisting speed at the hook, m/s")
    accel_time_s: float = Field(..., gt=0, le=300, description="Acceleration ramp time, s")
    drum_diameter_m: float = Field(..., gt=0, le=10, description="Rope drum diameter, m")
    reeving_factor: float = Field(
        ..., ge=1, le=100, description="Reeving factor (number of rope falls carrying the load)"
    )
    gear_ratio: float = Field(..., gt=0, le=10_000, description="Gearbox reduction ratio")
    efficiency: float = Field(
        ..., gt=0, le=1, description="Mechanical efficiency (gearbox + drum + reeving)"
    )
    motor_inertia_kgm2: float = Field(
        ..., ge=0, le=10_000, description="Motor rotor moment of inertia, kg*m^2"
    )
    brake_inertia_kgm2: float = Field(
        ..., ge=0, le=10_000, description="Brake moment of inertia, kg*m^2"
    )

    @model_validator(mode="after")
    def _check_hook_load(self) -> "HoistRequirementRequestSchema":
        if self.mass_load_kg + self.mass_tool_kg <= 0:
            raise ValueError("mass_load_kg + mass_tool_kg must be greater than zero")
        return self


class HoistRequirementResponseSchema(BaseModel):
    required_torque_nm: float
    required_speed_rpm: float
    static_lifting_torque_nm: float
    static_lowering_torque_nm: float
    rotor_dynamic_torque_nm: float
    load_dynamic_torque_nm: float
    components: tuple[FormulaOutputSchema, ...]
