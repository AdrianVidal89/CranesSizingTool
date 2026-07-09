"""Physics tests for DRIVE.VALIDATE.* — Module 6.4 conditions.

Currents reused from test_sizing.py's example: I_ss=3.224, I_acc=4.29 A
(2 motors). I_rms=2.1014 A (from CYCLE.Irms.v1 with the Phase 2 phase
timing). Candidate: rated_current_a=6.0 A, overload_factor=1.6 (generic
invented values).
"""

from app.domain.calc.drive.validation import (
    ContinuousCheckInput,
    DriveValidationInput,
    OverloadCheckInput,
    check_continuous,
    check_overload,
    validate_drive_candidate,
)
from app.domain.standards.drive_sizing_policy import DEFAULT_DRIVE_SIZING_POLICY

STEADY_CURRENT_A = 3.224
ACCEL_CURRENT_A = 4.29
RMS_CURRENT_A = 2.1014
RATED_CURRENT_A = 6.0
OVERLOAD_FACTOR = 1.6


def test_all_conditions_pass():
    result = validate_drive_candidate(
        DriveValidationInput(
            accel_current_a=ACCEL_CURRENT_A,
            steady_current_a=STEADY_CURRENT_A,
            required_rms_current_a=RMS_CURRENT_A,
            rated_current_a=RATED_CURRENT_A,
            overload_factor=OVERLOAD_FACTOR,
            policy=DEFAULT_DRIVE_SIZING_POLICY,
        )
    )
    assert result.passed is True
    assert len(result.conditions) == 3
    assert all(c.verdict == "pass" for c in result.conditions)


def test_overload_condition_fails_for_undersized_drive():
    result = check_overload(
        OverloadCheckInput(
            accel_current_a=ACCEL_CURRENT_A, rated_current_a=2.0, overload_factor=OVERLOAD_FACTOR
        )
    )
    # available = 2.0*1.6=3.2 < I_acc=4.29
    assert result.verdict == "fail"
    assert result.available_value == 3.2


def test_continuous_condition_fails_for_undersized_drive():
    result = check_continuous(
        ContinuousCheckInput(steady_current_a=STEADY_CURRENT_A, rated_current_a=3.0)
    )
    assert result.verdict == "fail"


def test_thermal_condition_uses_policy_margin():
    result = validate_drive_candidate(
        DriveValidationInput(
            accel_current_a=ACCEL_CURRENT_A,
            steady_current_a=STEADY_CURRENT_A,
            required_rms_current_a=RMS_CURRENT_A,
            rated_current_a=RATED_CURRENT_A,
            overload_factor=OVERLOAD_FACTOR,
            policy=DEFAULT_DRIVE_SIZING_POLICY,
        )
    )
    thermal = next(c for c in result.conditions if c.formula_id == "DRIVE.VALIDATE.Thermal.v1")
    assert thermal.required_value == round(0.9 * RMS_CURRENT_A, 3)
    assert thermal.verdict == "pass"
