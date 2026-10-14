from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient


def test_register_login_me_and_duplicate_email(client: TestClient) -> None:
    payload = {"email": "person@example.com", "password": "password", "full_name": "Person"}
    assert client.post("/auth/register", json=payload).status_code == 201
    duplicate = client.post("/auth/register", json=payload)
    login = client.post(
        "/auth/login", json={"email": payload["email"], "password": payload["password"]}
    )
    me = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"}
    )

    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "EMAIL_ALREADY_USED"
    assert login.status_code == 200
    assert me.json()["email"] == payload["email"]


def test_missing_invalid_and_expired_tokens_return_401(client: TestClient) -> None:
    assert client.get("/auth/me").status_code == 401
    response = client.get("/auth/me", headers={"Authorization": "Bearer invalid"})
    expired = jwt.encode(
        {
            "sub": "user-id",
            "role": "CUSTOMER",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        "test-secret-that-is-at-least-32-bytes-long",
        algorithm="HS256",
    )
    expired_response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {expired}"}
    )
    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"
    assert expired_response.status_code == 401


def test_validation_errors_use_standard_shape(client: TestClient) -> None:
    response = client.post(
        "/auth/register", json={"email": "invalid", "password": "short", "full_name": ""}
    )
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_health_openapi_and_options_are_public(client: TestClient) -> None:
    assert client.get("/health").status_code == 200
    schema = client.get("/openapi.json")
    preflight = client.options(
        "/bookings",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert schema.status_code == 200
    assert "BearerAuth" in schema.json()["components"]["securitySchemes"]
    assert preflight.status_code == 200
