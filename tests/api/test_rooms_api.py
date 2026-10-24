from uuid import uuid4

from fastapi.testclient import TestClient

from tests.api.conftest import auth_header, create_room, create_showtime


def test_admin_creates_and_lists_rooms(client: TestClient, admin_token: str) -> None:
    created = create_room(client, admin_token)

    assert created.status_code == 201
    room = created.json()
    assert room["name"] == "Phòng 1"
    assert room["seatCount"] == 40

    listing = client.get("/api/v1/admin/auditoriums", headers=auth_header(admin_token))
    assert listing.status_code == 200
    assert listing.json() == [room]


def test_room_name_must_be_unique(client: TestClient, admin_token: str) -> None:
    create_room(client, admin_token)

    response = create_room(client, admin_token, cols=2)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "AUDITORIUM_NAME_ALREADY_USED"


def test_room_layout_is_validated(client: TestClient, admin_token: str) -> None:
    assert create_room(client, admin_token, rows=27).status_code == 400
    assert create_room(client, admin_token, cols=0).status_code == 400
    vip_outside = create_room(client, admin_token, rows=3, vipRows=[4])
    assert vip_outside.status_code == 400
    assert vip_outside.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"
    assert client.get("/api/v1/admin/auditoriums", headers=auth_header(admin_token)).json() == []


def test_only_admin_manages_rooms(client: TestClient, customer_token: str) -> None:
    assert create_room(client, customer_token).status_code == 403
    assert (
        client.get("/api/v1/admin/auditoriums", headers=auth_header(customer_token)).status_code
        == 403
    )
    assert client.get("/api/v1/admin/auditoriums").status_code == 401
    assert client.post("/api/v1/admin/auditoriums", json={}).status_code == 401


def test_admin_reads_and_updates_auditorium(
    client: TestClient, admin_token: str, customer_token: str
) -> None:
    room = create_room(client, admin_token).json()
    url = f"/api/v1/admin/auditoriums/{room['id']}"

    detail = client.get(url, headers=auth_header(admin_token))
    updated = client.put(
        url,
        json={"name": "Phòng 1A", "rows": 3, "cols": 4, "vipRows": [3]},
        headers=auth_header(admin_token),
    )

    assert detail.status_code == 200
    assert detail.json() == {**room, "vipRows": [4, 5]}
    assert updated.status_code == 200
    assert updated.json() == {
        "id": room["id"],
        "name": "Phòng 1A",
        "rows": 3,
        "cols": 4,
        "seatCount": 12,
        "vipRows": [3],
    }
    assert client.get(url, headers=auth_header(customer_token)).status_code == 403
    missing = f"/api/v1/admin/auditoriums/{uuid4()}"
    assert client.get(missing, headers=auth_header(admin_token)).status_code == 404


def test_auditorium_with_showtimes_is_locked(
    client: TestClient, admin_token: str, setup: dict[str, str]
) -> None:
    create_showtime(client, admin_token, setup, "2026-10-20T19:00:00+07:00")

    response = client.put(
        f"/api/v1/admin/auditoriums/{setup['room']}",
        json={"name": "Phòng 1", "rows": 2, "cols": 2},
        headers=auth_header(admin_token),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"
