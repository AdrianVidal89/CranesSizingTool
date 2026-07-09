"""Physics tests for DRIVE.NoLoadRatio.v1, DRIVE.I_of_T.v1, DRIVE.PhaseCurrents.v1.

Requirement torque numbers reused from the Phase 1/2 example:
T_ss=4.12, T_acc=10.68, T_dec=2.44 N*m. Motor: I_r=4.294 A, T_r=28.011 N*m,
power_factor=0.85 (generic invented candidate, not a real nameplate).
"""

from app.domain.calc.drive.sizing import (
    CurrentOfTorqueInput,
    NoLoadCurrentRatioInput,
    PhaseCurrentsInput,
    current_of_torque,
    no_load_current_ratio,
    phase_currents,
)

RATED_CURRENT_A = 4.294
RATED_TORQUE_NM = 28.011
POWER_FACTOR = 0.85


def test_no_load_ratio_estimated_via_sinphi():
    """No nameplate I_0: i_o = sin(phi) = sqrt(1 - cos(phi)^2)."""
    result = no_load_current_ratio(
        NoLoadCurrentRatioInput(rated_current_a=RATED_CURRENT_A, power_factor=POWER_FACTOR)
    )
    assert result.value == 0.5268
    assert result.source == "estimated_sinphi"
    assert result.formula_id == "DRIVE.NoLoadRatio.v1"


def test_no_load_ratio_from_nameplate_differs_from_sinphi_estimate():
    """A nameplate I_0=1.5 A gives i_o=I_0/I_r, a different (and, per its own
    formula, equally correct) value from the sin(phi) estimate."""
    result = no_load_current_ratio(
        NoLoadCurrentRatioInput(
            rated_current_a=RATED_CURRENT_A, power_factor=POWER_FACTOR, no_load_current_a=1.5
        )
    )
    assert result.value == 0.3493
    assert result.source == "nameplate"

    estimated = no_load_current_ratio(
        NoLoadCurrentRatioInput(rated_current_a=RATED_CURRENT_A, power_factor=POWER_FACTOR)
    )
    assert result.value != estimated.value


def test_current_of_torque_endpoints():
    """I(0) = I_r*i_o = I_0, and I(T_r) = I_r (verifies the formula's
    boundary conditions from FORMULA_INVENTORY.md 6.1)."""
    i_o = 0.3493
    at_zero = current_of_torque(
        CurrentOfTorqueInput(
            rated_current_a=RATED_CURRENT_A,
            rated_torque_nm=RATED_TORQUE_NM,
            torque_nm=0.0,
            no_load_ratio=i_o,
        )
    )
    assert at_zero.value_a == round(RATED_CURRENT_A * i_o, 3)

    at_rated = current_of_torque(
        CurrentOfTorqueInput(
            rated_current_a=RATED_CURRENT_A,
            rated_torque_nm=RATED_TORQUE_NM,
            torque_nm=RATED_TORQUE_NM,
            no_load_ratio=i_o,
        )
    )
    assert at_rated.value_a == RATED_CURRENT_A


def test_phase_currents_doubled_for_two_motors():
    result = phase_currents(
        PhaseCurrentsInput(
            rated_current_a=RATED_CURRENT_A,
            rated_torque_nm=RATED_TORQUE_NM,
            no_load_ratio=0.3493,
            steady_torque_nm=4.12,
            accel_torque_nm=10.68,
            motors_count=2,
        )
    )
    assert result.steady_current_a == 3.224
    assert result.accel_current_a == 4.29
    assert result.formula_id == "DRIVE.PhaseCurrents.v1"
