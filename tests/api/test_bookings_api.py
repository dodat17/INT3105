from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, update

from app.bootstrap.settings import Settings
from app.infrastructure.persistence.models import BookingModel, ShowtimeModel
from tests.api.conftest import auth_header, create_showtime


def _future_start() -> str:
    return (datetime.now(UTC) + timedelta(days=1)).isoformat()


def _showtime_and_seats(
    client: TestClient, admin_token: str, setup: dict[str, str]
) -> tuple[str, list[str]]:
    showtime = create_showtime(client, admin_token, setup, _future_start()).json()
    seat_map = client.get(f"/api/v1/showtimes/{showtime['id']}/seats").json()
    return showtime["id"], [seat["id"] for seat in seat_map["seats"]]


def test_customer_holds_and_confirms_seats(
    client: TestClient, admin_token: str, customer_token: str, setup: dict[str, str]
) -> None:
    showtime_id, seats = _showtime_and_seats(client, admin_token, setup)

    created = client.post(
        "/api/v1/bookings",
        json={"showtimeId": showtime_id, "seatIds": seats[:2]},
        headers=auth_header(customer_token),
    )

    assert created.status_code == 201, created.text
    booking = created.json()
    assert booking["status"] == "HELD"
    assert booking["currency"] == "VND"
    assert len(booking["items"]) == 2
    assert booking["totalAmount"] == sum(item["unitPrice"] for item in booking["items"])
    assert created.headers["location"] == f"/api/v1/bookings/{booking['id']}"

    confirmed = client.post(
        f"/api/v1/bookings/{booking['id']}/confirm", headers=auth_header(customer_token)
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "CONFIRMED"
    assert confirmed.json()["bookingCode"]

    replay = client.post(
        f"/api/v1/bookings/{booking['id']}/confirm", headers=auth_header(customer_token)
    )
    assert replay.status_code == 200
    assert replay.json()["bookingCode"] == confirmed.json()["bookingCode"]


def test_occupied_seat_returns_conflict_without_partial_hold(
    client: TestClient, admin_token: str, customer_token: str, setup: dict[str, str]
) -> None:
    showtime_id, seats = _showtime_and_seats(client, admin_token, setup)
    first = client.post(
        "/api/v1/bookings",
        json={"showtimeId": showtime_id, "seatIds": [seats[0]]},
        headers=auth_header(customer_token),
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/bookings",
        json={"showtimeId": showtime_id, "seatIds": [seats[0], seats[1]]},
        headers=auth_header(customer_token),
    )

    assert second.status_code == 409
    assert second.json()["error"]["code"] == "SEAT_UNAVAILABLE"
    assert second.json()["error"]["details"]["seatIds"] == [seats[0]]
    seat_map = client.get(f"/api/v1/showtimes/{showtime_id}/seats").json()
    statuses = {seat["id"]: seat["status"] for seat in seat_map["seats"]}
    assert statuses[seats[0]] == "HELD"
    assert statuses[seats[1]] == "AVAILABLE"


def test_owner_lists_views_and_cancels_booking(
    client: TestClient, admin_token: str, customer_token: str, setup: dict[str, str]
) -> None:
    showtime_id, seats = _showtime_and_seats(client, admin_token, setup)
    created = client.post(
        "/api/v1/bookings",
        json={"showtimeId": showtime_id, "seatIds": [seats[0]]},
        headers=auth_header(customer_token),
    ).json()

    listed = client.get("/api/v1/me/bookings", headers=auth_header(customer_token))
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [created["id"]]

    detail = client.get(f"/api/v1/bookings/{created['id']}", headers=auth_header(customer_token))
    assert detail.status_code == 200
    assert detail.json()["items"][0]["seatId"] == seats[0]
    assert detail.json()["movie"]["id"] == setup["movie"]
    assert detail.json()["auditorium"]["id"] == setup["room"]
    assert detail.json()["showtime"]["id"] == showtime_id
    assert detail.json()["seats"] == [
        {
            "seatId": seats[0],
            "rowLabel": "A",
            "seatNumber": 1,
            "unitPrice": 90000,
        }
    ]

    cancelled = client.delete(
        f"/api/v1/bookings/{created['id']}", headers=auth_header(customer_token)
    )
    assert cancelled.status_code == 204
    assert (
        client.delete(
            f"/api/v1/bookings/{created['id']}", headers=auth_header(customer_token)
        ).status_code
        == 204
    )

    seat_map = client.get(f"/api/v1/showtimes/{showtime_id}/seats").json()
    assert (
        next(seat for seat in seat_map["seats"] if seat["id"] == seats[0])["status"] == "AVAILABLE"
    )

    rebooked = client.post(
        "/api/v1/bookings",
        json={"showtimeId": showtime_id, "seatIds": [seats[0]]},
        headers=auth_header(customer_token),
    )
    assert rebooked.status_code == 201


def test_booking_validation_and_owner_hiding(
    client: TestClient, admin_token: str, customer_token: str, setup: dict[str, str]
) -> None:
    showtime_id, seats = _showtime_and_seats(client, admin_token, setup)
    duplicate = client.post(
        "/api/v1/bookings",
        json={"showtimeId": showtime_id, "seatIds": [seats[0], seats[0]]},
        headers=auth_header(customer_token),
    )
    assert duplicate.status_code == 400
    assert duplicate.json()["error"]["code"] == "VALIDATION_ERROR"
    assert duplicate.json()["error"]["details"] == {"fields": ["seatIds"]}

    booking = client.post(
        "/api/v1/bookings",
        json={"showtimeId": showtime_id, "seatIds": [seats[0]]},
        headers=auth_header(customer_token),
    ).json()
    client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.test", "password": "secret123", "fullName": "Other"},
    )
    from tests.api.conftest import login

    other_token = login(client, "other@example.test")

    hidden = client.get(f"/api/v1/bookings/{booking['id']}", headers=auth_header(other_token))
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    hidden_from_admin = client.get(
        f"/api/v1/bookings/{booking['id']}", headers=auth_header(admin_token)
    )
    assert hidden_from_admin.status_code == 404
    assert hidden_from_admin.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert (
        client.delete(
            f"/api/v1/bookings/{booking['id']}", headers=auth_header(other_token)
        ).status_code
        == 404
    )


def test_confirmed_booking_cannot_be_cancelled(
    client: TestClient, admin_token: str, customer_token: str, setup: dict[str, str]
) -> None:
    showtime_id, seats = _showtime_and_seats(client, admin_token, setup)
    booking = client.post(
        "/api/v1/bookings",
        json={"showtimeId": showtime_id, "seatIds": [seats[0]]},
        headers=auth_header(customer_token),
    ).json()
    client.post(f"/api/v1/bookings/{booking['id']}/confirm", headers=auth_header(customer_token))

    response = client.delete(
        f"/api/v1/bookings/{booking['id']}", headers=auth_header(customer_token)
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_BOOKING_STATE"


def test_list_filters_on_effective_status_in_database(
    client: TestClient,
    settings: Settings,
    admin_token: str,
    customer_token: str,
    setup: dict[str, str],
) -> None:
    showtime_id, seats = _showtime_and_seats(client, admin_token, setup)

    def hold(seat_id: str) -> dict[str, object]:
        response = client.post(
            "/api/v1/bookings",
            json={"showtimeId": showtime_id, "seatIds": [seat_id]},
            headers=auth_header(customer_token),
        )
        assert response.status_code == 201, response.text
        return response.json()

    active = hold(seats[0])
    confirmed = hold(seats[1])
    client.post(
        f"/api/v1/bookings/{confirmed['id']}/confirm",
        headers=auth_header(customer_token),
    )
    expired = hold(seats[2])
    engine = create_engine(settings.database_url)
    with engine.begin() as connection:
        connection.execute(
            update(BookingModel)
            .where(BookingModel.id == UUID(str(expired["id"])))
            .values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
        )
    engine.dispose()

    cancelled = hold(seats[3])
    client.delete(f"/api/v1/bookings/{cancelled['id']}", headers=auth_header(customer_token))

    expected = {
        "HELD": {active["id"]},
        "EXPIRED": {expired["id"]},
        "CONFIRMED": {confirmed["id"]},
        "CANCELLED": {cancelled["id"]},
    }
    for status, ids in expected.items():
        response = client.get(
            "/api/v1/me/bookings",
            params={"status": status},
            headers=auth_header(customer_token),
        )
        assert response.status_code == 200
        assert {item["id"] for item in response.json()["items"]} == ids
        assert response.json()["totalItems"] == 1

    page = client.get(
        "/api/v1/me/bookings",
        params={"page": 2, "pageSize": 2},
        headers=auth_header(customer_token),
    )
    assert page.status_code == 200
    assert page.json()["totalItems"] == 4
    assert len(page.json()["items"]) == 2

    unfiltered = client.get("/api/v1/me/bookings", headers=auth_header(customer_token)).json()[
        "items"
    ]
    expired_item = next(item for item in unfiltered if item["id"] == expired["id"])
    assert expired_item["status"] == "EXPIRED"


def test_closed_showtime_rejects_new_booking(
    client: TestClient,
    settings: Settings,
    admin_token: str,
    customer_token: str,
    setup: dict[str, str],
) -> None:
    showtime_id, seats = _showtime_and_seats(client, admin_token, setup)
    engine = create_engine(settings.database_url)
    with engine.begin() as connection:
        connection.execute(
            update(ShowtimeModel)
            .where(ShowtimeModel.id == UUID(showtime_id))
            .values(is_open_for_booking=False)
        )
    engine.dispose()

    response = client.post(
        "/api/v1/bookings",
        json={"showtimeId": showtime_id, "seatIds": [seats[0]]},
        headers=auth_header(customer_token),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SHOWTIME_NOT_BOOKABLE"


def test_booking_rejects_invalid_seat_sets_and_started_showtime(
    client: TestClient, admin_token: str, customer_token: str, setup: dict[str, str]
) -> None:
    showtime_id, seats = _showtime_and_seats(client, admin_token, setup)
    for seat_ids in ([], seats[:9]):
        response = client.post(
            "/api/v1/bookings",
            json={"showtimeId": showtime_id, "seatIds": seat_ids},
            headers=auth_header(customer_token),
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
        assert response.json()["error"]["details"] == {"fields": ["seatIds"]}

    other_showtime = create_showtime(
        client, admin_token, setup, _future_start(), auditoriumId=setup["other_room"]
    ).json()
    other_seat = client.get(f"/api/v1/showtimes/{other_showtime['id']}/seats").json()["seats"][0][
        "id"
    ]
    wrong_room = client.post(
        "/api/v1/bookings",
        json={"showtimeId": showtime_id, "seatIds": [other_seat]},
        headers=auth_header(customer_token),
    )
    assert wrong_room.status_code == 400
    assert wrong_room.json()["error"]["code"] == "VALIDATION_ERROR"
    assert wrong_room.json()["error"]["details"] == {"fields": ["seatIds"]}

    started = create_showtime(
        client,
        admin_token,
        setup,
        (datetime.now(UTC) - timedelta(hours=3)).isoformat(),
    ).json()
    started_seat = client.get(f"/api/v1/showtimes/{started['id']}/seats").json()["seats"][0]["id"]
    response = client.post(
        "/api/v1/bookings",
        json={"showtimeId": started["id"], "seatIds": [started_seat]},
        headers=auth_header(customer_token),
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SHOWTIME_NOT_BOOKABLE"


def test_admin_looks_up_any_booking(
    client: TestClient, admin_token: str, customer_token: str, setup: dict[str, str]
) -> None:
    showtime_id, seats = _showtime_and_seats(client, admin_token, setup)
    booking = client.post(
        "/api/v1/bookings",
        json={"showtimeId": showtime_id, "seatIds": seats[:1]},
        headers=auth_header(customer_token),
    ).json()
    user_id = client.get("/api/v1/auth/me", headers=auth_header(customer_token)).json()["id"]

    listing = client.get(
        "/api/v1/admin/bookings",
        params={"showtimeId": showtime_id, "status": "HELD"},
        headers=auth_header(admin_token),
    )
    other_user = client.get(
        "/api/v1/admin/bookings",
        params={"userId": setup["movie"]},
        headers=auth_header(admin_token),
    )
    detail = client.get(f"/api/v1/admin/bookings/{booking['id']}", headers=auth_header(admin_token))

    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()["items"]] == [booking["id"]]
    assert listing.json()["items"][0]["userId"] == user_id
    assert other_user.json()["totalItems"] == 0
    assert detail.status_code == 200
    assert detail.json()["userId"] == user_id
    assert detail.json()["auditorium"]["id"] == setup["room"]
    customer = auth_header(customer_token)
    assert client.get("/api/v1/admin/bookings", headers=customer).status_code == 403
    assert (
        client.get(f"/api/v1/admin/bookings/{booking['id']}", headers=customer).status_code == 403
    )
    missing = f"/api/v1/admin/bookings/{setup['movie']}"
    assert client.get(missing, headers=auth_header(admin_token)).status_code == 404
