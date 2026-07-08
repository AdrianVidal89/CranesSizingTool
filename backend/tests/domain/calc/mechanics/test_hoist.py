"""Physics tests for MECH.HOIST formulas — source of truth for the mechanics.

Worked example (constructed, no numeric example in the original inventory):
hook load m_h = m_load(5000 kg) + m_tool(200 kg) = 5200 kg, D_w=0.4 m drum,
s=2 reeving factor, i=25 gear ratio, eta=0.92, v=0.2 m/s hoist speed,
t_r=1.5 s ramp, J_motor=0.05 kg*m^2, J_brake=0.01 kg*m^2. Expected values
below are hand-derived and cross-checked independently of the implementation.

The load-inertia case (test_load_dynamic_torque) additionally documents the
physics correction from FORMULA_INVENTORY.md 2.4: the original code's inertia
model gives J=0.0416 kg*m^2 for this example, versus the physically correct
J=0.0832 kg*m^2 computed here — a 2x underestimation.
"""

from app.domain.calc.mechanics.hoist import (
    HoistLoadDynamicTorqueInput,
    HoistRotorDynamicTorqueInput,
    HoistSpeedInput,
    HoistStaticTorqueInput,
    load_dynamic_torque,
    required_motor_speed,
    rotor_dynamic_torque,
    static_hoisting_torque,
    total_acceleration_torque,
)

HOOK_LOAD_MASS_KG = 5200.0
DRUM_DIAMETER_M = 0.4
REEVING_FACTOR = 2.0
GEAR_RATIO = 25.0
EFFICIENCY = 0.92
VELOCITY_MS = 0.2
ACCEL_TIME_S = 1.5
MOTOR_INERTIA_KGM2 = 0.05
BRAKE_INERTIA_KGM2 = 0.01
MOTOR_SPEED_RPM = 477.46  # MECH.HOIST.Nc.v1 output for this example


def test_static_hoisting_torque_lifting():
    result = static_hoisting_torque(
        HoistStaticTorqueInput(
            hook_load_mass_kg=HOOK_LOAD_MASS_KG,
            drum_diameter_m=DRUM_DIAMETER_M,
            reeving_factor=REEVING_FACTOR,
            gear_ratio=GEAR_RATIO,
            efficiency=EFFICIENCY,
            direction="lifting",
        )
    )
    assert result.value_nm == 221.72
    assert result.formula_id == "MECH.HOIST.Tss.v1"


def test_static_hoisting_torque_lowering():
    result = static_hoisting_torque(
        HoistStaticTorqueInput(
            hook_load_mass_kg=HOOK_LOAD_MASS_KG,
            drum_diameter_m=DRUM_DIAMETER_M,
            reeving_factor=REEVING_FACTOR,
            gear_ratio=GEAR_RATIO,
            efficiency=EFFICIENCY,
            direction="lowering",
        )
    )
    assert result.value_nm == 187.66
    assert result.value_nm < 221.72, "lowering must require less torque than lifting"


def test_required_motor_speed():
    result = required_motor_speed(
        HoistSpeedInput(
            velocity_ms=VELOCITY_MS,
            drum_diameter_m=DRUM_DIAMETER_M,
            reeving_factor=REEVING_FACTOR,
            gear_ratio=GEAR_RATIO,
        )
    )
    assert result.value_rpm == 477.46
    assert result.formula_id == "MECH.HOIST.Nc.v1"


def test_rotor_dynamic_torque():
    result = rotor_dynamic_torque(
        HoistRotorDynamicTorqueInput(
            motor_inertia_kgm2=MOTOR_INERTIA_KGM2,
            brake_inertia_kgm2=BRAKE_INERTIA_KGM2,
            motor_speed_rpm=MOTOR_SPEED_RPM,
            accel_time_s=ACCEL_TIME_S,
        )
    )
    assert result.value_nm == 2.0
    assert result.formula_id == "MECH.HOIST.Tdyn_rotor.v1"


def test_load_dynamic_torque_uses_corrected_inertia():
    result = load_dynamic_torque(
        HoistLoadDynamicTorqueInput(
            hook_load_mass_kg=HOOK_LOAD_MASS_KG,
            drum_diameter_m=DRUM_DIAMETER_M,
            reeving_factor=REEVING_FACTOR,
            gear_ratio=GEAR_RATIO,
            motor_speed_rpm=MOTOR_SPEED_RPM,
            accel_time_s=ACCEL_TIME_S,
        )
    )
    assert result.reflected_inertia_kgm2 == 0.0832
    assert result.value_nm == 2.7733
    assert result.formula_id == "MECH.HOIST.Tdyn_load.v1"

    # The original (incorrect) formula for this example gives J=0.0416 kg*m^2 —
    # half the physically correct value, because it used a solid-cylinder shape
    # factor and was missing the reeving factor s^2 (FORMULA_INVENTORY.md 2.4).
    original_incorrect_j = 0.25 * 0.5 * HOOK_LOAD_MASS_KG * (DRUM_DIAMETER_M / 2) ** 2 / GEAR_RATIO**2
    assert result.reflected_inertia_kgm2 > original_incorrect_j * 1.9


def test_total_acceleration_torque():
    static = static_hoisting_torque(
        HoistStaticTorqueInput(
            hook_load_mass_kg=HOOK_LOAD_MASS_KG,
            drum_diameter_m=DRUM_DIAMETER_M,
            reeving_factor=REEVING_FACTOR,
            gear_ratio=GEAR_RATIO,
            efficiency=EFFICIENCY,
            direction="lifting",
        )
    )
    rotor_dynamic = rotor_dynamic_torque(
        HoistRotorDynamicTorqueInput(
            motor_inertia_kgm2=MOTOR_INERTIA_KGM2,
            brake_inertia_kgm2=BRAKE_INERTIA_KGM2,
            motor_speed_rpm=MOTOR_SPEED_RPM,
            accel_time_s=ACCEL_TIME_S,
        )
    )
    load_dynamic = load_dynamic_torque(
        HoistLoadDynamicTorqueInput(
            hook_load_mass_kg=HOOK_LOAD_MASS_KG,
            drum_diameter_m=DRUM_DIAMETER_M,
            reeving_factor=REEVING_FACTOR,
            gear_ratio=GEAR_RATIO,
            motor_speed_rpm=MOTOR_SPEED_RPM,
            accel_time_s=ACCEL_TIME_S,
        )
    )
    result = total_acceleration_torque(static, rotor_dynamic, load_dynamic)
    assert result.value_nm == 226.49
    assert result.formula_id == "MECH.HOIST.Tacc.v1"
