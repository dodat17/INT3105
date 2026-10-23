from fastapi.testclient import TestClient

from tests.api.conftest import auth_header, create_room


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
