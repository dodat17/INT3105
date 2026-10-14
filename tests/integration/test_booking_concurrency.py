import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from cinema_booking.domain.entities import Movie, Room, Seat, Showtime, User
from cinema_booking.domain.enums import SeatType, UserRole
from cinema_booking.domain.errors import SeatUnavailable
from cinema_booking.domain.services.booking_service import BookingService
from cinema_booking.infrastructure.clock import SystemClock
from cinema_booking.infrastructure.database.models import TicketModel
from cinema_booking.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
    create_tables,
)
from cinema_booking.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

DATABASE_URL = os.environ.get("TEST_POSTGRES_URL")


@pytest.mark.skipif(not DATABASE_URL, reason="TEST_POSTGRES_URL is not configured")
def test_only_one_concurrent_booking_wins() -> None:
    engine = create_database_engine(DATABASE_URL)
    create_tables(engine)
    factory = create_session_factory(engine)
    suffix = str(uuid4())
    now = datetime.now(timezone.utc)
    user = User(suffix, f"{suffix}@example.com", "hash", "User", UserRole.CUSTOMER, now)
    movie = Movie(str(uuid4()), "Concurrent Movie", 90, "Drama", "P")
    room = Room(str(uuid4()), f"Room {suffix}", 1, 1)
    seat = Seat(str(uuid4()), room.id, "A", 1, SeatType.STANDARD)
    showtime = Showtime(
        str(uuid4()),
        movie.id,
        room.id,
        now + timedelta(days=1),
        now + timedelta(days=1, minutes=90),
        100_000,
    )
    with SqlAlchemyUnitOfWork(factory) as uow:
        uow.users.add(user)
        uow.movies.add(movie)
        uow.rooms.add(room, [seat])
        uow.showtimes.add(showtime)
        uow.commit()

    barrier = threading.Barrier(8)

    def book() -> str:
        barrier.wait()
        try:
            BookingService(SqlAlchemyUnitOfWork(factory), SystemClock()).create(
                user, showtime.id, [seat.id]
            )
            return "created"
        except SeatUnavailable:
            return "conflict"

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _index: book(), range(8)))

    with factory() as session:
        ticket_count = session.scalar(
            select(func.count()).select_from(TicketModel).where(
                TicketModel.showtime_id == showtime.id,
                TicketModel.seat_id == seat.id,
            )
        )
    engine.dispose()
    assert results.count("created") == 1
    assert results.count("conflict") == 7
    assert ticket_count == 1
