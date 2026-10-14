from datetime import datetime, timedelta, timezone

import pytest

from cinema_booking.domain.entities import Booking, Movie, Room, Seat, Showtime, Ticket, User
from cinema_booking.domain.enums import BookingStatus, SeatType, UserRole
from cinema_booking.domain.errors import SeatUnavailable
from cinema_booking.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
    create_tables,
)
from cinema_booking.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


@pytest.fixture
def uow_factory(tmp_path):
    engine = create_database_engine(f"sqlite:///{(tmp_path / 'repo.db').as_posix()}")
    create_tables(engine)
    yield lambda: SqlAlchemyUnitOfWork(create_session_factory(engine))
    engine.dispose()


def test_mapping_commit_and_rollback(uow_factory) -> None:
    movie = Movie("m1", "Movie", 90, "Drama", "P")
    with uow_factory() as uow:
        uow.movies.add(movie)
        uow.commit()
    with uow_factory() as uow:
        assert uow.movies.get(movie.id) == movie
        uow.movies.add(Movie("m2", "Rolled back", 100, "Drama", "P"))
    with uow_factory() as uow:
        assert uow.movies.get("m2") is None


def test_ticket_unique_constraint_is_mapped_to_domain_error(uow_factory) -> None:
    now = datetime.now(timezone.utc)
    user = User("u1", "u@example.com", "hash", "User", UserRole.CUSTOMER, now)
    movie = Movie("m1", "Movie", 90, "Drama", "P")
    room = Room("r1", "Room", 1, 1)
    seat = Seat("s1", room.id, "A", 1, SeatType.STANDARD)
    showtime = Showtime(
        "st1", movie.id, room.id, now + timedelta(days=1), now + timedelta(days=1, minutes=90), 100
    )
    with uow_factory() as uow:
        uow.users.add(user)
        uow.movies.add(movie)
        uow.rooms.add(room, [seat])
        uow.showtimes.add(showtime)
        uow.commit()
    for booking_id in ("b1", "b2"):
        booking = Booking(
            booking_id,
            user.id,
            showtime.id,
            BookingStatus.CONFIRMED,
            100,
            now,
            [Ticket(f"t-{booking_id}", booking_id, showtime.id, seat.id, 100)],
        )
        if booking_id == "b1":
            with uow_factory() as uow:
                uow.bookings.add(booking)
                uow.commit()
        else:
            with pytest.raises(SeatUnavailable), uow_factory() as uow:
                uow.bookings.add(booking)
