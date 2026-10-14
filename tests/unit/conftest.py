from datetime import datetime, timedelta, timezone

import pytest

from cinema_booking.domain.entities import Movie, Room, Seat, Showtime, User
from cinema_booking.domain.enums import SeatType, UserRole
from tests.unit.fakes import FakeClock, FakeUnitOfWork


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(datetime(2026, 1, 1, 12, tzinfo=timezone.utc))


@pytest.fixture
def admin(clock: FakeClock) -> User:
    return User("admin", "admin@example.com", "hash", "Admin", UserRole.ADMIN, clock.now())


@pytest.fixture
def customer(clock: FakeClock) -> User:
    return User("user", "user@example.com", "hash", "User", UserRole.CUSTOMER, clock.now())


@pytest.fixture
def cinema_data(uow: FakeUnitOfWork, clock: FakeClock):
    movie = Movie("movie", "Test Movie", 120, "Drama", "P", None)
    room = Room("room", "Room 1", 1, 3)
    seats = [
        Seat("s1", room.id, "A", 1, SeatType.STANDARD),
        Seat("s2", room.id, "A", 2, SeatType.VIP),
        Seat("s3", room.id, "A", 3, SeatType.STANDARD),
    ]
    showtime = Showtime(
        "showtime",
        movie.id,
        room.id,
        clock.now() + timedelta(hours=2),
        clock.now() + timedelta(hours=4),
        100_000,
    )
    uow.movies.items[movie.id] = movie
    uow.rooms.items[room.id] = room
    uow.rooms.seats.update({seat.id: seat for seat in seats})
    uow.showtimes.items[showtime.id] = showtime
    return movie, room, seats, showtime
