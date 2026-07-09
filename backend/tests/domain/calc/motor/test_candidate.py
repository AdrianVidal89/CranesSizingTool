"""MotorCandidate typed-field validation (no ">=7" heuristic)."""

import pytest

from app.domain.calc.motor.candidate import MotorCandidate, resolve_absolute_torque_nm

BASE_KWARGS = dict(
    rated_power_kw=2.2,
    rated_speed_rpm=750.0,
    rated_voltage_v=400.0,
    power_factor=0.85,
    efficiency=0.87,
    nameplate_frequency_hz=50.0,
)


def test_valid_candidate_with_pu_fields():
    candidate = MotorCandidate(
        **BASE_KWARGS,
        breakdown_torque_pu=2.5,
        max_mechanical_torque_pu=3.0,
    )
    assert candidate.breakdown_torque_pu == 2.5


def test_valid_candidate_with_absolute_fields():
    candidate = MotorCandidate(
        **BASE_KWARGS,
        breakdown_torque_nm=70.0,
        max_mechanical_torque_nm=84.0,
    )
    assert candidate.breakdown_torque_nm == 70.0


@pytest.mark.parametrize(
    "overrides",
    [
        dict(breakdown_torque_pu=2.5, breakdown_torque_nm=70.0),  # both
        dict(breakdown_torque_pu=None, breakdown_torque_nm=None),  # neither
    ],
)
def test_rejects_ambiguous_breakdown_torque(overrides):
    with pytest.raises(ValueError, match="Exactly one of"):
        MotorCandidate(**BASE_KWARGS, max_mechanical_torque_pu=3.0, **overrides)


def test_rejects_ambiguous_max_mechanical_torque():
    with pytest.raises(ValueError, match="Exactly one of"):
        MotorCandidate(
            **BASE_KWARGS,
            breakdown_torque_pu=2.5,
            max_mechanical_torque_pu=3.0,
            max_mechanical_torque_nm=84.0,
        )


def test_resolve_absolute_torque_from_pu():
    assert resolve_absolute_torque_nm(2.5, None, rated_torque_nm=28.011) == 70.0275


def test_resolve_absolute_torque_from_absolute():
    assert resolve_absolute_torque_nm(None, 70.0, rated_torque_nm=28.011) == 70.0
