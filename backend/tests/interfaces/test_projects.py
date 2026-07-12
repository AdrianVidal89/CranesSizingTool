"""Project setup endpoints: create a project with its named movements
(hoists and travel movements, at most 3 of each) and list it back."""

from tests.conftest import register_and_login

PROJECT_PAYLOAD = {
    "name": "Crane 86 (example data)",
    "crane_configuration_name": "Main configuration",
    "movements": [
        {"kind": "hoist", "name": "Main hoist"},
        {"kind": "hoist", "name": "Auxiliary hoist"},
        {"kind": "travel", "name": "Long travel (bridge)"},
        {"kind": "travel", "name": "Cross travel (trolley)"},
    ],
}


def test_create_project_with_movements(make_client):
    client = make_client()
    csrf = register_and_login(client, "setup-create@example.com")

    response = client.post(
        "/api/projects", json=PROJECT_PAYLOAD, headers={"X-CSRF-Token": csrf}
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == "Crane 86 (example data)"
    assert [m["kind"] for m in body["movements"]] == ["hoist", "hoist", "travel", "travel"]
    assert [m["name"] for m in body["movements"]] == [
        "Main hoist",
        "Auxiliary hoist",
        "Long travel (bridge)",
        "Cross travel (trolley)",
    ]
    assert all(m["id"] for m in body["movements"])


def test_list_projects_returns_movements(make_client):
    client = make_client()
    csrf = register_and_login(client, "setup-list@example.com")
    client.post("/api/projects", json=PROJECT_PAYLOAD, headers={"X-CSRF-Token": csrf})

    response = client.get("/api/projects")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) == 1
    assert len(projects[0]["movements"]) == 4


def test_create_project_without_movements_still_works(make_client):
    """Backward compatibility: SavePanel-style bare project creation."""
    client = make_client()
    csrf = register_and_login(client, "setup-bare@example.com")

    response = client.post(
        "/api/projects", json={"name": "Bare project"}, headers={"X-CSRF-Token": csrf}
    )
    assert response.status_code == 201, response.text
    assert response.json()["movements"] == []


def test_create_project_rejects_more_than_three_hoists(make_client):
    client = make_client()
    csrf = register_and_login(client, "setup-toomany@example.com")

    payload = {
        "name": "Too many hoists",
        "movements": [{"kind": "hoist", "name": f"Hoist {n}"} for n in range(4)],
    }
    response = client.post("/api/projects", json=payload, headers={"X-CSRF-Token": csrf})
    assert response.status_code == 422


def test_create_project_rejects_unknown_movement_kind(make_client):
    client = make_client()
    csrf = register_and_login(client, "setup-kind@example.com")

    payload = {"name": "Bad kind", "movements": [{"kind": "slew", "name": "Slewing"}]}
    response = client.post("/api/projects", json=payload, headers={"X-CSRF-Token": csrf})
    assert response.status_code == 422
