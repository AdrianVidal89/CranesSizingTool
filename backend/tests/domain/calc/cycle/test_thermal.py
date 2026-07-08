"""Physics tests for CYCLE.Trms.v1 / CYCLE.Irms.v1 — thermal RMS with cooling."""

import pytest

from app.domain.calc.cycle.thermal import ThermalRmsInput, rms_current, rms_torque


def test_rms_torque_with_standstill_cooling():
    """T_acc=10.68, T_ss=4.12, T_dec=2.44 N*m; t_a=2, t_c=18, t_d=2, t_off=66 s;
    k_f=0.5 (self-ventilated, half cooling at standstill)."""
    result = rms_torque(
        ThermalRmsInput(
            accel_value=10.68,
            steady_value=4.12,
            decel_value=2.44,
            accel_time_s=2.0,
            const_time_s=18.0,
            decel_time_s=2.0,
            off_time_s=66.0,
            cooling_factor=0.5,
        )
    )
    assert result.value == 3.1495
    assert result.formula_id == "CYCLE.Trms.v1"


def test_rms_torque_ignores_sign_of_regenerative_decel_value():
    """Squaring in the RMS means +2.44 and -2.44 give the same magnitude."""
    positive = rms_torque(
        ThermalRmsInput(
            accel_value=10.68,
            steady_value=4.12,
            decel_value=2.44,
            accel_time_s=2.0,
            const_time_s=18.0,
            decel_time_s=2.0,
            off_time_s=66.0,
            cooling_factor=0.5,
        )
    )
    negative = rms_torque(
        ThermalRmsInput(
            accel_value=10.68,
            steady_value=4.12,
            decel_value=-2.44,
            accel_time_s=2.0,
            const_time_s=18.0,
            decel_time_s=2.0,
            off_time_s=66.0,
            cooling_factor=0.5,
        )
    )
    assert positive.value == negative.value


def test_rms_current():
    """I_acc=25, I_ss=12, I_dec=8 A; same phase timing as the torque case."""
    result = rms_current(
        ThermalRmsInput(
            accel_value=25.0,
            steady_value=12.0,
            decel_value=8.0,
            accel_time_s=2.0,
            const_time_s=18.0,
            decel_time_s=2.0,
            off_time_s=66.0,
            cooling_factor=0.5,
        )
    )
    assert result.value == 8.496
    assert result.formula_id == "CYCLE.Irms.v1"


def test_full_cooling_reduces_rms_versus_no_cooling():
    """k_f=1 (full cooling) must give a lower RMS than k_f=0 (no cooling from rest)."""
    kwargs = dict(
        accel_value=10.68,
        steady_value=4.12,
        decel_value=2.44,
        accel_time_s=2.0,
        const_time_s=18.0,
        decel_time_s=2.0,
        off_time_s=66.0,
    )
    full_cooling = rms_torque(ThermalRmsInput(**kwargs, cooling_factor=1.0))
    no_cooling = rms_torque(ThermalRmsInput(**kwargs, cooling_factor=0.0))
    assert full_cooling.value < no_cooling.value


@pytest.mark.parametrize("cooling_factor", [-0.1, 1.1])
def test_rejects_out_of_range_cooling_factor(cooling_factor):
    with pytest.raises(ValueError):
        ThermalRmsInput(
            accel_value=1,
            steady_value=1,
            decel_value=1,
            accel_time_s=1,
            const_time_s=1,
            decel_time_s=1,
            off_time_s=1,
            cooling_factor=cooling_factor,
        )
