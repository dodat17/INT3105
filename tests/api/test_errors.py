from collections.abc import Iterator
from uuid import uuid4

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.bootstrap.application import create_app
from app.bootstrap.settings import get_settings
from app.domain.auth.model import Role
from app.infrastructure.security.tokens import JwtTokenService


def _token() -> dict[str, str]:
    settings = get_settings()
    token = JwtTokenService(settings.jwt_secret, settings.jwt_algorithm, 60).issue(
        uuid4(), Role.CUSTOMER
    )
    return {"Authorization": f"Bearer {token.access_token}"}


def test_http_error_uses_shared_envelope() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/missing", headers=_token())

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert response.json()["error"]["requestId"] == response.headers["x-request-id"]


def test_unsupported_method_on_known_route_is_405() -> None:
    with TestClient(create_app()) as client:
        response = client.patch(f"/api/v1/bookings/{uuid4()}", headers=_token())

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"
    assert response.headers["allow"] == "DELETE, GET"


def test_unexpected_error_hides_internals() -> None:
    app = create_app()

    def boom() -> None:
        raise RuntimeError("SELECT secret FROM users")

    # Ahead of the SPA mount, which would otherwise serve /boom.
    app.router.routes.insert(0, APIRoute("/boom", boom))

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom")

    assert response.status_code == 500
    error = response.json()["error"]
    assert error["code"] == "INTERNAL_ERROR"
    assert "SELECT" not in error["message"]
    assert error["requestId"] == response.headers["x-request-id"]


def test_body_must_be_json_and_is_checked_before_auth() -> None:
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/bookings", content=b"{}", headers={"Content-Type": "text/plain"}
        )
        no_body = client.delete(
            f"/api/v1/bookings/{uuid4()}", headers={"Content-Type": "text/plain"}
        )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"
    assert no_body.status_code == 401


def test_body_over_64_kb_is_rejected(client: TestClient) -> None:
    big_name = "x" * (64 * 1024)
    payload = {"email": "big@example.test", "password": "secret123", "fullName": big_name}

    response = client.post("/api/v1/auth/register", json=payload)

    def chunks() -> Iterator[bytes]:
        yield b'{"email": "big@example.test", "password": "secret123", "fullName": "'
        yield big_name.encode()
        yield b'"}'

    chunked = client.post(
        "/api/v1/auth/register", content=chunks(), headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
    assert chunked.status_code == 413
    assert chunked.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
    login = client.post(
        "/api/v1/auth/login", json={"email": "big@example.test", "password": "secret123"}
    )
    assert login.status_code == 401
