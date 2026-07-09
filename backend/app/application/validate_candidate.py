"""Candidate-validation use case: closes the two-stage business flow.

Stage 1 ("Requirement", Phases 1-2) computed the torque/speed/RMS the
mechanism needs, independent of any motor. Stage 2 ("Validation") takes a
user-proposed MotorCandidate (and optionally a DriveCandidate) and validates
it against that requirement. The system never selects equipment on its own
(CLAUDE.md business flow).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.application.calculate_duty_cycle import (
    CalculateDutyCycle,
    CalculateDutyCycleRequest,
    DutyCycleCalculationResult,
)
from app.domain.calc.cycle.thermal import ThermalRmsInput, rms_current
from app.domain.calc.drive.candidate import DriveCandidate
from app.domain.calc.drive.sizing import (
    CurrentOfTorqueInput,
    NoLoadCurrentRatioInput,
    PhaseCurrentsInput,
    current_of_torque,
    no_load_current_ratio,
    phase_currents,
)
from app.domain.calc.drive.validation import (
    DriveValidationInput,
    DriveValidationResult,
    validate_drive_candidate,
)
from app.domain.calc.motor.candidate import MotorCandidate, resolve_absolute_torque_nm
from app.domain.calc.motor.sizing import (
    FrequencyConversionInput,
    RatedCurrentInput,
    convert_frequency,
    rated_current,
)
from app.domain.calc.motor.validation import (
    MotorValidationInput,
    MotorValidationResult,
    validate_motor_candidate,
)
from app.domain.standards.drive_sizing_policy import (
    DEFAULT_DRIVE_SIZING_POLICY,
    DriveSizingPolicy,
)
from app.domain.standards.motor_sizing_policy import (
    DEFAULT_MOTOR_SIZING_POLICY,
    MotorSizingPolicy,
)


@dataclass(frozen=True)
class ValidateCandidateRequest:
    duty_cycle: CalculateDutyCycleRequest
    motor: MotorCandidate
    motor_target_frequency_hz: float
    """Mains frequency the motor will actually run at; usually equal to
    motor.nameplate_frequency_hz (no conversion)."""
    drive: DriveCandidate | None
    motor_sizing_policy: MotorSizingPolicy = DEFAULT_MOTOR_SIZING_POLICY
    drive_sizing_policy: DriveSizingPolicy = DEFAULT_DRIVE_SIZING_POLICY


@dataclass(frozen=True)
class ResolvedMotorData:
    rated_torque_nm: float
    rated_speed_rpm: float
    rated_current_a: float
    breakdown_torque_nm: float
    max_mechanical_torque_nm: float


@dataclass(frozen=True)
class ValidateCandidateResult:
    requirement: DutyCycleCalculationResult
    resolved_motor: ResolvedMotorData
    motor_validation: MotorValidationResult
    drive_validation: DriveValidationResult | None
    rms_current_a: float | None
    """I_rms, only computed when a DriveCandidate is given (it needs I(T))."""


class ValidateCandidate:
    """Validate a user-proposed motor (and optional drive) candidate against
    the calculated requirement. Never picks a candidate on its own."""

    def execute(self, request: ValidateCandidateRequest) -> ValidateCandidateResult:
        requirement = CalculateDutyCycle().execute(request.duty_cycle)

        freq = convert_frequency(
            FrequencyConversionInput(
                rated_power_kw=request.motor.rated_power_kw,
                rated_speed_rpm=request.motor.rated_speed_rpm,
                nameplate_frequency_hz=request.motor.nameplate_frequency_hz,
                target_frequency_hz=request.motor_target_frequency_hz,
            )
        )

        breakdown_torque_nm = round(
            resolve_absolute_torque_nm(
                request.motor.breakdown_torque_pu,
                request.motor.breakdown_torque_nm,
                freq.rated_torque_nm,
            ),
            3,
        )
        max_mechanical_torque_nm = round(
            resolve_absolute_torque_nm(
                request.motor.max_mechanical_torque_pu,
                request.motor.max_mechanical_torque_nm,
                freq.rated_torque_nm,
            ),
            3,
        )

        motor_current = rated_current(
            RatedCurrentInput(
                rated_power_kw=freq.rated_power_kw,
                rated_voltage_v=request.motor.rated_voltage_v,
                efficiency=request.motor.efficiency,
                power_factor=request.motor.power_factor,
            )
        )

        resolved_motor = ResolvedMotorData(
            rated_torque_nm=freq.rated_torque_nm,
            rated_speed_rpm=freq.rated_speed_rpm,
            rated_current_a=motor_current.value_a,
            breakdown_torque_nm=breakdown_torque_nm,
            max_mechanical_torque_nm=max_mechanical_torque_nm,
        )

        motor_validation = validate_motor_candidate(
            MotorValidationInput(
                required_torque_nm=requirement.required_torque_nm,
                required_speed_rpm=requirement.required_speed_rpm,
                required_rms_torque_nm=requirement.rms_torque.value,
                rated_torque_nm=freq.rated_torque_nm,
                rated_speed_rpm=freq.rated_speed_rpm,
                max_mechanical_torque_nm=max_mechanical_torque_nm,
                breakdown_torque_nm=breakdown_torque_nm,
                policy=request.motor_sizing_policy,
            )
        )

        drive_validation: DriveValidationResult | None = None
        rms_current_a: float | None = None

        if request.drive is not None:
            no_load = no_load_current_ratio(
                NoLoadCurrentRatioInput(
                    rated_current_a=motor_current.value_a,
                    power_factor=request.motor.power_factor,
                    no_load_current_a=request.motor.no_load_current_a,
                )
            )
            phases = phase_currents(
                PhaseCurrentsInput(
                    rated_current_a=motor_current.value_a,
                    rated_torque_nm=freq.rated_torque_nm,
                    no_load_ratio=no_load.value,
                    steady_torque_nm=requirement.steady_torque_nm,
                    accel_torque_nm=requirement.required_torque_nm,
                    motors_count=request.duty_cycle.travel.motors_count,
                )
            )
            decel_current_a = (
                current_of_torque(
                    CurrentOfTorqueInput(
                        rated_current_a=motor_current.value_a,
                        rated_torque_nm=freq.rated_torque_nm,
                        torque_nm=requirement.decel_torque.value_nm,
                        no_load_ratio=no_load.value,
                    )
                ).value_a
                * request.duty_cycle.travel.motors_count
            )

            i_rms = rms_current(
                ThermalRmsInput(
                    accel_value=phases.accel_current_a,
                    steady_value=phases.steady_current_a,
                    decel_value=decel_current_a,
                    accel_time_s=requirement.profile.accel_time_s,
                    const_time_s=requirement.profile.const_time_s,
                    decel_time_s=requirement.profile.decel_time_s,
                    off_time_s=requirement.regime.off_time_s,
                    cooling_factor=request.duty_cycle.cooling_factor,
                )
            )
            rms_current_a = i_rms.value

            drive_validation = validate_drive_candidate(
                DriveValidationInput(
                    accel_current_a=phases.accel_current_a,
                    steady_current_a=phases.steady_current_a,
                    required_rms_current_a=i_rms.value,
                    rated_current_a=request.drive.rated_current_a,
                    overload_factor=request.drive.overload_factor,
                    policy=request.drive_sizing_policy,
                )
            )

        return ValidateCandidateResult(
            requirement=requirement,
            resolved_motor=resolved_motor,
            motor_validation=motor_validation,
            drive_validation=drive_validation,
            rms_current_a=rms_current_a,
        )
