from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Barrier
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.bootstrap.settings import Settings
from app.domain.auth.model import Actor, Role
from app.domain.booking.service import BookingService
from app.domain.errors import HoldLimitExceededError, SeatUnavailableError
from app.infrastructure.persistence.uow import SqlAlchemyUnitOfWork, create_session_factory
from tests.api.conftest import auth_header, create_showtime

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
