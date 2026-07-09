"""Auth endpoint tests: register, login, logout, /me, and CSRF protection."""

from tests.conftest import register_and_login


def test_register_then_me_requires_login(make_client):
    client = make_client()
    response = client.post(
        "/api/auth/register",
        json={"email": "newuser@example.com", "password": "correct-horse-battery"},
    )
    assert response.status_code == 201

    # Not logged in yet: /me must reject.
    assert client.get("/api/auth/me").status_code == 401


def test_duplicate_registration_rejected(make_client):
    client = make_client()
    payload = {"email": "dup@example.com", "password": "correct-horse-battery"}
    first = client.post("/api/auth/register", json=payload)
    assert first.status_code == 201
    second = client.post("/api/auth/register", json=payload)
    assert second.status_code == 409


def test_login_with_wrong_password_rejected(make_client):
    client = make_client()
    client.post(
        "/api/auth/register", json={"email": "wrongpw@example.com", "password": "correct-one"}
    )
    response = client.post(
        "/api/auth/login", json={"email": "wrongpw@example.com", "password": "not-the-password"}
    )
    assert response.status_code == 401


def test_login_sets_cookies_and_me_works(make_client):
    client = make_client()
    register_and_login(client, "loginflow@example.com")
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "loginflow@example.com"


def test_logout_without_csrf_header_is_rejected(make_client):
    client = make_client()
    register_and_login(client, "csrf-missing@example.com")
    response = client.post("/api/auth/logout")
    assert response.status_code == 403


def test_logout_with_wrong_csrf_header_is_rejected(make_client):
    client = make_client()
    register_and_login(client, "csrf-wrong@example.com")
    response = client.post("/api/auth/logout", headers={"X-CSRF-Token": "not-the-real-token"})
    assert response.status_code == 403


def test_logout_invalidates_session(make_client):
    client = make_client()
    csrf_token = register_and_login(client, "logout-flow@example.com")
    response = client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf_token})
    assert response.status_code == 204
    assert client.get("/api/auth/me").status_code == 401
