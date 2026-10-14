from datetime import datetime, timedelta

from fastapi.testclient import TestClient


def test_customer_cannot_call_admin_endpoint(
    client: TestClient, customer_token: str
) -> None:
    response = client.post(
        "/movies",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={
            "title": "Forbidden",
            "duration_minutes": 90,
            "genre": "Drama",
            "age_rating": "P",
        },
    )
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


def test_showtime_overlap_returns_conflict(
    client: TestClient, admin_token: str, catalog: dict[str, object]
) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    showtime = catalog["showtime"]
    response = client.post(
        "/showtimes",
        headers=headers,
        json={
            "movie_id": catalog["movie"]["id"],
            "room_id": catalog["room"]["id"],
            "starts_at": (
                datetime.fromisoformat(showtime["starts_at"].replace("Z", "+00:00"))
                + timedelta(minutes=30)
            ).isoformat(),
            "base_price": 100000,
        },
    )
    assert response.status_code == 409
    assert response.json()["code"] == "SHOWTIME_OVERLAP"


def test_public_browse_and_admin_room_list(
    client: TestClient, admin_token: str, catalog: dict[str, object]
) -> None:
    assert client.get("/movies").status_code == 200
    assert client.get("/showtimes").status_code == 200
    assert client.get(f"/showtimes/{catalog['showtime']['id']}/seats").status_code == 200
    assert client.get("/rooms").status_code == 401
    assert (
        client.get(
            "/rooms", headers={"Authorization": f"Bearer {admin_token}"}
        ).status_code
        == 200
    )
