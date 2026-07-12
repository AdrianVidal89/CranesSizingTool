"""API smoke tests: endpoints are wired and return the expected shape."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_calculate_travel_requirement():
    response = client.post(
        "/api/calc/travel",
        json={
            "mass_dead_kg": 800.0,
            "mass_load_kg": 5000.0,
            "mass_tool_kg": 200.0,
            "velocity_ms": 0.5,
            "accel_time_s": 2.0,
            "wheel_diameter_m": 0.315,
            "gear_ratio": 20.0,
            "efficiency": 0.9,
            "motors_count": 2,
            "rolling_coeff": 0.016,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["required_torque_nm"] == 10.68
    assert body["required_speed_rpm"] == 606.3
    assert len(body["components"]) == 5


HOIST_PAYLOAD = {
    "mass_load_kg": 5000.0,
    "mass_tool_kg": 200.0,
    "velocity_ms": 0.2,
    "accel_time_s": 1.5,
    "drum_diameter_m": 0.4,
    "reeving_factor": 2.0,
    "gear_ratio": 25.0,
    "efficiency": 0.92,
    "motor_inertia_kgm2": 0.05,
    "brake_inertia_kgm2": 0.01,
}


def test_calculate_hoist_requirement():
    response = client.post("/api/calc/hoist", json=HOIST_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["required_torque_nm"] == 226.49
    assert body["required_speed_rpm"] == 477.46
    assert body["static_lifting_torque_nm"] == 221.72
    assert body["static_lowering_torque_nm"] == 187.66
    assert len(body["components"]) == 6


def test_calculate_hoist_requirement_rejects_zero_hook_load():
    payload = {**HOIST_PAYLOAD, "mass_load_kg": 0.0, "mass_tool_kg": 0.0}
    response = client.post("/api/calc/hoist", json=payload)
    assert response.status_code == 422


DUTY_CYCLE_PAYLOAD = {
    "mass_dead_kg": 800.0,
    "mass_load_kg": 5000.0,
    "mass_tool_kg": 200.0,
    "velocity_ms": 0.5,
    "accel_time_s": 2.0,
    "wheel_diameter_m": 0.315,
    "gear_ratio": 20.0,
    "efficiency": 0.9,
    "motors_count": 2,
    "rolling_coeff": 0.016,
    "distance_m": 10.0,
    "duty_factor_pct": 25.0,
    "cooling_factor": 0.5,
}


def test_calculate_duty_cycle():
    response = client.post("/api/calc/duty-cycle", json=DUTY_CYCLE_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["required_torque_nm"] == 10.68
    assert body["profile"]["is_triangular"] is False
    assert body["regime"]["starts_per_hour"] == 40.91
    assert body["decel_torque"]["is_regenerative"] is False
    assert body["rms_torque"]["value"] == 3.1495
    assert body["energy"]["energy_per_cycle_j"] == 6157.27
    assert body["mechanism_group_check"]["status"] == "not_available"


def test_calculate_duty_cycle_rejects_both_duty_regime_fields():
    payload = {**DUTY_CYCLE_PAYLOAD, "starts_per_hour": 30.0}
    response = client.post("/api/calc/duty-cycle", json=payload)
    assert response.status_code == 422


def test_calculate_duty_cycle_rejects_neither_duty_regime_field():
    payload = {k: v for k, v in DUTY_CYCLE_PAYLOAD.items() if k != "duty_factor_pct"}
    response = client.post("/api/calc/duty-cycle", json=payload)
    assert response.status_code == 422


def test_calculate_duty_cycle_triangular_profile():
    payload = {**DUTY_CYCLE_PAYLOAD, "distance_m": 0.4}
    response = client.post("/api/calc/duty-cycle", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["is_triangular"] is True


VALIDATE_CANDIDATE_PAYLOAD = {
    **DUTY_CYCLE_PAYLOAD,
    "motor": {
        "rated_power_kw": 2.2,
        "rated_speed_rpm": 750.0,
        "rated_voltage_v": 400.0,
        "power_factor": 0.85,
        "efficiency": 0.87,
        "nameplate_frequency_hz": 50.0,
        "breakdown_torque_pu": 2.5,
        "max_mechanical_torque_pu": 3.0,
        "no_load_current_a": 1.5,
    },
    "motor_target_frequency_hz": 50.0,
    "drive": {
        "rated_current_a": 6.0,
        "overload_factor": 1.6,
        "overload_duration_s": 60.0,
        "rated_voltage_v": 400.0,
    },
}


def test_validate_candidate_all_pass():
    response = client.post("/api/calc/validate-candidate", json=VALIDATE_CANDIDATE_PAYLOAD)
    assert response.status_code == 200
    body = response.json()
    assert body["motor_passed"] is True
    assert len(body["motor_conditions"]) == 4
    assert body["drive_passed"] is True
    assert len(body["drive_conditions"]) == 3
    assert body["rms_current_a"] == 2.1014
    assert body["requirement"]["required_torque_nm"] == 10.68


def test_validate_candidate_without_drive():
    payload = {k: v for k, v in VALIDATE_CANDIDATE_PAYLOAD.items() if k != "drive"}
    response = client.post("/api/calc/validate-candidate", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["drive_conditions"] is None
    assert body["drive_passed"] is None
    assert body["rms_current_a"] is None


def test_validate_candidate_rejects_ambiguous_torque_fields():
    payload = {
        **VALIDATE_CANDIDATE_PAYLOAD,
        "motor": {**VALIDATE_CANDIDATE_PAYLOAD["motor"], "breakdown_torque_nm": 70.0},
    }
    response = client.post("/api/calc/validate-candidate", json=payload)
    assert response.status_code == 422


def test_validate_candidate_fails_on_speed_band():
    payload = {
        **VALIDATE_CANDIDATE_PAYLOAD,
        "motor": {**VALIDATE_CANDIDATE_PAYLOAD["motor"], "rated_speed_rpm": 1450.0},
    }
    response = client.post("/api/calc/validate-candidate", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["motor_passed"] is False
    speed = next(c for c in body["motor_conditions"] if c["formula_id"] == "MOTOR.VALIDATE.Speed.v1")
    assert speed["verdict"] == "fail"
