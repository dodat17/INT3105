from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from tests.api.conftest import JWT_SECRET, PASSWORD, auth_header, login


def _register(client: TestClient, **overrides: Any) -> Any:
    body = {"email": "an@example.test", "password": PASSWORD, "fullName": "Nguyễn An"}
    return client.post("/api/v1/auth/register", json={**body, **overrides})


def test_register_login_me_then_browse_movies(client: TestClient) -> None:
    registered = _register(client, email="  An@Example.TEST ")
    assert registered.status_code == 201
    user = registered.json()
    assert user["email"] == "an@example.test"
    assert user["role"] == "CUSTOMER"
    assert "password" not in str(user).lower()

    login_response = client.post(
        "/api/v1/auth/login", json={"email": "AN@example.test", "password": PASSWORD}
    )
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["tokenType"] == "Bearer"
    assert body["expiresIn"] == 3600

    me = client.get("/api/v1/auth/me", headers=auth_header(body["accessToken"]))
    assert me.status_code == 200
    assert me.json() == user

    assert client.get("/api/v1/movies", headers=auth_header(body["accessToken"])).status_code == 200


def test_register_rejects_duplicate_email(client: TestClient) -> None:
    _register(client)

    response = _register(client, email="AN@example.test")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "EMAIL_ALREADY_USED"


def test_register_rejects_short_password(client: TestClient) -> None:
    response = _register(client, password="1234567")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


@pytest.mark.parametrize(
    "overrides",
    [{"role": "ADMIN"}, {"email": "not-an-email"}, {"fullName": "   "}],
    ids=["role-field", "bad-email", "blank-name"],
)
def test_register_rejects_invalid_payload(client: TestClient, overrides: dict[str, str]) -> None:
    response = _register(client, **overrides)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_wrong_password_and_unknown_email_get_identical_error(client: TestClient) -> None:
    _register(client)

    wrong_password = client.post(
        "/api/v1/auth/login", json={"email": "an@example.test", "password": "wrong-pass"}
    )
    unknown_email = client.post(
        "/api/v1/auth/login", json={"email": "nobody@example.test", "password": PASSWORD}
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    first, second = wrong_password.json()["error"], unknown_email.json()["error"]
    assert (first["code"], first["message"]) == (second["code"], second["message"])
    assert first["code"] == "INVALID_CREDENTIALS"


def _token(secret: str = JWT_SECRET, algorithm: str = "HS256", **claims: Any) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(uuid4()),
        "role": "CUSTOMER",
        "iat": now,
        "exp": now + timedelta(minutes=5),
        **claims,
    }
    payload = {key: value for key, value in payload.items() if value is not None}
    return jwt.encode(payload, secret, algorithm=algorithm)


def _alg_none_token() -> str:
    return _token(secret="", algorithm="none")


@pytest.mark.parametrize(
    "authorization",
    [
        None,
        "Bearer",
        "Bearer not-a-jwt",
        "Basic dXNlcjpwYXNz",
        f"Bearer {_token(secret='another-secret-with-at-least-32-bytes')}",
        f"Bearer {_alg_none_token()}",
        f"Bearer {_token(sub=None)}",
        f"Bearer {_token(role='SUPERUSER')}",
        f"Bearer {_token(exp=datetime.now(UTC) - timedelta(seconds=120))}",
    ],
    ids=[
        "missing",
        "empty",
        "garbage",
        "basic-scheme",
        "wrong-key",
        "alg-none",
        "no-sub",
        "unknown-role",
        "expired",
    ],
)
def test_protected_endpoint_rejects_bad_tokens(
    client: TestClient, authorization: str | None
) -> None:
    headers = {"Authorization": authorization} if authorization else {}

    response = client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    assert response.json()["error"]["requestId"] == response.headers["x-request-id"]


def test_token_expired_within_clock_skew_is_accepted(client: TestClient) -> None:
    _register(client)
    real = jwt.decode(login(client, "an@example.test"), JWT_SECRET, algorithms=["HS256"])
    token = _token(sub=real["sub"], exp=datetime.now(UTC) - timedelta(seconds=30))

    assert client.get("/api/v1/auth/me", headers=auth_header(token)).status_code == 200


def test_unknown_api_route_is_protected_by_default(client: TestClient) -> None:
    assert client.get("/api/v1/not-yet-built").status_code == 401
