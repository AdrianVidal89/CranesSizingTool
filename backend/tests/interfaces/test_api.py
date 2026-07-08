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
