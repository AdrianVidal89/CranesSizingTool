"""Application-level test: the use case orchestrates the domain formulas
correctly and surfaces every component's provenance (formula_id, assumptions,
standard_refs). Numbers reuse the worked example documented in
tests/domain/calc/mechanics/test_travel.py.
"""

from app.application.calculate_travel_requirement import (
    CalculateTravelRequirement,
    TravelRequirementRequest,
)


def test_execute_returns_total_torque_speed_and_components():
    use_case = CalculateTravelRequirement()
    result = use_case.execute(
        TravelRequirementRequest(
            mass_dead_kg=800.0,
            mass_load_kg=5000.0,
            mass_tool_kg=200.0,
            velocity_ms=0.5,
            accel_time_s=2.0,
            wheel_diameter_m=0.315,
            gear_ratio=20.0,
            efficiency=0.9,
            motors_count=2,
            rolling_coeff=0.016,
        )
    )

    assert result.required_torque_nm == 10.68
    assert result.required_speed_rpm == 606.3
    assert len(result.components) == 5
    assert {c.formula_id for c in result.components} == {
        "MECH.TRAVEL.Fr.v1",
        "MECH.TRAVEL.Nc.v1",
        "MECH.TRAVEL.Tss.v1",
        "MECH.TRAVEL.Tdyn.v1",
        "MECH.TRAVEL.Tacc.v1",
    }
    for component in result.components:
        assert component.assumptions
        assert component.standard_refs
