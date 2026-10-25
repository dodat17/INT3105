from fastapi.testclient import TestClient

from app.bootstrap.application import create_app
from scripts.export_openapi import OPENAPI_FILE, render


def _operations() -> list[tuple[str, str, dict[str, dict[str, object]]]]:
    with TestClient(create_app()) as client:
        schema = client.get("/openapi.json").json()
    return [
        (path, method, operation["responses"])
        for path, operations in schema["paths"].items()
        for method, operation in operations.items()
    ]


def test_openapi_documents_runtime_error_contract() -> None:
    operations = _operations()

    assert operations
    for path, method, responses in operations:
        assert "422" not in responses, (method, path)
        if path.startswith("/api/"):
            assert "500" in responses, (method, path)
        if path.startswith("/api/v1/admin/"):
            assert {"401", "403"} <= responses.keys(), (method, path)


def test_openapi_error_responses_use_shared_envelope() -> None:
    by_key = {(method, path): responses for path, method, responses in _operations()}

    ready = by_key[("get", "/health/ready")]["503"]
    conflict = by_key[("post", "/api/v1/bookings")]["409"]
    for response in (ready, conflict):
        schema = response["content"]["application/json"]["schema"]  # type: ignore[index]
        assert schema == {"$ref": "#/components/schemas/ErrorResponse"}
    assert {"400", "401", "403", "413", "415"} <= by_key[("post", "/api/v1/bookings")].keys()


def test_committed_openapi_matches_runtime() -> None:
    # Regenerate with: uv run python scripts/export_openapi.py
    assert OPENAPI_FILE.read_text(encoding="utf-8") == render()
