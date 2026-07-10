"""Pydantic schemas for the candidate-validation endpoint (Phase 3, stage 2
of the business flow: the user proposes, the system validates)."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.interfaces.schemas.duty_cycle import (
    DutyCycleRequestFieldsSchema,
    DutyCycleResponseSchema,
)


class MotorCandidateSchema(BaseModel):
    rated_power_kw: float = Field(..., gt=0, le=100_000)
    rated_speed_rpm: float = Field(..., gt=0, le=100_000)
    rated_voltage_v: float = Field(..., gt=0, le=1_000_000)
    power_factor: float = Field(..., gt=0, le=1, description="cos(phi)")
    efficiency: float = Field(..., gt=0, le=1)
    nameplate_frequency_hz: float = Field(..., gt=0, le=1000)

    breakdown_torque_pu: float | None = Field(None, gt=0, le=100)
    breakdown_torque_nm: float | None = Field(None, gt=0, le=10_000_000)
    max_mechanical_torque_pu: float | None = Field(None, gt=0, le=100)
    max_mechanical_torque_nm: float | None = Field(None, gt=0, le=10_000_000)

    no_load_current_a: float | None = Field(
        None, ge=0, le=1_000_000, description="I_0, nameplate, optional"
    )
    rotor_inertia_kgm2: float = Field(0.0, ge=0, le=10_000)

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
    rated_current_a: float = Field(..., gt=0, le=1_000_000)
    overload_factor: float = Field(..., ge=1, le=100)
    overload_duration_s: float = Field(..., gt=0, le=86_400)
    rated_voltage_v: float = Field(..., gt=0, le=1_000_000)


class ValidateCandidateRequestSchema(DutyCycleRequestFieldsSchema):
    # Mechanics + duty cycle inputs inherited from DutyCycleRequestFieldsSchema
    # (same fields and bounds as the duty-cycle endpoint, including the
    # duty_factor_pct/starts_per_hour exclusivity check).

    # Candidate inputs — the user proposes, the system validates.
    motor: MotorCandidateSchema
    motor_target_frequency_hz: float = Field(
        ..., gt=0, le=1000, description="Mains frequency the motor will run at"
    )
    drive: DriveCandidateSchema | None = None


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
