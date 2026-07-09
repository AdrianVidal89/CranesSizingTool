"""Shared test fixtures: a real Postgres test database and FastAPI
TestClients wired to it via the DATABASE_URL environment variable.

Uses a dedicated test database (cranes_sizing_test), never the dev/prod
one, so tests can freely create and truncate data. These are integration
tests for the persistence layer, not mocked — they require a reachable
Postgres instance (see README for local setup).
"""

from __future__ import annotations

import os

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://cranes:cranes_dev_password@localhost:5432/cranes_sizing_test",
)
# TestClient talks plain HTTP (http://testserver); a Secure cookie would be
# silently dropped by the client, same as a real browser would over HTTP.
os.environ["SESSION_COOKIE_SECURE"] = "false"

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.db import models  # noqa: F401  (registers tables on Base.metadata)
from app.infrastructure.db.base import Base
from app.infrastructure.db.session import engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def make_client():
    """Factory for a fresh TestClient (own cookie jar) per call, so a test
    can hold two independently-authenticated clients at once."""

    def _make() -> TestClient:
        return TestClient(app)

    return _make


def register_and_login(client: TestClient, email: str, password: str = "correct-horse-battery") -> str:
    """Register + log in a user on the given client. Returns the CSRF token
    to send as X-CSRF-Token on subsequent mutating requests."""
    client.post("/api/auth/register", json={"email": email, "password": password})
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return client.cookies["csrf_token"]


# Generic, invented example data (not any real client's crane/motor) reused
# across persistence tests. Numbers match the worked examples from Phases
# 1-3, so results are cross-checked against those hand-derived values.
SAVE_CALCULATION_RUN_PAYLOAD: dict = {
    "new_project_name": "Generic Test Project (example data)",
    "crane_configuration_name": "Test Gantry Crane",
    "movement_kind": "travel",
    "movement_name": "Trolley travel",
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
