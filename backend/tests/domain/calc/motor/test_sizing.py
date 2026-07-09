"""Physics tests for MOTOR.FREQ_CONVERT.v1, MOTOR.Ir.v1, MOTOR.FIELD_WEAKENING.v1."""

import pytest

from app.domain.calc.motor.sizing import (
    FieldWeakeningInput,
    FrequencyConversionInput,
    RatedCurrentInput,
    convert_frequency,
    field_weakening_torque,
    rated_current,
)


def test_frequency_conversion_identity_when_same_frequency():
    """No conversion needed: ratio=1, values pass through, T_r computed directly."""
    result = convert_frequency(
        FrequencyConversionInput(
            rated_power_kw=2.2,
            rated_speed_rpm=750.0,
            nameplate_frequency_hz=50.0,
            target_frequency_hz=50.0,
        )
    )
    assert result.rated_power_kw == 2.2
    assert result.rated_speed_rpm == 750.0
    assert result.rated_torque_nm == 28.011
    assert result.formula_id == "MOTOR.FREQ_CONVERT.v1"


def test_frequency_conversion_50_to_60hz_preserves_torque():
    """50->60 Hz: power and speed scale by 1.2, but rated torque is invariant
    (both P and N in T=P/omega scale by the same ratio)."""
    result = convert_frequency(
        FrequencyConversionInput(
            rated_power_kw=2.2,
            rated_speed_rpm=1450.0,
            nameplate_frequency_hz=50.0,
            target_frequency_hz=60.0,
        )
    )
    assert result.rated_power_kw == 2.64
    assert result.rated_speed_rpm == 1740.0
    assert result.rated_torque_nm == 14.489


def test_rated_current():
    result = rated_current(
        RatedCurrentInput(
            rated_power_kw=2.2, rated_voltage_v=400.0, efficiency=0.87, power_factor=0.85
        )
    )
    assert result.value_a == 4.294
    assert result.formula_id == "MOTOR.Ir.v1"


def test_field_weakening_reduces_torque_above_base_speed():
    result = field_weakening_torque(
        FieldWeakeningInput(
            breakdown_torque_nm=70.028, rated_speed_rpm=750.0, operating_speed_rpm=1500.0
        )
    )
    # At double the base speed, torque falls by (1/2)^2 = 0.25
    assert result.value_nm == round(70.028 * 0.25, 3)
    assert result.value_nm < 70.028
    assert result.formula_id == "MOTOR.FIELD_WEAKENING.v1"


def test_field_weakening_at_base_speed_is_unchanged():
    result = field_weakening_torque(
        FieldWeakeningInput(
            breakdown_torque_nm=70.028, rated_speed_rpm=750.0, operating_speed_rpm=750.0
        )
    )
    assert result.value_nm == 70.028


def test_field_weakening_rejects_speed_below_base():
    with pytest.raises(ValueError):
        FieldWeakeningInput(
            breakdown_torque_nm=70.028, rated_speed_rpm=750.0, operating_speed_rpm=600.0
        )
