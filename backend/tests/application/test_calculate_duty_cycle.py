"""Integration tests for CalculateDutyCycle: mechanics (Phase 1) + cycle
formulas (Phase 2) composed end-to-end.
"""

from app.application.calculate_duty_cycle import (
    CalculateDutyCycle,
    CalculateDutyCycleRequest,
)
from app.application.calculate_travel_requirement import TravelRequirementRequest

BASE_TRAVEL = dict(
    mass_dead_kg=800.0,
    mass_load_kg=5000.0,
    mass_tool_kg=200.0,
    wheel_diameter_m=0.315,
    gear_ratio=20.0,
    efficiency=0.9,
    motors_count=2,
    rolling_coeff=0.016,
)


def test_trapezoidal_profile_with_duty_factor_pct():
    """distance=10m reaches nominal speed; %ED=25 target; not regenerative."""
    result = CalculateDutyCycle().execute(
        CalculateDutyCycleRequest(
            travel=TravelRequirementRequest(
                **BASE_TRAVEL, velocity_ms=0.5, accel_time_s=2.0
            ),
            distance_m=10.0,
            decel_time_s=None,
            duty_factor_pct=25.0,
            starts_per_hour=None,
            cooling_factor=0.5,
            mechanism_group=None,
        )
    )

    assert result.required_torque_nm == 10.68
    assert result.required_speed_rpm == 606.3
    assert result.steady_torque_nm == 4.12
    assert result.dynamic_torque_nm == 6.56

    assert result.profile.is_triangular is False
    assert result.profile.accel_time_s == 2.0
    assert result.profile.const_time_s == 18.0

    assert result.regime.off_time_s == 66.0
    assert result.regime.starts_per_hour == 40.91

    assert result.decel_torque.value_nm == 2.44
    assert result.decel_torque.is_regenerative is False

    assert result.rms_torque.value == 3.1495

    assert result.energy.energy_per_cycle_j == 6157.27
    assert result.energy.energy_per_hour_j == 251893.92
    assert result.energy.has_regenerative_phase is False

    assert result.mechanism_group_check.status == "not_available"
    assert result.mechanism_group_check.mechanism_group is None


def test_triangular_profile_degeneration_through_full_pipeline():
    """distance=0.4m never reaches nominal speed: profile degenerates to
    triangular and the rest of the pipeline still assembles correctly."""
    result = CalculateDutyCycle().execute(
        CalculateDutyCycleRequest(
            travel=TravelRequirementRequest(
                **BASE_TRAVEL, velocity_ms=0.5, accel_time_s=2.0
            ),
            distance_m=0.4,
            decel_time_s=None,
            duty_factor_pct=25.0,
            starts_per_hour=None,
            cooling_factor=0.5,
            mechanism_group=None,
        )
    )

    assert result.profile.is_triangular is True
    assert result.profile.accel_time_s == 1.2649
    assert result.profile.decel_time_s == 1.2649
    assert result.profile.const_time_s == 0.0
    assert result.profile.peak_velocity_ms == 0.3162
    assert result.rms_torque.value == 4.8993


def test_starts_per_hour_as_duty_regime_input():
    """Same mechanics/profile as the %ED case, but the duty regime is given
    as starts/hour=30 instead of a target %ED."""
    result = CalculateDutyCycle().execute(
        CalculateDutyCycleRequest(
            travel=TravelRequirementRequest(
                **BASE_TRAVEL, velocity_ms=0.5, accel_time_s=2.0
            ),
            distance_m=10.0,
            decel_time_s=None,
            duty_factor_pct=None,
            starts_per_hour=30.0,
            cooling_factor=0.5,
            mechanism_group=None,
        )
    )

    assert result.regime.starts_per_hour == 30.0
    assert result.regime.off_time_s == 98.0
    assert result.regime.duty_factor_pct == 18.33
    assert result.rms_torque.value == 2.772
    assert result.energy.energy_per_hour_j == 184718.1


def test_regenerative_deceleration_through_full_pipeline():
    """A gentle ramp (v=0.1 m/s, t_r=1s) makes Tdyn < Tss, so the
    deceleration phase is regenerative — the whole pipeline must reflect
    this without ever taking abs()."""
    result = CalculateDutyCycle().execute(
        CalculateDutyCycleRequest(
            travel=TravelRequirementRequest(
                **BASE_TRAVEL, velocity_ms=0.1, accel_time_s=1.0
            ),
            distance_m=10.0,
            decel_time_s=None,
            duty_factor_pct=25.0,
            starts_per_hour=None,
            cooling_factor=0.5,
            mechanism_group=None,
        )
    )

    assert result.decel_torque.value_nm == -1.5
    assert result.decel_torque.is_regenerative is True
    assert result.energy.has_regenerative_phase is True

    decel_phase = next(p for p in result.energy.phases if p.label == "Deceleration")
    assert decel_phase.is_regenerative is True
    assert decel_phase.energy_j < 0

    assert result.rms_torque.value == 2.6161
    assert result.energy.energy_per_cycle_j == 5793.86


def test_mechanism_group_check_is_todo_when_group_declared():
    result = CalculateDutyCycle().execute(
        CalculateDutyCycleRequest(
            travel=TravelRequirementRequest(
                **BASE_TRAVEL, velocity_ms=0.5, accel_time_s=2.0
            ),
            distance_m=10.0,
            decel_time_s=None,
            duty_factor_pct=25.0,
            starts_per_hour=None,
            cooling_factor=0.5,
            mechanism_group="M5",
        )
    )
    assert result.mechanism_group_check.status == "not_available"
    assert result.mechanism_group_check.mechanism_group == "M5"
    assert "TODO" in result.mechanism_group_check.note
