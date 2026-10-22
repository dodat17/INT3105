from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Barrier
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text, update

from app.bootstrap.settings import Settings
from app.domain.auth.model import Actor, Role
from app.domain.booking.service import BookingService
from app.domain.errors import (
    BookingExpiredError,
    HoldLimitExceededError,
    InvalidBookingStateError,
    SeatUnavailableError,
)
from app.infrastructure.persistence.models import BookingModel, ShowtimeSeatModel
from app.infrastructure.persistence.uow import SqlAlchemyUnitOfWork, create_session_factory
from tests.api.conftest import auth_header, create_showtime, login

REQUESTS = 20


def test_twenty_concurrent_requests_for_one_seat_have_one_winner(
    client: TestClient,
    settings: Settings,
    setup: dict[str, str],
    admin_token: str,
    customer_token: str,
) -> None:
    if not settings.database_url.startswith("postgresql"):
        pytest.skip("needs PostgreSQL row locks; set TEST_DATABASE_URL")
    from datetime import UTC, datetime, timedelta

    showtime = create_showtime(
        client, admin_token, setup, (datetime.now(UTC) + timedelta(days=1)).isoformat()
    ).json()
    seat = client.get(f"/api/v1/showtimes/{showtime['id']}/seats").json()["seats"][0]
    user_id = client.get("/api/v1/auth/me", headers=auth_header(customer_token)).json()["id"]
    session_factory = create_session_factory(settings.database_url, REQUESTS)
    service = BookingService(partial(SqlAlchemyUnitOfWork, session_factory), 300, 2, 5)
    actor = Actor(UUID(user_id), Role.CUSTOMER)
    barrier = Barrier(REQUESTS)

    def attempt() -> str:
        barrier.wait()
        try:
            service.create(actor, UUID(showtime["id"]), [UUID(seat["id"])])
            return "created"
        except SeatUnavailableError:
            return "conflict"

    with ThreadPoolExecutor(REQUESTS) as pool:
        results = sorted(pool.map(lambda _: attempt(), range(REQUESTS)))

    assert results == ["conflict"] * (REQUESTS - 1) + ["created"]
    seat_map = client.get(f"/api/v1/showtimes/{showtime['id']}/seats").json()
    assert next(item for item in seat_map["seats"] if item["id"] == seat["id"])["status"] == "HELD"


def test_concurrent_disjoint_holds_respect_per_showtime_limit(
    client: TestClient,
    settings: Settings,
    setup: dict[str, str],
    admin_token: str,
    customer_token: str,
) -> None:
    if not settings.database_url.startswith("postgresql"):
        pytest.skip("needs PostgreSQL row locks; set TEST_DATABASE_URL")
    from datetime import UTC, datetime, timedelta

    showtime = create_showtime(
        client, admin_token, setup, (datetime.now(UTC) + timedelta(days=1)).isoformat()
    ).json()
    seats = client.get(f"/api/v1/showtimes/{showtime['id']}/seats").json()["seats"]
    user_id = client.get("/api/v1/auth/me", headers=auth_header(customer_token)).json()["id"]
    session_factory = create_session_factory(settings.database_url, REQUESTS)
    service = BookingService(partial(SqlAlchemyUnitOfWork, session_factory), 300, 2, 5)
    actor = Actor(UUID(user_id), Role.CUSTOMER)
    attempts = len(seats)
    barrier = Barrier(attempts)

    def attempt(index: int) -> str:
        barrier.wait()
        try:
            service.create(actor, UUID(showtime["id"]), [UUID(seats[index]["id"])])
            return "created"
        except HoldLimitExceededError:
            return "limit"

    with ThreadPoolExecutor(attempts) as pool:
        results = sorted(pool.map(attempt, range(attempts)))

    assert results == ["created"] * 2 + ["limit"] * (attempts - 2)


def test_overlapping_seat_sets_are_all_or_nothing(
    client: TestClient,
    settings: Settings,
    setup: dict[str, str],
    admin_token: str,
    customer_token: str,
) -> None:
    if not settings.database_url.startswith("postgresql"):
        pytest.skip("needs PostgreSQL row locks; set TEST_DATABASE_URL")
    from datetime import UTC, datetime, timedelta

    showtime = create_showtime(
        client, admin_token, setup, (datetime.now(UTC) + timedelta(days=1)).isoformat()
    ).json()
    seats = client.get(f"/api/v1/showtimes/{showtime['id']}/seats").json()["seats"]
    user_id = client.get("/api/v1/auth/me", headers=auth_header(customer_token)).json()["id"]
    service = BookingService(
        partial(SqlAlchemyUnitOfWork, create_session_factory(settings.database_url, 2)),
        300,
        2,
        5,
    )
    actor = Actor(UUID(user_id), Role.CUSTOMER)
    groups = ([seats[0], seats[1]], [seats[1], seats[2]])
    barrier = Barrier(2)

    def attempt(group: list[dict[str, str]]) -> tuple[str, list[str]]:
        barrier.wait()
        ids = [UUID(seat["id"]) for seat in group]
        try:
            service.create(actor, UUID(showtime["id"]), ids)
            return "created", [str(seat_id) for seat_id in ids]
        except SeatUnavailableError:
            return "conflict", [str(seat_id) for seat_id in ids]

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(attempt, groups))

    assert sorted(result for result, _ in results) == ["conflict", "created"]
    winner = next(ids for result, ids in results if result == "created")
    loser = next(ids for result, ids in results if result == "conflict")
    statuses = {
        seat["id"]: seat["status"]
        for seat in client.get(f"/api/v1/showtimes/{showtime['id']}/seats").json()["seats"]
    }
    assert all(statuses[seat_id] == "HELD" for seat_id in winner)
    assert all(statuses[seat_id] == "AVAILABLE" for seat_id in set(loser) - set(winner))


def test_confirm_and_cancel_race_keeps_inventory_consistent(
    client: TestClient,
    settings: Settings,
    setup: dict[str, str],
    admin_token: str,
    customer_token: str,
) -> None:
    if not settings.database_url.startswith("postgresql"):
        pytest.skip("needs PostgreSQL row locks; set TEST_DATABASE_URL")
    from datetime import UTC, datetime, timedelta

    showtime = create_showtime(
        client, admin_token, setup, (datetime.now(UTC) + timedelta(days=1)).isoformat()
    ).json()
    seat = client.get(f"/api/v1/showtimes/{showtime['id']}/seats").json()["seats"][0]
    booking = client.post(
        "/api/v1/bookings",
        json={"showtimeId": showtime["id"], "seatIds": [seat["id"]]},
        headers=auth_header(customer_token),
    ).json()
    user_id = client.get("/api/v1/auth/me", headers=auth_header(customer_token)).json()["id"]
    service = BookingService(
        partial(SqlAlchemyUnitOfWork, create_session_factory(settings.database_url, 2)),
        300,
        2,
        5,
    )
    actor = Actor(UUID(user_id), Role.CUSTOMER)
    booking_id = UUID(booking["id"])
    barrier = Barrier(2)

    def transition(action: str) -> str:
        barrier.wait()
        try:
            if action == "confirm":
                service.confirm(actor, booking_id)
            else:
                service.cancel(actor, booking_id)
            return action
        except InvalidBookingStateError:
            return "rejected"

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(transition, ["confirm", "cancel"]))

    assert results.count("rejected") == 1
    final = client.get(
        f"/api/v1/bookings/{booking['id']}", headers=auth_header(customer_token)
    ).json()
    seat_status = next(
        item["status"]
        for item in client.get(f"/api/v1/showtimes/{showtime['id']}/seats").json()["seats"]
        if item["id"] == seat["id"]
    )
    assert (final["status"], seat_status) in {
        ("CONFIRMED", "BOOKED"),
        ("CANCELLED", "AVAILABLE"),
    }


def _assert_booking_invariants(settings: Settings) -> None:
    engine = create_engine(settings.database_url)
    with engine.connect() as connection:
        partial_bookings = connection.scalar(
            text(
                "SELECT count(*) FROM bookings b "
                "WHERE (SELECT count(*) FROM booking_items bi WHERE bi.booking_id = b.id) NOT BETWEEN 1 AND 8"  # noqa: E501
            )
        )
        invalid_inventory = connection.scalar(
            text(
                "SELECT count(*) FROM showtime_seats ss LEFT JOIN bookings b ON b.id = ss.booking_id "  # noqa: E501
                "WHERE (ss.state = 'HELD' AND (b.id IS NULL OR b.status <> 'HELD' OR ss.hold_expires_at <> b.expires_at)) "  # noqa: E501
                "OR (ss.state = 'BOOKED' AND (b.id IS NULL OR b.status <> 'CONFIRMED')) "
                "OR (ss.state = 'AVAILABLE' AND (ss.booking_id IS NOT NULL OR ss.hold_expires_at IS NOT NULL))"  # noqa: E501
            )
        )
    engine.dispose()
    assert partial_bookings == 0
    assert invalid_inventory == 0


def test_twenty_different_users_competing_for_one_seat_have_one_winner(
    client: TestClient,
    settings: Settings,
    setup: dict[str, str],
    admin_token: str,
) -> None:
    if not settings.database_url.startswith("postgresql"):
        pytest.skip("needs PostgreSQL row locks; set TEST_DATABASE_URL")
    from datetime import UTC, datetime, timedelta

    showtime = create_showtime(
        client, admin_token, setup, (datetime.now(UTC) + timedelta(days=1)).isoformat()
    ).json()
    seat = client.get(f"/api/v1/showtimes/{showtime['id']}/seats").json()["seats"][0]
    actors: list[Actor] = []
    for index in range(REQUESTS):
        email = f"race-{index}@example.test"
        response = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "secret123", "fullName": f"Race {index}"},
        )
        assert response.status_code == 201
        token = login(client, email)
        user_id = client.get("/api/v1/auth/me", headers=auth_header(token)).json()["id"]
        actors.append(Actor(UUID(user_id), Role.CUSTOMER))

    service = BookingService(
        partial(
            SqlAlchemyUnitOfWork,
            create_session_factory(settings.database_url, REQUESTS),
        ),
        300,
        2,
        5,
    )
    barrier = Barrier(REQUESTS)

    def attempt(actor: Actor) -> str:
        barrier.wait()
        try:
            service.create(actor, UUID(showtime["id"]), [UUID(seat["id"])])
            return "created"
        except SeatUnavailableError:
            return "conflict"

    with ThreadPoolExecutor(REQUESTS) as pool:
        results = sorted(pool.map(attempt, actors))

    assert results == ["conflict"] * (REQUESTS - 1) + ["created"]
    _assert_booking_invariants(settings)


def test_expired_hold_reacquire_cannot_be_confirmed_by_previous_owner(
    client: TestClient,
    settings: Settings,
    setup: dict[str, str],
    admin_token: str,
    customer_token: str,
) -> None:
    if not settings.database_url.startswith("postgresql"):
        pytest.skip("needs PostgreSQL row locks; set TEST_DATABASE_URL")
    from datetime import UTC, datetime, timedelta

    showtime = create_showtime(
        client, admin_token, setup, (datetime.now(UTC) + timedelta(days=1)).isoformat()
    ).json()
    seat = client.get(f"/api/v1/showtimes/{showtime['id']}/seats").json()["seats"][0]
    old_booking = client.post(
        "/api/v1/bookings",
        json={"showtimeId": showtime["id"], "seatIds": [seat["id"]]},
        headers=auth_header(customer_token),
    ).json()
    client.post(
        "/api/v1/auth/register",
        json={"email": "reacquire@example.test", "password": "secret123", "fullName": "New"},
    )
    new_token = login(client, "reacquire@example.test")
    old_user_id = client.get("/api/v1/auth/me", headers=auth_header(customer_token)).json()["id"]
    new_user_id = client.get("/api/v1/auth/me", headers=auth_header(new_token)).json()["id"]
    expired_at = datetime.now(UTC) - timedelta(seconds=1)
    engine = create_engine(settings.database_url)
    with engine.begin() as connection:
        connection.execute(
            update(BookingModel)
            .where(BookingModel.id == UUID(old_booking["id"]))
            .values(expires_at=expired_at)
        )
        connection.execute(
            update(ShowtimeSeatModel)
            .where(
                ShowtimeSeatModel.showtime_id == UUID(showtime["id"]),
                ShowtimeSeatModel.seat_id == UUID(seat["id"]),
            )
            .values(hold_expires_at=expired_at)
        )
    engine.dispose()

    service = BookingService(
        partial(SqlAlchemyUnitOfWork, create_session_factory(settings.database_url, 2)),
        300,
        2,
        5,
    )
    old_actor = Actor(UUID(old_user_id), Role.CUSTOMER)
    new_actor = Actor(UUID(new_user_id), Role.CUSTOMER)
    barrier = Barrier(2)

    def confirm_old() -> str:
        barrier.wait()
        try:
            service.confirm(old_actor, UUID(old_booking["id"]))
            return "confirmed"
        except BookingExpiredError:
            return "expired"

    def reacquire() -> str:
        barrier.wait()
        service.create(new_actor, UUID(showtime["id"]), [UUID(seat["id"])])
        return "reacquired"

    with ThreadPoolExecutor(2) as pool:
        confirm_result = pool.submit(confirm_old)
        reacquire_result = pool.submit(reacquire)
        results = {confirm_result.result(), reacquire_result.result()}

    assert results == {"expired", "reacquired"}
    _assert_booking_invariants(settings)
