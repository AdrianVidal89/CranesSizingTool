"""Pydantic schemas for the candidate-validation endpoint (Phase 3, stage 2
of the business flow: the user proposes, the system validates)."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.interfaces.schemas.duty_cycle import DutyCycleResponseSchema


class MotorCandidateSchema(BaseModel):
    rated_power_kw: float = Field(..., gt=0)
    rated_speed_rpm: float = Field(..., gt=0)
    rated_voltage_v: float = Field(..., gt=0)
    power_factor: float = Field(..., gt=0, le=1, description="cos(phi)")
    efficiency: float = Field(..., gt=0, le=1)
    nameplate_frequency_hz: float = Field(..., gt=0)

    breakdown_torque_pu: float | None = Field(None, gt=0)
    breakdown_torque_nm: float | None = Field(None, gt=0)
    max_mechanical_torque_pu: float | None = Field(None, gt=0)
    max_mechanical_torque_nm: float | None = Field(None, gt=0)

    no_load_current_a: float | None = Field(None, ge=0, description="I_0, nameplate, optional")
    rotor_inertia_kgm2: float = Field(0.0, ge=0)

    @model_validator(mode="after")
    def check_exactly_one_torque_field(self) -> "MotorCandidateSchema":
        for name, pu, absolute in (
            ("breakdown_torque", self.breakdown_torque_pu, self.breakdown_torque_nm),
            (
                "max_mechanical_torque",
                self.max_mechanical_torque_pu,
                self.max_mechanical_torque_nm,
            ),
        ):
            if sum((pu is not None, absolute is not None)) != 1:
                raise ValueError(
                    f"Exactly one of {name}_pu or {name}_nm must be provided"
                )
        return self


class DriveCandidateSchema(BaseModel):
    rated_current_a: float = Field(..., gt=0)
    overload_factor: float = Field(..., ge=1)
    overload_duration_s: float = Field(..., gt=0)
    rated_voltage_v: float = Field(..., gt=0)


class ValidateCandidateRequestSchema(BaseModel):
    # Mechanics + duty cycle inputs (same shape as DutyCycleRequestSchema).
    mass_dead_kg: float = Field(..., gt=0)
    mass_load_kg: float = Field(..., ge=0)
    mass_tool_kg: float = Field(..., ge=0)
    velocity_ms: float = Field(..., gt=0)
    accel_time_s: float = Field(..., gt=0)
    wheel_diameter_m: float = Field(..., gt=0)
    gear_ratio: float = Field(..., gt=0)
    efficiency: float = Field(..., gt=0, le=1)
    motors_count: int = Field(..., gt=0)
    rolling_coeff: float = Field(..., gt=0)
    distance_m: float = Field(..., gt=0)
    decel_time_s: float | None = Field(None, gt=0)
    duty_factor_pct: float | None = Field(None, gt=0, le=100)
    starts_per_hour: float | None = Field(None, gt=0)
    cooling_factor: float = Field(0.5, ge=0, le=1)
    mechanism_group: str | None = None

    # Candidate inputs — the user proposes, the system validates.
    motor: MotorCandidateSchema
    motor_target_frequency_hz: float = Field(
        ..., gt=0, description="Mains frequency the motor will run at"
    )
    drive: DriveCandidateSchema | None = None

    @model_validator(mode="after")
    def check_duty_regime_exclusive(self) -> "ValidateCandidateRequestSchema":
        provided = (self.duty_factor_pct is not None, self.starts_per_hour is not None)
        if sum(provided) != 1:
            raise ValueError(
                "Exactly one of duty_factor_pct or starts_per_hour must be provided"
            )
        return self


class ConditionResultSchema(BaseModel):
    label: str
    verdict: str
    required_value: float
    available_value: float
    margin: float
    formula_id: str
    assumptions: tuple[str, ...]
    standard_refs: tuple[str, ...]


class ResolvedMotorSchema(BaseModel):
    rated_torque_nm: float
    rated_speed_rpm: float
    rated_current_a: float
    breakdown_torque_nm: float
    max_mechanical_torque_nm: float


class ValidateCandidateResponseSchema(BaseModel):
    requirement: DutyCycleResponseSchema
    resolved_motor: ResolvedMotorSchema
    motor_conditions: tuple[ConditionResultSchema, ...]
    motor_passed: bool
    drive_conditions: tuple[ConditionResultSchema, ...] | None
    drive_passed: bool | None
    rms_current_a: float | None
