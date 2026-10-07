from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import update

from app.bootstrap.settings import Settings
from app.infrastructure.persistence.models import BookingModel, ShowtimeSeatModel
from app.infrastructure.persistence.uow import create_session_factory
from tests.api.conftest import auth_header, create_showtime, login


def _showtime_with_seats(
    client: TestClient,
    admin_token: str,
    setup: dict[str, str],
    starts_at: str = "2026-10-20T19:00:00+07:00",
    **overrides: str,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    showtime = create_showtime(client, admin_token, setup, starts_at, **overrides).json()
    seats = client.get(f"/api/v1/showtimes/{showtime['id']}/seats").json()["seats"]
    return showtime, seats


def _book(client: TestClient, token: str, showtime_id: object, seat_ids: list[object]) -> object:
    return client.post(
        "/api/v1/bookings",
        json={"showtimeId": str(showtime_id), "seatIds": [str(seat_id) for seat_id in seat_ids]},
        headers=auth_header(token),
    )


def test_create_booking_prices_seats_and_marks_them_held(
    client: TestClient,
    admin_token: str,
    customer_token: str,
    setup: dict[str, str],
) -> None:
    showtime, seats = _showtime_with_seats(client, admin_token, setup)
    standard = next(seat for seat in seats if seat["seatType"] == "STANDARD")
    vip = next(seat for seat in seats if seat["seatType"] == "VIP")

    response = _book(client, customer_token, showtime["id"], [standard["id"], vip["id"]])

    assert response.status_code == 201
    body = response.json()
    assert response.headers["Location"] == f"/api/v1/bookings/{body['id']}"
    assert body["status"] == "HELD"
    assert body["currency"] == "VND"
    assert {item["unitPrice"] for item in body["items"]} == {90_000, 117_000}
    assert body["totalAmount"] == 207_000
    seat_map = client.get(f"/api/v1/showtimes/{showtime['id']}/seats").json()["seats"]
    held_ids = {seat["id"] for seat in seat_map if seat["status"] == "HELD"}
    assert held_ids == {standard["id"], vip["id"]}


def test_create_booking_validates_seat_count_duplicates_room_and_start_time(
    client: TestClient,
    admin_token: str,
    customer_token: str,
    setup: dict[str, str],
) -> None:
    showtime, seats = _showtime_with_seats(client, admin_token, setup)
    other_showtime, other_seats = _showtime_with_seats(
        client,
        admin_token,
        setup,
        roomId=setup["other_room"],
    )
    del other_showtime
    started, started_seats = _showtime_with_seats(
        client, admin_token, setup, "2026-10-14T19:00:00+07:00"
    )

    empty = _book(client, customer_token, showtime["id"], [])
    too_many = _book(client, customer_token, showtime["id"], [seat["id"] for seat in seats[:9]])
    duplicate = _book(client, customer_token, showtime["id"], [seats[0]["id"], seats[0]["id"]])
    wrong_room = _book(client, customer_token, showtime["id"], [other_seats[0]["id"]])
    unknown = _book(client, customer_token, showtime["id"], [uuid4()])
    already_started = _book(client, customer_token, started["id"], [started_seats[0]["id"]])

    assert {empty.status_code, too_many.status_code, duplicate.status_code} == {400}
    assert wrong_room.status_code == 400
    assert unknown.status_code == 400
    assert already_started.status_code == 409
    assert already_started.json()["error"]["code"] == "SHOWTIME_NOT_BOOKABLE"
    assert (
        client.get("/api/v1/me/bookings", headers=auth_header(customer_token)).json()["totalItems"]
        == 0
    )


def test_occupied_seat_rejects_the_whole_booking(
    client: TestClient,
    admin_token: str,
    customer_token: str,
    setup: dict[str, str],
) -> None:
    showtime, seats = _showtime_with_seats(client, admin_token, setup)
    occupied, free = seats[:2]
    assert _book(client, customer_token, showtime["id"], [occupied["id"]]).status_code == 201

    response = _book(client, customer_token, showtime["id"], [occupied["id"], free["id"]])

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SEAT_UNAVAILABLE"
    assert response.json()["error"]["details"] == {"seatIds": [occupied["id"]]}
    seat_map = client.get(f"/api/v1/showtimes/{showtime['id']}/seats").json()["seats"]
    assert next(seat for seat in seat_map if seat["id"] == free["id"])["status"] == "AVAILABLE"


def test_confirm_is_idempotent_and_confirmed_booking_cannot_be_cancelled(
    client: TestClient,
    admin_token: str,
    customer_token: str,
    setup: dict[str, str],
) -> None:
    showtime, seats = _showtime_with_seats(client, admin_token, setup)
    booking = _book(client, customer_token, showtime["id"], [seats[0]["id"]]).json()
    url = f"/api/v1/bookings/{booking['id']}"

    first = client.post(f"{url}/confirm", headers=auth_header(customer_token))
    second = client.post(f"{url}/confirm", headers=auth_header(customer_token))
    cancelled = client.delete(url, headers=auth_header(customer_token))

    assert first.status_code == second.status_code == 200
    assert first.json()["status"] == "CONFIRMED"
    assert first.json()["bookingCode"] == second.json()["bookingCode"]
    assert cancelled.status_code == 409
    assert cancelled.json()["error"]["code"] == "INVALID_BOOKING_STATE"
    cannot_delete = client.delete(
        f"/api/v1/showtimes/{showtime['id']}", headers=auth_header(admin_token)
    )
    assert cannot_delete.status_code == 400
    seat_map = client.get(f"/api/v1/showtimes/{showtime['id']}/seats").json()["seats"]
    assert next(seat for seat in seat_map if seat["id"] == seats[0]["id"])["status"] == "BOOKED"


def test_cancel_keeps_ticket_history_and_releases_seat(
    client: TestClient,
    admin_token: str,
    customer_token: str,
    setup: dict[str, str],
) -> None:
    showtime, seats = _showtime_with_seats(client, admin_token, setup)
    booking = _book(client, customer_token, showtime["id"], [seats[0]["id"]]).json()
    url = f"/api/v1/bookings/{booking['id']}"

    assert client.delete(url, headers=auth_header(customer_token)).status_code == 204
    assert client.delete(url, headers=auth_header(customer_token)).status_code == 204
    detail = client.get(url, headers=auth_header(customer_token)).json()
    replacement = _book(client, customer_token, showtime["id"], [seats[0]["id"]])

    assert detail["status"] == "CANCELLED"
    assert detail["items"] == booking["items"]
    assert replacement.status_code == 201


def test_owner_is_hidden_from_other_customers_but_admin_can_lookup(
    client: TestClient,
    admin_token: str,
    customer_token: str,
    setup: dict[str, str],
) -> None:
    showtime, seats = _showtime_with_seats(client, admin_token, setup)
    booking = _book(client, customer_token, showtime["id"], [seats[0]["id"]]).json()
    client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.test", "password": "secret123", "fullName": "Khác"},
    )
    other_token = login(client, "other@example.test")
    url = f"/api/v1/bookings/{booking['id']}"

    assert client.get(url, headers=auth_header(other_token)).status_code == 404
    assert client.delete(url, headers=auth_header(other_token)).status_code == 404
    assert client.post(f"{url}/confirm", headers=auth_header(other_token)).status_code == 404
    detail = client.get(url, headers=auth_header(admin_token))
    assert detail.status_code == 200
    assert detail.json()["movie"]["title"] == "Mai"
    assert detail.json()["room"]["name"] == "Phòng 1"
    assert detail.json()["seats"][0]["seatId"] == seats[0]["id"]
    assert client.delete(url, headers=auth_header(admin_token)).status_code == 204


def test_active_hold_limits_apply_per_showtime_and_globally(
    client: TestClient,
    admin_token: str,
    customer_token: str,
    setup: dict[str, str],
) -> None:
    first, seats = _showtime_with_seats(client, admin_token, setup)
    second, _ = _showtime_with_seats(client, admin_token, setup, "2026-10-20T21:00:00+07:00")
    third, _ = _showtime_with_seats(client, admin_token, setup, "2026-10-20T23:00:00+07:00")

    assert _book(client, customer_token, first["id"], [seats[0]["id"]]).status_code == 201
    assert _book(client, customer_token, first["id"], [seats[1]["id"]]).status_code == 201
    per_showtime = _book(client, customer_token, first["id"], [seats[2]["id"]])
    assert per_showtime.status_code == 409
    assert per_showtime.json()["error"]["code"] == "HOLD_LIMIT_EXCEEDED"

    assert _book(client, customer_token, second["id"], [seats[0]["id"]]).status_code == 201
    assert _book(client, customer_token, second["id"], [seats[1]["id"]]).status_code == 201
    assert _book(client, customer_token, third["id"], [seats[0]["id"]]).status_code == 201
    global_limit = _book(client, customer_token, third["id"], [seats[1]["id"]])
    assert global_limit.status_code == 409
    assert global_limit.json()["error"]["code"] == "HOLD_LIMIT_EXCEEDED"


def test_my_bookings_supports_status_filter_and_pagination(
    client: TestClient,
    admin_token: str,
    customer_token: str,
    setup: dict[str, str],
) -> None:
    showtime, seats = _showtime_with_seats(client, admin_token, setup)
    confirmed = _book(client, customer_token, showtime["id"], [seats[0]["id"]]).json()
    client.post(f"/api/v1/bookings/{confirmed['id']}/confirm", headers=auth_header(customer_token))
    cancelled = _book(client, customer_token, showtime["id"], [seats[1]["id"]]).json()
    client.delete(f"/api/v1/bookings/{cancelled['id']}", headers=auth_header(customer_token))

    confirmed_page = client.get(
        "/api/v1/me/bookings",
        params={"status": "CONFIRMED", "pageSize": 1},
        headers=auth_header(customer_token),
    ).json()
    empty_page = client.get(
        "/api/v1/me/bookings",
        params={"page": 99},
        headers=auth_header(customer_token),
    ).json()

    assert confirmed_page["totalItems"] == 1
    assert [item["id"] for item in confirmed_page["items"]] == [confirmed["id"]]
    assert empty_page["items"] == []
    assert empty_page["totalItems"] == 2
    assert (
        client.get(
            "/api/v1/me/bookings",
            params={"status": "INVALID"},
            headers=auth_header(customer_token),
        ).status_code
        == 400
    )


def test_expired_hold_reads_available_and_can_be_booked_again(
    client: TestClient,
    settings: Settings,
    admin_token: str,
    customer_token: str,
    setup: dict[str, str],
) -> None:
    showtime, seats = _showtime_with_seats(client, admin_token, setup)
    booking = _book(client, customer_token, showtime["id"], [seats[0]["id"]]).json()
    expired_at = datetime(2020, 1, 1, tzinfo=UTC)
    session_factory = create_session_factory(settings.database_url, 1)
    with session_factory.begin() as session:
        session.execute(
            update(BookingModel)
            .where(BookingModel.id == UUID(booking["id"]))
            .values(expires_at=expired_at)
        )
        session.execute(
            update(ShowtimeSeatModel)
            .where(
                ShowtimeSeatModel.showtime_id == UUID(str(showtime["id"])),
                ShowtimeSeatModel.seat_id == UUID(str(seats[0]["id"])),
            )
            .values(hold_expires_at=expired_at)
        )

    detail = client.get(
        f"/api/v1/bookings/{booking['id']}", headers=auth_header(customer_token)
    ).json()
    held = client.get(
        "/api/v1/me/bookings",
        params={"status": "HELD"},
        headers=auth_header(customer_token),
    ).json()
    expired = client.get(
        "/api/v1/me/bookings",
        params={"status": "EXPIRED"},
        headers=auth_header(customer_token),
    ).json()
    seat_map = client.get(f"/api/v1/showtimes/{showtime['id']}/seats").json()["seats"]
    replacement = _book(client, customer_token, showtime["id"], [seats[0]["id"]])

    assert detail["status"] == "EXPIRED"
    assert held["totalItems"] == 0
    assert [item["id"] for item in expired["items"]] == [booking["id"]]
    assert next(seat for seat in seat_map if seat["id"] == seats[0]["id"])["status"] == "AVAILABLE"
    assert replacement.status_code == 201
