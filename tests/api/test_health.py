from pathlib import Path

from fastapi.testclient import TestClient

from app.bootstrap.application import create_app
from app.bootstrap.settings import Settings


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


def test_ready_checks_database_and_migrations(client: TestClient) -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "checks": {"database": "ok", "migrations": "ok"}}


def test_ready_returns_503_when_schema_is_not_migrated(tmp_path: Path) -> None:
    settings = Settings(app_env="test", database_url=f"sqlite:///{tmp_path / 'empty.db'}")
    with TestClient(create_app(settings)) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.headers["content-type"] == "application/json"
    error = response.json()["error"]
    assert error["code"] == "SERVICE_UNAVAILABLE"
    assert error["details"] == {"checks": {"database": "ok", "migrations": "fail"}}


def test_ready_returns_503_when_database_is_down(tmp_path: Path) -> None:
    # A file in a missing directory cannot be opened: fails at once, unlike a closed TCP port.
    settings = Settings(app_env="test", database_url=f"sqlite:///{tmp_path / 'missing' / 'x.db'}")
    with TestClient(create_app(settings)) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["error"]["details"]["checks"] == {
        "database": "fail",
        "migrations": "fail",
    }


def test_unknown_health_path_is_json_not_spa() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health/unknown")

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/json"
