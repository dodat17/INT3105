from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from functools import partial
from threading import Barrier
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app.bootstrap.settings import Settings
from app.domain.auth.model import Actor, Role
from app.domain.errors import ShowtimeOverlapError
from app.domain.scheduling.service import ShowtimeService
from app.infrastructure.persistence.uow import SqlAlchemyUnitOfWork, create_session_factory

REQUESTS = 8
ROUNDS = 10  # a missing lock lets two through in at least one round


def test_concurrent_overlapping_showtimes_only_one_wins(
    client: TestClient, settings: Settings, setup: dict[str, str]
) -> None:
    """BR-04 under concurrency: the room row lock lets only one overlapping showtime in.

    Calls the service from real threads with their own DB connections; going through
    TestClient would serialize the requests and hide the race.
    """
    if not settings.database_url.startswith("postgresql"):
        pytest.skip("needs PostgreSQL row locks; set TEST_DATABASE_URL")
    session_factory = create_session_factory(settings.database_url, REQUESTS)
    service = ShowtimeService(partial(SqlAlchemyUnitOfWork, session_factory), ZoneInfo("UTC"))
    admin = Actor(uuid4(), Role.ADMIN)
    barrier = Barrier(REQUESTS)

    def attempt(base: datetime, minute: int) -> str:
        barrier.wait()
        try:
            service.create_showtime(
                admin,
                movie_id=UUID(setup["movie"]),
                room_id=UUID(setup["room"]),
                starts_at=base + timedelta(minutes=minute),
                base_price=90_000,
            )
            return "created"
        except ShowtimeOverlapError:
            return "overlap"

    with ThreadPoolExecutor(REQUESTS) as pool:
        for round_ in range(ROUNDS):
            base = datetime(2026, 10, 20, tzinfo=UTC) + timedelta(hours=3 * round_)
            results = sorted(pool.map(partial(attempt, base), range(REQUESTS)))
            assert results == ["created"] + ["overlap"] * (REQUESTS - 1), f"round {round_}"

    assert client.get("/api/v1/showtimes").json()["totalItems"] == ROUNDS
