from concurrent.futures import ThreadPoolExecutor
from functools import partial
from threading import Barrier
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.bootstrap.settings import Settings
from app.domain.auth.model import Actor, Role
from app.domain.booking.service import BookingService
from app.domain.errors import SeatUnavailableError
from app.infrastructure.persistence.uow import SqlAlchemyUnitOfWork, create_session_factory
from tests.api.conftest import auth_header, create_showtime

REQUESTS = 20


def test_concurrent_requests_for_one_seat_have_exactly_one_winner(
    client: TestClient,
    settings: Settings,
    admin_token: str,
    customer_token: str,
    setup: dict[str, str],
) -> None:
    if not settings.database_url.startswith("postgresql"):
        pytest.skip("Row-lock concurrency requires PostgreSQL")

    showtime = create_showtime(client, admin_token, setup, "2026-10-20T19:00:00+07:00").json()
    seat_id = UUID(client.get(f"/api/v1/showtimes/{showtime['id']}/seats").json()["seats"][0]["id"])
    user_id = UUID(client.get("/api/v1/auth/me", headers=auth_header(customer_token)).json()["id"])
    session_factory = create_session_factory(settings.database_url, REQUESTS)
    service = BookingService(
        partial(SqlAlchemyUnitOfWork, session_factory),
        settings.hold_ttl_seconds,
        settings.hold_max_active_per_showtime,
        settings.hold_max_active_total,
    )
    actor = Actor(user_id, Role.CUSTOMER)
    barrier = Barrier(REQUESTS)

    def attempt() -> str:
        barrier.wait()
        try:
            service.create_booking(actor, UUID(showtime["id"]), [seat_id])
        except SeatUnavailableError:
            return "conflict"
        return "created"

    with ThreadPoolExecutor(max_workers=REQUESTS) as pool:
        results = sorted(pool.map(lambda _: attempt(), range(REQUESTS)))

    assert results == ["conflict"] * (REQUESTS - 1) + ["created"]
    mine = client.get("/api/v1/me/bookings", headers=auth_header(customer_token)).json()
    assert mine["totalItems"] == 1
