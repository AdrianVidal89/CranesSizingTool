"""Physics tests for CYCLE.PROFILE.v1 — trapezoidal and triangular cases."""

import pytest

from app.domain.calc.cycle.profile import MotionProfileInput, motion_profile


def test_trapezoidal_profile():
    """distance=10m, v=0.5 m/s, t_a=t_d=2s: reaches nominal speed (d_a+d_d=1m < 10m)."""
    result = motion_profile(
        MotionProfileInput(
            distance_m=10.0, velocity_ms=0.5, accel_time_s=2.0, decel_time_s=2.0
        )
    )
    assert result.is_triangular is False
    assert result.accel_time_s == 2.0
    assert result.const_time_s == 18.0
    assert result.decel_time_s == 2.0
    assert result.accel_distance_m == 0.5
    assert result.const_distance_m == 9.0
    assert result.decel_distance_m == 0.5
    assert result.peak_velocity_ms == 0.5
    assert result.formula_id == "CYCLE.PROFILE.v1"


def test_triangular_profile_degeneration():
    """distance=0.4m is shorter than d_a+d_d=1.0m: never reaches nominal speed."""
    result = motion_profile(
        MotionProfileInput(
            distance_m=0.4, velocity_ms=0.5, accel_time_s=2.0, decel_time_s=2.0
        )
    )
    assert result.is_triangular is True
    assert result.accel_time_s == 1.2649
    assert result.decel_time_s == 1.2649
    assert result.const_time_s == 0.0
    assert result.peak_velocity_ms == 0.3162
    assert result.peak_velocity_ms < 0.5, "must not reach the nominal velocity"
    assert result.accel_distance_m == 0.2
    assert result.decel_distance_m == 0.2
    assert result.const_distance_m == 0.0


def test_decel_time_defaults_to_accel_time():
    result = motion_profile(
        MotionProfileInput(distance_m=10.0, velocity_ms=0.5, accel_time_s=2.0)
    )
    assert result.decel_time_s == 2.0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"distance_m": 0, "velocity_ms": 0.5, "accel_time_s": 2.0},
        {"distance_m": 10.0, "velocity_ms": 0, "accel_time_s": 2.0},
        {"distance_m": 10.0, "velocity_ms": 0.5, "accel_time_s": 0},
        {"distance_m": 10.0, "velocity_ms": 0.5, "accel_time_s": 2.0, "decel_time_s": 0},
    ],
)
def test_invalid_inputs_raise(kwargs):
    with pytest.raises(ValueError):
        MotionProfileInput(**kwargs)
