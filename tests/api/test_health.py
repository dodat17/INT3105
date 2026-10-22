from fastapi.testclient import TestClient

from app.bootstrap.application import create_app


def test_health_returns_ok_and_request_id() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-request-id"]
    assert "default-src 'self'" in response.headers["content-security-policy"]
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_docs_csp_allows_swagger_assets_only_on_docs() -> None:
    with TestClient(create_app()) as client:
        docs_response = client.get("/docs")
        health_response = client.get("/health")

    docs_csp = docs_response.headers["content-security-policy"]
    health_csp = health_response.headers["content-security-policy"]
    assert "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net" in docs_csp
    assert "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net" in docs_csp
    assert "cdn.jsdelivr.net" not in health_csp
