"""Physics tests for MOTOR.VALIDATE.* — Module 5.5 conditions.

Requirement numbers reused from the Phase 1/2 worked example:
T_acc=10.68 N*m, N_c=606.3 rpm, T_rms=3.1495 N*m.

Candidate: a generic, invented 2.2 kW motor (not any real manufacturer's
nameplate) at 50 Hz, breakdown_torque_pu=2.5, max_mechanical_torque_pu=3.0.
"""

from app.domain.calc.motor.validation import (
    BreakdownTorqueCheckInput,
    MechTorqueCheckInput,
    MotorValidationInput,
    SpeedBandCheckInput,
    ThermalTorqueCheckInput,
    check_breakdown_torque,
    check_mechanical_torque,
    check_speed_band,
    check_thermal_torque,
    validate_motor_candidate,
)
from app.domain.standards.motor_sizing_policy import DEFAULT_MOTOR_SIZING_POLICY

REQUIRED_TORQUE_NM = 10.68
REQUIRED_SPEED_RPM = 606.3
REQUIRED_RMS_TORQUE_NM = 3.1495


def test_all_conditions_pass():
    """rated_speed_rpm=750 puts N_c comfortably inside the speed band
    (0.75*750=562.5 < 606.3 < 750), and the breakdown/max-mechanical torques
    (pu=2.5/3.0 on T_r=28.011) clear T_acc with margin."""
    result = validate_motor_candidate(
        MotorValidationInput(
            required_torque_nm=REQUIRED_TORQUE_NM,
            required_speed_rpm=REQUIRED_SPEED_RPM,
            required_rms_torque_nm=REQUIRED_RMS_TORQUE_NM,
            rated_torque_nm=28.011,
            rated_speed_rpm=750.0,
            max_mechanical_torque_nm=84.034,
            breakdown_torque_nm=70.028,
            policy=DEFAULT_MOTOR_SIZING_POLICY,
        )
    )
    assert result.passed is True
    assert all(c.verdict == "pass" for c in result.conditions)
    assert len(result.conditions) == 4


def test_fails_on_breakdown_torque_margin():
    """Same passing candidate, but with an (invented, unrealistically low)
    breakdown_torque_pu=0.4 -> T_st=11.205, /1.2=9.337 < T_acc=10.68."""
    result = check_breakdown_torque(
        BreakdownTorqueCheckInput(
            required_torque_nm=REQUIRED_TORQUE_NM,
            breakdown_torque_nm=11.205,
            policy=DEFAULT_MOTOR_SIZING_POLICY,
        )
    )
    assert result.verdict == "fail"
    assert result.available_value == 9.338
    assert result.margin < 0

    full = validate_motor_candidate(
        MotorValidationInput(
            required_torque_nm=REQUIRED_TORQUE_NM,
            required_speed_rpm=REQUIRED_SPEED_RPM,
            required_rms_torque_nm=REQUIRED_RMS_TORQUE_NM,
            rated_torque_nm=28.011,
            rated_speed_rpm=750.0,
            max_mechanical_torque_nm=84.034,
            breakdown_torque_nm=11.205,
            policy=DEFAULT_MOTOR_SIZING_POLICY,
        )
    )
    assert full.passed is False
    breakdown_condition = next(
        c for c in full.conditions if c.formula_id == "MOTOR.VALIDATE.BreakdownTorque.v1"
    )
    assert breakdown_condition.verdict == "fail"
    # The other 3 conditions are unaffected by this candidate's breakdown torque.
    other_conditions = [c for c in full.conditions if c is not breakdown_condition]
    assert all(c.verdict == "pass" for c in other_conditions)


def test_fails_on_speed_band():
    """A 1450 rpm rated speed is far above the 606.3 rpm requirement: N_c is
    below 0.75*N_r=1087.5, so the motor is oversized on speed."""
    result = check_speed_band(
        SpeedBandCheckInput(
            required_speed_rpm=REQUIRED_SPEED_RPM,
            rated_speed_rpm=1450.0,
            policy=DEFAULT_MOTOR_SIZING_POLICY,
        )
    )
    assert result.verdict == "fail"

    full = validate_motor_candidate(
        MotorValidationInput(
            required_torque_nm=REQUIRED_TORQUE_NM,
            required_speed_rpm=REQUIRED_SPEED_RPM,
            required_rms_torque_nm=REQUIRED_RMS_TORQUE_NM,
            rated_torque_nm=14.489,
            rated_speed_rpm=1450.0,
            max_mechanical_torque_nm=43.466,
            breakdown_torque_nm=36.221,
            policy=DEFAULT_MOTOR_SIZING_POLICY,
        )
    )
    assert full.passed is False
    speed_condition = next(c for c in full.conditions if c.formula_id == "MOTOR.VALIDATE.Speed.v1")
    assert speed_condition.verdict == "fail"
    other_conditions = [c for c in full.conditions if c is not speed_condition]
    assert all(c.verdict == "pass" for c in other_conditions)


def test_mechanical_torque_condition_isolated():
    result = check_mechanical_torque(
        MechTorqueCheckInput(
            required_torque_nm=REQUIRED_TORQUE_NM, max_mechanical_torque_nm=84.034
        )
    )
    assert result.verdict == "pass"
    assert result.formula_id == "MOTOR.VALIDATE.MechTorque.v1"


def test_thermal_torque_condition_isolated():
    result = check_thermal_torque(
        ThermalTorqueCheckInput(
            required_rms_torque_nm=REQUIRED_RMS_TORQUE_NM,
            rated_torque_nm=28.011,
            policy=DEFAULT_MOTOR_SIZING_POLICY,
        )
    )
    assert result.verdict == "pass"
    assert result.required_value == round(0.9 * REQUIRED_RMS_TORQUE_NM, 3)
