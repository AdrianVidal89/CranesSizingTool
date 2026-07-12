"""Use-case test for CalculateHoistRequirement.

Expected values come from the hand-derived worked example in
tests/domain/calc/mechanics/test_hoist.py: hook load 5000+200 kg, 0.4 m
drum, reeving factor 2, gear ratio 25, eta 0.92, 0.2 m/s, 1.5 s ramp,
J_motor 0.05, J_brake 0.01 kg*m^2.
"""

from app.application.calculate_hoist_requirement import (
    CalculateHoistRequirement,
    HoistRequirementRequest,
)

REQUEST = HoistRequirementRequest(
    mass_load_kg=5000.0,
    mass_tool_kg=200.0,
    velocity_ms=0.2,
    accel_time_s=1.5,
    drum_diameter_m=0.4,
    reeving_factor=2.0,
    gear_ratio=25.0,
    efficiency=0.92,
    motor_inertia_kgm2=0.05,
    brake_inertia_kgm2=0.01,
)


def test_hoist_requirement_matches_worked_example():
    result = CalculateHoistRequirement().execute(REQUEST)

    assert result.required_speed_rpm == 477.46
    assert result.static_lifting_torque_nm == 221.72
    assert result.static_lowering_torque_nm == 187.66
    assert result.rotor_dynamic_torque_nm == 2.0
    assert result.load_dynamic_torque_nm == 2.7733
    assert result.required_torque_nm == 226.49


def test_hoist_requirement_reports_both_directions_with_formula_ids():
    result = CalculateHoistRequirement().execute(REQUEST)

    labels = [c.label for c in result.components]
    assert "Static hoisting torque (lifting)" in labels
    assert "Static torque (lowering)" in labels

    formula_ids = {c.formula_id for c in result.components}
    assert formula_ids == {
        "MECH.HOIST.Nc.v1",
        "MECH.HOIST.Tss.v1",
        "MECH.HOIST.Tdyn_rotor.v1",
        "MECH.HOIST.Tdyn_load.v1",
        "MECH.HOIST.Tacc.v1",
    }
    for component in result.components:
        assert component.assumptions
        assert component.standard_refs


def test_lowering_requires_less_torque_than_lifting():
    result = CalculateHoistRequirement().execute(REQUEST)
    assert result.static_lowering_torque_nm < result.static_lifting_torque_nm
