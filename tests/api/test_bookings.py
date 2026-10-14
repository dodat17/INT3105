from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient


def test_booking_end_to_end_cancel_and_rebook(
    client: TestClient, customer_token: str, catalog: dict[str, object]
) -> None:
    headers = {"Authorization": f"Bearer {customer_token}"}
    payload = {
        "showtime_id": catalog["showtime"]["id"],
        "seat_ids": [catalog["seats"][0]["id"]],
    }
    created = client.post("/bookings", headers=headers, json=payload)
    listed = client.get("/bookings", headers=headers)
    detail = client.get(f"/bookings/{created.json()['id']}", headers=headers)
    cancelled = client.delete(f"/bookings/{created.json()['id']}", headers=headers)
    rebooked = client.post("/bookings", headers=headers, json=payload)

    assert created.status_code == 201
    assert listed.status_code == 200 and len(listed.json()) == 1
    assert detail.status_code == 200
    assert cancelled.status_code == 204
    assert rebooked.status_code == 201


def test_duplicate_seat_and_protected_delete(
    client: TestClient,
    customer_token: str,
    admin_token: str,
    catalog: dict[str, object],
) -> None:
    customer_headers = {"Authorization": f"Bearer {customer_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "showtime_id": catalog["showtime"]["id"],
        "seat_ids": [catalog["seats"][0]["id"]],
    }
    assert client.post("/bookings", headers=customer_headers, json=payload).status_code == 201
    conflict = client.post("/bookings", headers=customer_headers, json=payload)
    movie_delete = client.delete(
        f"/movies/{catalog['movie']['id']}", headers=admin_headers
    )
    showtime_delete = client.delete(
        f"/showtimes/{catalog['showtime']['id']}", headers=admin_headers
    )

    assert conflict.status_code == 409
    assert conflict.json()["code"] == "SEAT_UNAVAILABLE"
    assert movie_delete.status_code == 400
    assert showtime_delete.status_code == 400


def test_started_showtime_cannot_be_booked(
    client: TestClient,
    customer_token: str,
    admin_token: str,
    catalog: dict[str, object],
) -> None:
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    started = client.post(
        "/showtimes",
        headers=admin_headers,
        json={
            "movie_id": catalog["movie"]["id"],
            "room_id": catalog["room"]["id"],
            "starts_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "base_price": 100000,
        },
    ).json()
    seats = client.get(f"/showtimes/{started['id']}/seats").json()["seats"]
    response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {customer_token}"},
        json={"showtime_id": started["id"], "seat_ids": [seats[0]["id"]]},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "SHOWTIME_ALREADY_STARTED"
