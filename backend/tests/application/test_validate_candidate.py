"""Integration tests for ValidateCandidate: mechanics + cycle (Phases 1-2)
composed with motor/drive candidate validation (Phase 3), end to end.

Requirement inputs reused from the Phase 1/2 worked example. Motor/drive
candidates are generic, invented values (not any real manufacturer's
nameplate), annotated as such.
"""

from app.application.calculate_duty_cycle import CalculateDutyCycleRequest
from app.application.calculate_travel_requirement import TravelRequirementRequest
from app.application.validate_candidate import ValidateCandidate, ValidateCandidateRequest
from app.domain.calc.drive.candidate import DriveCandidate
from app.domain.calc.motor.candidate import MotorCandidate

TRAVEL = TravelRequirementRequest(
    mass_dead_kg=800.0,
    mass_load_kg=5000.0,
    mass_tool_kg=200.0,
    velocity_ms=0.5,
    accel_time_s=2.0,
    wheel_diameter_m=0.315,
    gear_ratio=20.0,
    efficiency=0.9,
    motors_count=2,
    rolling_coeff=0.016,
)

DUTY_CYCLE = CalculateDutyCycleRequest(
    travel=TRAVEL,
    distance_m=10.0,
    decel_time_s=None,
    duty_factor_pct=25.0,
    starts_per_hour=None,
    cooling_factor=0.5,
    mechanism_group=None,
)

# Generic invented candidate (not a real manufacturer's nameplate):
# 2.2 kW / 750 rpm / 400 V motor, breakdown_torque_pu=2.5, max_mechanical_pu=3.0.
PASSING_MOTOR = MotorCandidate(
    rated_power_kw=2.2,
    rated_speed_rpm=750.0,
    rated_voltage_v=400.0,
    power_factor=0.85,
    efficiency=0.87,
    nameplate_frequency_hz=50.0,
    breakdown_torque_pu=2.5,
    max_mechanical_torque_pu=3.0,
    no_load_current_a=1.5,
)

PASSING_DRIVE = DriveCandidate(
    rated_current_a=6.0, overload_factor=1.6, overload_duration_s=60.0, rated_voltage_v=400.0
)


def test_all_conditions_pass_motor_and_drive():
    result = ValidateCandidate().execute(
        ValidateCandidateRequest(
            duty_cycle=DUTY_CYCLE,
            motor=PASSING_MOTOR,
            motor_target_frequency_hz=50.0,
            drive=PASSING_DRIVE,
        )
    )

    assert result.resolved_motor.rated_torque_nm == 28.011
    assert result.resolved_motor.rated_current_a == 4.294

    assert result.motor_validation.passed is True
    assert len(result.motor_validation.conditions) == 4

    assert result.rms_current_a == 2.1014
    assert result.drive_validation is not None
    assert result.drive_validation.passed is True
    assert len(result.drive_validation.conditions) == 3

    # The requirement (Phases 1-2) is carried through untouched for display.
    assert result.requirement.required_torque_nm == 10.68
    assert result.requirement.rms_torque.value == 3.1495


def test_fails_on_breakdown_torque_margin():
    """(Invented) breakdown_torque_pu=0.4 is too low: T_st/1.2 < T_acc."""
    motor = MotorCandidate(
        rated_power_kw=2.2,
        rated_speed_rpm=750.0,
        rated_voltage_v=400.0,
        power_factor=0.85,
        efficiency=0.87,
        nameplate_frequency_hz=50.0,
        breakdown_torque_pu=0.4,
        max_mechanical_torque_pu=3.0,
    )
    result = ValidateCandidate().execute(
        ValidateCandidateRequest(
            duty_cycle=DUTY_CYCLE, motor=motor, motor_target_frequency_hz=50.0, drive=None
        )
    )
    assert result.motor_validation.passed is False
    breakdown = next(
        c
        for c in result.motor_validation.conditions
        if c.formula_id == "MOTOR.VALIDATE.BreakdownTorque.v1"
    )
    assert breakdown.verdict == "fail"
    assert breakdown.available_value == 9.337
    other = [c for c in result.motor_validation.conditions if c is not breakdown]
    assert all(c.verdict == "pass" for c in other)
    assert result.drive_validation is None
    assert result.rms_current_a is None


def test_fails_on_speed_band():
    """A 1450 rpm rated speed is far above the 606.3 rpm requirement:
    N_c < 0.75*N_r, so the motor is oversized on speed."""
    motor = MotorCandidate(
        rated_power_kw=2.2,
        rated_speed_rpm=1450.0,
        rated_voltage_v=400.0,
        power_factor=0.85,
        efficiency=0.87,
        nameplate_frequency_hz=50.0,
        breakdown_torque_pu=2.5,
        max_mechanical_torque_pu=3.0,
    )
    result = ValidateCandidate().execute(
        ValidateCandidateRequest(
            duty_cycle=DUTY_CYCLE, motor=motor, motor_target_frequency_hz=50.0, drive=None
        )
    )
    assert result.motor_validation.passed is False
    speed = next(
        c for c in result.motor_validation.conditions if c.formula_id == "MOTOR.VALIDATE.Speed.v1"
    )
    assert speed.verdict == "fail"
    other = [c for c in result.motor_validation.conditions if c is not speed]
    assert all(c.verdict == "pass" for c in other)


def test_frequency_conversion_scales_speed_current_not_torque():
    """A 50 Hz nameplate motor run at 60 Hz: speed/power/current scale up by
    1.2, but rated torque is invariant (see MOTOR.FREQ_CONVERT.v1)."""
    motor = MotorCandidate(
        rated_power_kw=2.2,
        rated_speed_rpm=1450.0,
        rated_voltage_v=400.0,
        power_factor=0.85,
        efficiency=0.87,
        nameplate_frequency_hz=50.0,
        breakdown_torque_pu=2.5,
        max_mechanical_torque_pu=3.0,
    )
    result = ValidateCandidate().execute(
        ValidateCandidateRequest(
            duty_cycle=DUTY_CYCLE, motor=motor, motor_target_frequency_hz=60.0, drive=None
        )
    )
    assert result.resolved_motor.rated_speed_rpm == 1740.0
    assert result.resolved_motor.rated_torque_nm == 14.489
    assert result.resolved_motor.rated_current_a == 5.153


def test_no_load_current_nameplate_vs_estimated_give_different_drive_currents():
    """Same requirement/motor/drive, only I_0 differs: nameplate I_0=1.5 A vs
    no I_0 given (estimated via sin(phi)). Both are individually correct per
    their own formula, but the resulting drive currents differ."""
    motor_with_nameplate_i0 = PASSING_MOTOR
    motor_without_i0 = MotorCandidate(
        rated_power_kw=2.2,
        rated_speed_rpm=750.0,
        rated_voltage_v=400.0,
        power_factor=0.85,
        efficiency=0.87,
        nameplate_frequency_hz=50.0,
        breakdown_torque_pu=2.5,
        max_mechanical_torque_pu=3.0,
        no_load_current_a=None,
    )

    result_nameplate = ValidateCandidate().execute(
        ValidateCandidateRequest(
            duty_cycle=DUTY_CYCLE,
            motor=motor_with_nameplate_i0,
            motor_target_frequency_hz=50.0,
            drive=PASSING_DRIVE,
        )
    )
    result_estimated = ValidateCandidate().execute(
        ValidateCandidateRequest(
            duty_cycle=DUTY_CYCLE,
            motor=motor_without_i0,
            motor_target_frequency_hz=50.0,
            drive=PASSING_DRIVE,
        )
    )

    assert result_nameplate.rms_current_a != result_estimated.rms_current_a
    assert result_nameplate.rms_current_a == 2.1014
    # Both scenarios still validate successfully; only the numbers differ.
    assert result_nameplate.drive_validation.passed is True
    assert result_estimated.drive_validation.passed is True
