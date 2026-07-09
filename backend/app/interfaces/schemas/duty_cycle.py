"""Pydantic schemas for the duty-cycle calculation endpoint."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class DutyCycleRequestSchema(BaseModel):
    # Mechanics inputs (same shape as TravelRequirementRequestSchema; the
    # duty cycle is computed on top of the travel requirement).
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

    # Duty cycle inputs
    distance_m: float = Field(..., gt=0, description="Movement travel distance, m")
    decel_time_s: float | None = Field(
        None, gt=0, description="Deceleration ramp time, s (defaults to accel_time_s)"
    )
    duty_factor_pct: float | None = Field(
        None, gt=0, le=100, description="Target cyclic duration factor %ED"
    )
    starts_per_hour: float | None = Field(
        None, gt=0, description="Target starts per hour"
    )
    cooling_factor: float = Field(
        0.5, ge=0, le=1, description="k_f, standstill cooling factor (0=none, 1=full)"
    )
    mechanism_group: str | None = Field(
        None, description="ISO 4301-1 / FEM 9.511 mechanism group, e.g. 'M5'"
    )

    @model_validator(mode="after")
    def check_duty_regime_exclusive(self) -> "DutyCycleRequestSchema":
        provided = (self.duty_factor_pct is not None, self.starts_per_hour is not None)
        if sum(provided) != 1:
            raise ValueError(
                "Exactly one of duty_factor_pct or starts_per_hour must be provided"
            )
        return self


class MotionProfileSchema(BaseModel):
    accel_time_s: float
    const_time_s: float
    decel_time_s: float
    accel_distance_m: float
    const_distance_m: float
    decel_distance_m: float
    peak_velocity_ms: float
    is_triangular: bool
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


class DutyRegimeSchema(BaseModel):
    on_time_s: float
    off_time_s: float
    cycle_time_s: float
    duty_factor_pct: float
    starts_per_hour: float
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


class DecelTorqueSchema(BaseModel):
    value_nm: float
    is_regenerative: bool
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


class ThermalRmsSchema(BaseModel):
    value: float
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


class PhaseEnergySchema(BaseModel):
    label: str
    energy_j: float
    is_regenerative: bool


class EnergyCycleSchema(BaseModel):
    energy_per_cycle_j: float
    energy_per_hour_j: float
    phases: tuple[PhaseEnergySchema, ...]
    has_regenerative_phase: bool
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


class MechanismGroupCheckSchema(BaseModel):
    status: str
    mechanism_group: str | None
    starts_per_hour_limit: float | None
    note: str


class DutyCycleResponseSchema(BaseModel):
    required_torque_nm: float
    required_speed_rpm: float
    steady_torque_nm: float
    dynamic_torque_nm: float
    profile: MotionProfileSchema
    regime: DutyRegimeSchema
    decel_torque: DecelTorqueSchema
    rms_torque: ThermalRmsSchema
    energy: EnergyCycleSchema
    mechanism_group_check: MechanismGroupCheckSchema
