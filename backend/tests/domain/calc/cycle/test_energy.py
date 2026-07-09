"""Physics tests for CYCLE.ENERGY.v1 — signed energy, regenerative phases."""

from app.domain.calc.cycle.energy import EnergyCycleInput, energy_per_cycle


def test_energy_per_cycle_all_motoring_phases():
    """T_acc=10.68, T_ss=4.12, T_dec=2.44 N*m (all positive: no regeneration),
    omega_nominal=63.49158752904972 rad/s (from N_c=606.3 rpm), eta=0.9,
    starts_per_hour=40.91."""
    result = energy_per_cycle(
        EnergyCycleInput(
            accel_torque_nm=10.68,
            accel_time_s=2.0,
            steady_torque_nm=4.12,
            const_time_s=18.0,
            decel_torque_nm=2.44,
            decel_time_s=2.0,
            nominal_angular_velocity_rad_s=63.49158752904972,
            efficiency=0.9,
            starts_per_hour=40.91,
        )
    )
    assert result.has_regenerative_phase is False
    assert result.energy_per_cycle_j == 6157.27
    assert result.energy_per_hour_j == 251893.92
    assert result.formula_id == "CYCLE.ENERGY.v1"
    assert all(not p.is_regenerative for p in result.phases)


def test_energy_per_cycle_regenerative_deceleration_preserves_sign():
    """Deceleration torque is negative (regenerative): its energy contribution
    is negative and reduces the net cycle energy, without using abs()."""
    result = energy_per_cycle(
        EnergyCycleInput(
            accel_torque_nm=5.0,
            accel_time_s=2.0,
            steady_torque_nm=3.0,
            const_time_s=10.0,
            decel_torque_nm=-2.0,
            decel_time_s=2.0,
            nominal_angular_velocity_rad_s=50.0,
            efficiency=0.9,
            starts_per_hour=20.0,
        )
    )
    assert result.has_regenerative_phase is True
    decel_phase = next(p for p in result.phases if p.label == "Deceleration")
    assert decel_phase.is_regenerative is True
    assert decel_phase.energy_j == -90.0
    assert result.energy_per_cycle_j == 1854.45
    assert result.energy_per_hour_j == 37089.0

    # Sign preserved: net energy is less than the sum of the magnitudes of the
    # motoring phases alone (the regenerative phase offsets consumption).
    motoring_only = sum(
        p.energy_j for p in result.phases if not p.is_regenerative
    )
    assert result.energy_per_cycle_j < motoring_only
