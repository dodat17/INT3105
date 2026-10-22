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
