from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient

from tests.api.conftest import auth_header


def _create(client: TestClient, token: str, **overrides: Any) -> Any:
    body = {"title": "Mai", "durationMinutes": 131, "genre": "Tâm lý", "ageRating": "T18"}
    return client.post(
        "/api/v1/admin/movies", json={**body, **overrides}, headers=auth_header(token)
    )


def test_admin_creates_and_deletes_movie(client: TestClient, admin_token: str) -> None:
    created = _create(client, admin_token, description="Một câu chuyện.")
    assert created.status_code == 201
    movie = created.json()
    assert movie["title"] == "Mai"
    assert movie["durationMinutes"] == 131

    assert client.get(f"/api/v1/movies/{movie['id']}").json() == movie

    deleted = client.delete(f"/api/v1/admin/movies/{movie['id']}", headers=auth_header(admin_token))
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/movies/{movie['id']}").status_code == 404


def test_guest_browses_list_and_detail_without_token(client: TestClient, admin_token: str) -> None:
    movie = _create(client, admin_token).json()

    listing = client.get("/api/v1/movies")
    detail = client.get(f"/api/v1/movies/{movie['id']}")

    assert listing.status_code == 200
    assert listing.json() == {"items": [movie], "page": 1, "pageSize": 20, "totalItems": 1}
    assert detail.status_code == 200


def test_search_and_pagination(client: TestClient, admin_token: str) -> None:
    for title in ["Dune: Part Two", "Dune", "Mai", "Inside Out 2"]:
        _create(client, admin_token, title=title)

    found = client.get("/api/v1/movies", params={"q": "dUNe"}).json()
    page_two = client.get("/api/v1/movies", params={"page": 2, "pageSize": 3}).json()
    beyond = client.get("/api/v1/movies", params={"page": 9}).json()
    literal_percent = client.get("/api/v1/movies", params={"q": "%"}).json()

    assert [m["title"] for m in found["items"]] == ["Dune", "Dune: Part Two"]
    assert found["totalItems"] == 2
    assert [m["title"] for m in page_two["items"]] == ["Mai"]
    assert page_two["totalItems"] == 4
    assert beyond["items"] == [] and beyond["totalItems"] == 4
    assert literal_percent["totalItems"] == 0


def test_invalid_query_and_unknown_movie(client: TestClient) -> None:
    assert client.get("/api/v1/movies", params={"pageSize": 101}).status_code == 400
    assert client.get("/api/v1/movies", params={"page": 0}).status_code == 400
    assert client.get("/api/v1/movies/not-a-uuid").status_code == 400

    missing = client.get(f"/api/v1/movies/{uuid4()}")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


def test_create_movie_validates_payload(client: TestClient, admin_token: str) -> None:
    assert _create(client, admin_token, durationMinutes=0).status_code == 400
    assert _create(client, admin_token, title="  ").status_code == 400
    assert _create(client, admin_token, id=str(uuid4())).status_code == 400


def test_customer_cannot_call_admin_movie_api(
    client: TestClient, admin_token: str, customer_token: str
) -> None:
    movie = _create(client, admin_token).json()

    created = _create(client, customer_token)
    deleted = client.delete(
        f"/api/v1/admin/movies/{movie['id']}", headers=auth_header(customer_token)
    )

    assert created.status_code == deleted.status_code == 403
    assert created.json()["error"]["code"] == "FORBIDDEN"
    assert client.get(f"/api/v1/movies/{movie['id']}").status_code == 200


def test_guest_cannot_call_admin_movie_api(client: TestClient) -> None:
    assert client.post("/api/v1/admin/movies", json={}).status_code == 401
    assert client.delete(f"/api/v1/admin/movies/{uuid4()}").status_code == 401


def test_admin_updates_movie(client: TestClient, admin_token: str, customer_token: str) -> None:
    movie = _create(client, admin_token).json()
    url = f"/api/v1/admin/movies/{movie['id']}"
    body = {"title": "Mai 2", "durationMinutes": 100, "description": "Phần hai."}

    updated = client.put(url, json=body, headers=auth_header(admin_token))

    assert updated.status_code == 200
    assert updated.json() == {**movie, **body, "genre": "", "ageRating": ""}
    assert client.get(f"/api/v1/movies/{movie['id']}").json() == updated.json()
    assert client.put(url, json=body, headers=auth_header(customer_token)).status_code == 403
    missing = f"/api/v1/admin/movies/{uuid4()}"
    assert client.put(missing, json=body, headers=auth_header(admin_token)).status_code == 404
    invalid = {**body, "durationMinutes": 0}
    assert client.put(url, json=invalid, headers=auth_header(admin_token)).status_code == 400
