"""Calculation endpoints — requirement stage (see CLAUDE.md business flow)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.application.calculate_duty_cycle import (
    CalculateDutyCycle,
    CalculateDutyCycleRequest,
)
from app.application.calculate_travel_requirement import (
    CalculateTravelRequirement,
    TravelRequirementRequest,
)
from app.application.validate_candidate import ValidateCandidate, ValidateCandidateRequest
from app.domain.calc.drive.candidate import DriveCandidate
from app.domain.calc.motor.candidate import MotorCandidate
from app.interfaces.schemas.duty_cycle import (
    DecelTorqueSchema,
    DutyCycleRequestSchema,
    DutyCycleResponseSchema,
    DutyRegimeSchema,
    EnergyCycleSchema,
    MechanismGroupCheckSchema,
    MotionProfileSchema,
    PhaseEnergySchema,
    ThermalRmsSchema,
)
from app.interfaces.schemas.travel import (
    FormulaOutputSchema,
    TravelRequirementRequestSchema,
    TravelRequirementResponseSchema,
)
from app.interfaces.schemas.validate_candidate import (
    ConditionResultSchema,
    ResolvedMotorSchema,
    ValidateCandidateRequestSchema,
    ValidateCandidateResponseSchema,
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
        steady_torque_nm=result.steady_torque_nm,
        dynamic_torque_nm=result.dynamic_torque_nm,
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


def _travel_request_from_payload(payload) -> TravelRequirementRequest:
    return TravelRequirementRequest(
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


def _duty_cycle_request_from_payload(payload) -> CalculateDutyCycleRequest:
    return CalculateDutyCycleRequest(
        travel=_travel_request_from_payload(payload),
        distance_m=payload.distance_m,
        decel_time_s=payload.decel_time_s,
        duty_factor_pct=payload.duty_factor_pct,
        starts_per_hour=payload.starts_per_hour,
        cooling_factor=payload.cooling_factor,
        mechanism_group=payload.mechanism_group,
    )


def _duty_cycle_response_from_result(result) -> DutyCycleResponseSchema:
    return DutyCycleResponseSchema(
        required_torque_nm=result.required_torque_nm,
        required_speed_rpm=result.required_speed_rpm,
        steady_torque_nm=result.steady_torque_nm,
        dynamic_torque_nm=result.dynamic_torque_nm,
        profile=MotionProfileSchema(
            accel_time_s=result.profile.accel_time_s,
            const_time_s=result.profile.const_time_s,
            decel_time_s=result.profile.decel_time_s,
            accel_distance_m=result.profile.accel_distance_m,
            const_distance_m=result.profile.const_distance_m,
            decel_distance_m=result.profile.decel_distance_m,
            peak_velocity_ms=result.profile.peak_velocity_ms,
            is_triangular=result.profile.is_triangular,
            formula_id=result.profile.formula_id,
            assumptions=result.profile.assumptions,
            standard_refs=result.profile.standard_refs,
        ),
        regime=DutyRegimeSchema(
            on_time_s=result.regime.on_time_s,
            off_time_s=result.regime.off_time_s,
            cycle_time_s=result.regime.cycle_time_s,
            duty_factor_pct=result.regime.duty_factor_pct,
            starts_per_hour=result.regime.starts_per_hour,
            formula_id=result.regime.formula_id,
            assumptions=result.regime.assumptions,
            standard_refs=result.regime.standard_refs,
        ),
        decel_torque=DecelTorqueSchema(
            value_nm=result.decel_torque.value_nm,
            is_regenerative=result.decel_torque.is_regenerative,
            formula_id=result.decel_torque.formula_id,
            assumptions=result.decel_torque.assumptions,
            standard_refs=result.decel_torque.standard_refs,
        ),
        rms_torque=ThermalRmsSchema(
            value=result.rms_torque.value,
            formula_id=result.rms_torque.formula_id,
            assumptions=result.rms_torque.assumptions,
            standard_refs=result.rms_torque.standard_refs,
        ),
        energy=EnergyCycleSchema(
            energy_per_cycle_j=result.energy.energy_per_cycle_j,
            energy_per_hour_j=result.energy.energy_per_hour_j,
            phases=tuple(
                PhaseEnergySchema(
                    label=p.label, energy_j=p.energy_j, is_regenerative=p.is_regenerative
                )
                for p in result.energy.phases
            ),
            has_regenerative_phase=result.energy.has_regenerative_phase,
            formula_id=result.energy.formula_id,
            assumptions=result.energy.assumptions,
            standard_refs=result.energy.standard_refs,
        ),
        mechanism_group_check=MechanismGroupCheckSchema(
            status=result.mechanism_group_check.status,
            mechanism_group=result.mechanism_group_check.mechanism_group,
            starts_per_hour_limit=result.mechanism_group_check.starts_per_hour_limit,
            note=result.mechanism_group_check.note,
        ),
    )


@router.post("/duty-cycle", response_model=DutyCycleResponseSchema)
def calculate_duty_cycle(payload: DutyCycleRequestSchema) -> DutyCycleResponseSchema:
    use_case = CalculateDutyCycle()
    request = _duty_cycle_request_from_payload(payload)

    try:
        result = use_case.execute(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return _duty_cycle_response_from_result(result)


@router.post("/validate-candidate", response_model=ValidateCandidateResponseSchema)
def validate_candidate(payload: ValidateCandidateRequestSchema) -> ValidateCandidateResponseSchema:
    use_case = ValidateCandidate()
    request = ValidateCandidateRequest(
        duty_cycle=_duty_cycle_request_from_payload(payload),
        motor=MotorCandidate(
            rated_power_kw=payload.motor.rated_power_kw,
            rated_speed_rpm=payload.motor.rated_speed_rpm,
            rated_voltage_v=payload.motor.rated_voltage_v,
            power_factor=payload.motor.power_factor,
            efficiency=payload.motor.efficiency,
            nameplate_frequency_hz=payload.motor.nameplate_frequency_hz,
            breakdown_torque_pu=payload.motor.breakdown_torque_pu,
            breakdown_torque_nm=payload.motor.breakdown_torque_nm,
            max_mechanical_torque_pu=payload.motor.max_mechanical_torque_pu,
            max_mechanical_torque_nm=payload.motor.max_mechanical_torque_nm,
            no_load_current_a=payload.motor.no_load_current_a,
            rotor_inertia_kgm2=payload.motor.rotor_inertia_kgm2,
        ),
        motor_target_frequency_hz=payload.motor_target_frequency_hz,
        drive=(
            DriveCandidate(
                rated_current_a=payload.drive.rated_current_a,
                overload_factor=payload.drive.overload_factor,
                overload_duration_s=payload.drive.overload_duration_s,
                rated_voltage_v=payload.drive.rated_voltage_v,
            )
            if payload.drive is not None
            else None
        ),
    )

    try:
        result = use_case.execute(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return ValidateCandidateResponseSchema(
        requirement=_duty_cycle_response_from_result(result.requirement),
        resolved_motor=ResolvedMotorSchema(
            rated_torque_nm=result.resolved_motor.rated_torque_nm,
            rated_speed_rpm=result.resolved_motor.rated_speed_rpm,
            rated_current_a=result.resolved_motor.rated_current_a,
            breakdown_torque_nm=result.resolved_motor.breakdown_torque_nm,
            max_mechanical_torque_nm=result.resolved_motor.max_mechanical_torque_nm,
        ),
        motor_conditions=tuple(
            _condition_result_to_schema(c) for c in result.motor_validation.conditions
        ),
        motor_passed=result.motor_validation.passed,
        drive_conditions=(
            tuple(_condition_result_to_schema(c) for c in result.drive_validation.conditions)
            if result.drive_validation is not None
            else None
        ),
        drive_passed=(
            result.drive_validation.passed if result.drive_validation is not None else None
        ),
        rms_current_a=result.rms_current_a,
    )


def _condition_result_to_schema(condition) -> ConditionResultSchema:
    return ConditionResultSchema(
        label=condition.label,
        verdict=condition.verdict,
        required_value=condition.required_value,
        available_value=condition.available_value,
        margin=condition.margin,
        formula_id=condition.formula_id,
        assumptions=condition.assumptions,
        standard_refs=condition.standard_refs,
    )
