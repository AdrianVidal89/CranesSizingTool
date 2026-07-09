"""DriveCandidate validation."""

import pytest

from app.domain.calc.drive.candidate import DriveCandidate


def test_valid_candidate():
    candidate = DriveCandidate(
        rated_current_a=6.0, overload_factor=1.6, overload_duration_s=60.0, rated_voltage_v=400.0
    )
    assert candidate.overload_factor == 1.6


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(rated_current_a=0, overload_factor=1.6, overload_duration_s=60.0, rated_voltage_v=400.0),
        dict(rated_current_a=6.0, overload_factor=0.9, overload_duration_s=60.0, rated_voltage_v=400.0),
        dict(rated_current_a=6.0, overload_factor=1.6, overload_duration_s=0, rated_voltage_v=400.0),
        dict(rated_current_a=6.0, overload_factor=1.6, overload_duration_s=60.0, rated_voltage_v=0),
    ],
)
def test_invalid_inputs_raise(kwargs):
    with pytest.raises(ValueError):
        DriveCandidate(**kwargs)
