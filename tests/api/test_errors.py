from uuid import uuid4

from fastapi.testclient import TestClient

from app.bootstrap.application import create_app
from app.bootstrap.settings import get_settings
from app.domain.auth.model import Role
from app.infrastructure.security.tokens import JwtTokenService


def test_http_error_uses_shared_envelope() -> None:
    app = create_app()
    settings = get_settings()
    token = JwtTokenService(settings.jwt_secret, settings.jwt_algorithm, 60).issue(
        uuid4(), Role.CUSTOMER
    )

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/missing", headers={"Authorization": f"Bearer {token.access_token}"}
        )

    assert response.status_code == 404
    assert response.json()["error"]["requestId"] == response.headers["x-request-id"]
