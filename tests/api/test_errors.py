from fastapi.testclient import TestClient

from app.bootstrap.application import create_app


def test_http_error_uses_shared_envelope() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/api/v1/missing")

    assert response.status_code == 404
    assert response.json()["error"]["requestId"] == response.headers["x-request-id"]
