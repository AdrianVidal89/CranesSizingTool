"""Physics tests for MECH.TRAVEL formulas — source of truth for the mechanics.

Worked example (constructed, no numeric example in the original inventory):
a trolley moving m_dead=800 kg dead weight + m_load=5000 kg SWL + m_tool=200 kg
spreader = 6000 kg total, mu=0.016 (steel wheel/rail, FEM 9.511 typical),
D_w=0.315 m wheel, i=20 gear ratio, eta=0.9, z=2 motors, v=0.5 m/s,
t_r=2 s ramp. Expected values below are hand-derived and cross-checked
independently of the implementation.
"""

from app.domain.calc.mechanics.travel import (
    RollingResistanceInput,
    TravelDynamicTorqueInput,
    TravelSpeedInput,
    TravelTorqueInput,
    dynamic_torque,
    required_motor_speed,
    rolling_resistance_force,
    steady_state_torque,
    total_acceleration_torque,
)

MASS_TOTAL_KG = 6000.0
ROLLING_COEFF = 0.016
WHEEL_DIAMETER_M = 0.315
GEAR_RATIO = 20.0
EFFICIENCY = 0.9
MOTORS_COUNT = 2
VELOCITY_MS = 0.5
ACCEL_TIME_S = 2.0


def test_rolling_resistance_force():
    result = rolling_resistance_force(
        RollingResistanceInput(mass_total_kg=MASS_TOTAL_KG, rolling_coeff=ROLLING_COEFF)
    )
    assert result.value_n == 941.44
    assert result.formula_id == "MECH.TRAVEL.Fr.v1"


def test_required_motor_speed():
    result = required_motor_speed(
        TravelSpeedInput(
            velocity_ms=VELOCITY_MS,
            wheel_diameter_m=WHEEL_DIAMETER_M,
            gear_ratio=GEAR_RATIO,
        )
    )
    assert result.value_rpm == 606.3
    assert result.formula_id == "MECH.TRAVEL.Nc.v1"


def test_steady_state_torque():
    result = steady_state_torque(
        TravelTorqueInput(
            mass_total_kg=MASS_TOTAL_KG,
            wheel_diameter_m=WHEEL_DIAMETER_M,
            gear_ratio=GEAR_RATIO,
            efficiency=EFFICIENCY,
            motors_count=MOTORS_COUNT,
            rolling_coeff=ROLLING_COEFF,
        )
    )
    assert result.value_nm == 4.12
    assert result.formula_id == "MECH.TRAVEL.Tss.v1"


def test_dynamic_torque():
    result = dynamic_torque(
        TravelDynamicTorqueInput(
            mass_total_kg=MASS_TOTAL_KG,
            velocity_ms=VELOCITY_MS,
            accel_time_s=ACCEL_TIME_S,
            wheel_diameter_m=WHEEL_DIAMETER_M,
            gear_ratio=GEAR_RATIO,
            efficiency=EFFICIENCY,
            motors_count=MOTORS_COUNT,
        )
    )
    assert result.value_nm == 6.56
    assert result.formula_id == "MECH.TRAVEL.Tdyn.v1"


def test_total_acceleration_torque():
    steady = steady_state_torque(
        TravelTorqueInput(
            mass_total_kg=MASS_TOTAL_KG,
            wheel_diameter_m=WHEEL_DIAMETER_M,
            gear_ratio=GEAR_RATIO,
            efficiency=EFFICIENCY,
            motors_count=MOTORS_COUNT,
            rolling_coeff=ROLLING_COEFF,
        )
    )
    dynamic = dynamic_torque(
        TravelDynamicTorqueInput(
            mass_total_kg=MASS_TOTAL_KG,
            velocity_ms=VELOCITY_MS,
            accel_time_s=ACCEL_TIME_S,
            wheel_diameter_m=WHEEL_DIAMETER_M,
            gear_ratio=GEAR_RATIO,
            efficiency=EFFICIENCY,
            motors_count=MOTORS_COUNT,
        )
    )
    result = total_acceleration_torque(steady, dynamic)
    assert result.value_nm == 10.68
    assert result.formula_id == "MECH.TRAVEL.Tacc.v1"
