"""Per-user isolation: a user must never be able to read, list, or download
another user's Project, CalculationRun, or Report (CLAUDE.md: "toda query
filtra por propietario, sin excepción").
"""

from tests.conftest import SAVE_CALCULATION_RUN_PAYLOAD, register_and_login


def _save_run(client, csrf_token):
    response = client.post(
        "/api/calculation-runs",
        json=SAVE_CALCULATION_RUN_PAYLOAD,
        headers={"X-CSRF-Token": csrf_token},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_user_cannot_get_another_users_calculation_run(make_client):
    client_a = make_client()
    csrf_a = register_and_login(client_a, "alice-isolation@example.com")
    run = _save_run(client_a, csrf_a)

    client_b = make_client()
    register_and_login(client_b, "bob-isolation@example.com")

    response = client_b.get(f"/api/calculation-runs/{run['id']}")
    assert response.status_code == 404


def test_user_cannot_list_another_users_calculation_runs(make_client):
    client_a = make_client()
    csrf_a = register_and_login(client_a, "alice-list@example.com")
    _save_run(client_a, csrf_a)

    client_b = make_client()
    register_and_login(client_b, "bob-list@example.com")

    response = client_b.get("/api/calculation-runs")
    assert response.status_code == 200
    assert response.json() == []


def test_user_cannot_generate_report_for_another_users_calculation_run(make_client):
    client_a = make_client()
    csrf_a = register_and_login(client_a, "alice-report@example.com")
    run = _save_run(client_a, csrf_a)

    client_b = make_client()
    csrf_b = register_and_login(client_b, "bob-report@example.com")

    response = client_b.post(
        "/api/reports",
        json={"calculation_run_id": run["id"]},
        headers={"X-CSRF-Token": csrf_b},
    )
    assert response.status_code == 404


def test_user_cannot_download_another_users_report(make_client):
    client_a = make_client()
    csrf_a = register_and_login(client_a, "alice-pdf@example.com")
    run = _save_run(client_a, csrf_a)
    report = client_a.post(
        "/api/reports",
        json={"calculation_run_id": run["id"]},
        headers={"X-CSRF-Token": csrf_a},
    ).json()

    client_b = make_client()
    register_and_login(client_b, "bob-pdf@example.com")

    response = client_b.get(f"/api/reports/{report['id']}/pdf")
    assert response.status_code == 404


def test_user_cannot_list_another_users_projects(make_client):
    client_a = make_client()
    csrf_a = register_and_login(client_a, "alice-proj@example.com")
    client_a.post(
        "/api/projects",
        json={"name": "Alice's private project"},
        headers={"X-CSRF-Token": csrf_a},
    )

    client_b = make_client()
    register_and_login(client_b, "bob-proj@example.com")

    response = client_b.get("/api/projects")
    assert response.status_code == 200
    assert response.json() == []


def test_user_cannot_attach_calculation_run_to_another_users_project(make_client):
    client_a = make_client()
    csrf_a = register_and_login(client_a, "alice-attach@example.com")
    project = client_a.post(
        "/api/projects",
        json={"name": "Alice's project"},
        headers={"X-CSRF-Token": csrf_a},
    ).json()

    client_b = make_client()
    csrf_b = register_and_login(client_b, "bob-attach@example.com")

    payload = {**SAVE_CALCULATION_RUN_PAYLOAD, "project_id": project["id"]}
    payload.pop("new_project_name", None)
    response = client_b.post(
        "/api/calculation-runs", json=payload, headers={"X-CSRF-Token": csrf_b}
    )
    assert response.status_code == 404


def test_own_calculation_run_is_readable(make_client):
    """Sanity check: a user CAN read their own data (isolation isn't over-broad)."""
    client_a = make_client()
    csrf_a = register_and_login(client_a, "alice-own@example.com")
    run = _save_run(client_a, csrf_a)

    response = client_a.get(f"/api/calculation-runs/{run['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == run["id"]
