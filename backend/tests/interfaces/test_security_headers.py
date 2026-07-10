"""Security response headers (defense-in-depth for direct backend access;
Nginx sets the canonical ones in production — see nginx/prod/)."""

from fastapi.testclient import TestClient

from app.main import app, docs_urls

client = TestClient(app)


def test_docs_disabled_in_production():
    assert docs_urls(is_production=True) == (None, None, None)


def test_docs_enabled_outside_production():
    assert docs_urls(is_production=False) == ("/docs", "/redoc", "/openapi.json")


def test_security_headers_present_on_api_response():
    response = client.get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["Content-Security-Policy"] == "default-src 'none'; frame-ancestors 'none'"


def test_docs_paths_exempt_from_strict_csp_in_dev():
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Content-Security-Policy" not in response.headers
