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
