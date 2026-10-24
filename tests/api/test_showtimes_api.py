from uuid import uuid4

from fastapi.testclient import TestClient

from tests.api.conftest import auth_header, create_showtime


def test_admin_creates_showtime_with_computed_end(
    client: TestClient, admin_token: str, setup: dict[str, str]
) -> None:
    response = create_showtime(client, admin_token, setup, "2026-10-20T19:00:00+07:00")

    assert response.status_code == 201
    showtime = response.json()
    assert showtime["startsAt"] == "2026-10-20T12:00:00Z"
    assert showtime["endsAt"] == "2026-10-20T14:00:00Z"
    assert showtime["basePrice"] == 90000


def test_overlapping_showtime_in_same_room_is_rejected(
    client: TestClient, admin_token: str, setup: dict[str, str]
) -> None:
    create_showtime(client, admin_token, setup, "2026-10-20T19:00:00+07:00")

    clash = create_showtime(client, admin_token, setup, "2026-10-20T20:30:00+07:00")
    back_to_back = create_showtime(client, admin_token, setup, "2026-10-20T21:00:00+07:00")
    other_room = create_showtime(
        client, admin_token, setup, "2026-10-20T19:30:00+07:00", auditoriumId=setup["other_room"]
    )

    assert clash.status_code == 409
    assert clash.json()["error"]["code"] == "SHOWTIME_OVERLAP"
    assert back_to_back.status_code == 201
    assert other_room.status_code == 201


def test_create_showtime_validates_input(
    client: TestClient, admin_token: str, setup: dict[str, str]
) -> None:
    naive = create_showtime(client, admin_token, setup, "2026-10-20T19:00:00")
    free = create_showtime(client, admin_token, setup, "2026-10-20T19:00:00Z", basePrice=0)
    unknown_movie = create_showtime(
        client, admin_token, setup, "2026-10-20T19:00:00Z", movieId=str(uuid4())
    )

    assert naive.status_code == 400
    assert free.status_code == 400
    assert unknown_movie.status_code == 404


def test_guest_lists_showtimes_filtered_by_movie_and_local_date(
    client: TestClient, admin_token: str, setup: dict[str, str]
) -> None:
    # 23:30 on 20/10 in Vietnam is still 20/10 locally although it is 16:30 UTC...
    late = create_showtime(client, admin_token, setup, "2026-10-20T23:30:00+07:00").json()
    # ...and 06:00 on 21/10 locally is 23:00 UTC on 20/10, yet belongs to 21/10.
    early = create_showtime(client, admin_token, setup, "2026-10-21T06:00:00+07:00").json()
    first = create_showtime(client, admin_token, setup, "2026-10-20T09:00:00+07:00").json()

    everything = client.get("/api/v1/showtimes").json()
    on_20 = client.get("/api/v1/showtimes", params={"date": "2026-10-20"}).json()
    on_21 = client.get(
        "/api/v1/showtimes", params={"date": "2026-10-21", "movieId": setup["movie"]}
    ).json()
    other_movie = client.get("/api/v1/showtimes", params={"movieId": str(uuid4())}).json()

    assert [s["id"] for s in everything["items"]] == [first["id"], late["id"], early["id"]]
    assert [s["id"] for s in on_20["items"]] == [first["id"], late["id"]]
    assert [s["id"] for s in on_21["items"]] == [early["id"]]
    assert other_movie == {"items": [], "page": 1, "pageSize": 20, "totalItems": 0}
    assert client.get("/api/v1/showtimes", params={"date": "20-10-2026"}).status_code == 400


def test_guest_sees_seat_map_with_vip_prices(
    client: TestClient, admin_token: str, setup: dict[str, str]
) -> None:
    showtime = create_showtime(client, admin_token, setup, "2026-10-20T19:00:00+07:00").json()

    response = client.get(f"/api/v1/showtimes/{showtime['id']}/seats")

    assert response.status_code == 200
    body = response.json()
    assert body["showtimeId"] == showtime["id"]
    assert body["auditorium"]["name"] == "Phòng 1"
    seats = body["seats"]
    assert len(seats) == 12
    assert [s["label"] for s in seats[:5]] == ["A1", "A2", "A3", "A4", "B1"]
    assert {s["price"] for s in seats if s["seatType"] == "STANDARD"} == {90000}
    assert {s["price"] for s in seats if s["seatType"] == "VIP"} == {117000}
    assert {s["rowLabel"] for s in seats if s["seatType"] == "VIP"} == {"C"}
    assert {s["status"] for s in seats} == {"AVAILABLE"}
    assert client.get(f"/api/v1/showtimes/{uuid4()}/seats").status_code == 404


def test_admin_deletes_showtime_and_movie_in_use_is_kept(
    client: TestClient, admin_token: str, customer_token: str, setup: dict[str, str]
) -> None:
    showtime = create_showtime(client, admin_token, setup, "2026-10-20T19:00:00+07:00").json()
    url = f"/api/v1/admin/showtimes/{showtime['id']}"

    blocked = client.delete(
        f"/api/v1/admin/movies/{setup['movie']}", headers=auth_header(admin_token)
    )
    assert blocked.status_code == 400
    assert client.delete(url, headers=auth_header(customer_token)).status_code == 403

    assert client.delete(url, headers=auth_header(admin_token)).status_code == 204
    assert client.get(f"/api/v1/showtimes/{showtime['id']}/seats").status_code == 404
    assert client.delete(url, headers=auth_header(admin_token)).status_code == 404
    movie_url = f"/api/v1/admin/movies/{setup['movie']}"
    assert client.delete(movie_url, headers=auth_header(admin_token)).status_code == 204


def test_only_admin_creates_showtimes(
    client: TestClient, admin_token: str, customer_token: str, setup: dict[str, str]
) -> None:
    as_customer = create_showtime(client, customer_token, setup, "2026-10-20T19:00:00+07:00")
    as_guest = client.post("/api/v1/admin/showtimes", json={})

    assert as_customer.status_code == 403
    assert as_guest.status_code == 401
    assert client.get("/api/v1/showtimes").json()["totalItems"] == 0


def test_guest_sees_showtime_detail(
    client: TestClient, admin_token: str, setup: dict[str, str]
) -> None:
    showtime = create_showtime(client, admin_token, setup, "2026-10-20T19:00:00+07:00").json()

    response = client.get(f"/api/v1/showtimes/{showtime['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["movie"] == {"id": setup["movie"], "title": "Mai"}
    assert body["auditorium"] == {"id": setup["room"], "name": "Phòng 1"}
    assert body["currency"] == "VND"
    assert body["basePrice"] == 90000
    assert client.get(f"/api/v1/showtimes/{uuid4()}").status_code == 404


def test_admin_updates_showtime(
    client: TestClient, admin_token: str, customer_token: str, setup: dict[str, str]
) -> None:
    showtime = create_showtime(client, admin_token, setup, "2026-10-20T19:00:00+07:00").json()
    url = f"/api/v1/admin/showtimes/{showtime['id']}"
    body = {
        "movieId": setup["movie"],
        "auditoriumId": setup["other_room"],
        "startsAt": "2026-10-20T20:00:00+07:00",
        "basePrice": 100000,
        "isOpenForBooking": False,
    }

    updated = client.put(url, json=body, headers=auth_header(admin_token))

    assert updated.status_code == 200
    assert updated.json()["startsAt"] == "2026-10-20T13:00:00Z"
    assert updated.json()["endsAt"] == "2026-10-20T15:00:00Z"
    assert updated.json()["auditoriumId"] == setup["other_room"]
    assert updated.json()["isOpenForBooking"] is False
    seats = client.get(f"/api/v1/showtimes/{showtime['id']}/seats").json()["seats"]
    assert len(seats) == 1
    assert client.put(url, json=body, headers=auth_header(customer_token)).status_code == 403
    missing = f"/api/v1/admin/showtimes/{uuid4()}"
    assert client.put(missing, json=body, headers=auth_header(admin_token)).status_code == 404


def test_update_showtime_rejects_overlap(
    client: TestClient, admin_token: str, setup: dict[str, str]
) -> None:
    create_showtime(client, admin_token, setup, "2026-10-20T19:00:00+07:00")
    later = create_showtime(client, admin_token, setup, "2026-10-20T22:00:00+07:00").json()

    response = client.put(
        f"/api/v1/admin/showtimes/{later['id']}",
        json={
            "movieId": setup["movie"],
            "auditoriumId": setup["room"],
            "startsAt": "2026-10-20T20:00:00+07:00",
            "basePrice": 90000,
        },
        headers=auth_header(admin_token),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SHOWTIME_OVERLAP"
