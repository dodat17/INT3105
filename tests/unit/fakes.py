from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
from types import TracebackType

from cinema_booking.domain.entities import Booking, Movie, Room, Seat, Showtime, User
from cinema_booking.domain.enums import BookingStatus
from cinema_booking.domain.errors import SeatUnavailable


class FakeUserRepository:
    def __init__(self) -> None:
        self.items: dict[str, User] = {}

    def get(self, user_id: str) -> User | None:
        return self.items.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        return next((user for user in self.items.values() if user.email == email), None)

    def add(self, user: User) -> None:
        self.items[user.id] = user


class FakeMovieRepository:
    def __init__(self) -> None:
        self.items: dict[str, Movie] = {}
        self.blocked_ids: set[str] = set()

    def get(self, movie_id: str) -> Movie | None:
        return self.items.get(movie_id)

    def list(self, search: str | None, offset: int, limit: int) -> list[Movie]:
        movies = list(self.items.values())
        if search:
            movies = [movie for movie in movies if search.lower() in movie.title.lower()]
        return movies[offset : offset + limit]

    def add(self, movie: Movie) -> None:
        self.items[movie.id] = movie

    def delete(self, movie_id: str) -> None:
        self.items.pop(movie_id)

    def has_confirmed_bookings(self, movie_id: str) -> bool:
        return movie_id in self.blocked_ids


class FakeRoomRepository:
    def __init__(self) -> None:
        self.items: dict[str, Room] = {}
        self.seats: dict[str, Seat] = {}

    def get(self, room_id: str) -> Room | None:
        return self.items.get(room_id)

    def list(self) -> list[Room]:
        return list(self.items.values())

    def add(self, room: Room, seats: list[Seat]) -> None:
        self.items[room.id] = room
        self.seats.update({seat.id: seat for seat in seats})

    def get_seats(self, room_id: str) -> list[Seat]:
        return [seat for seat in self.seats.values() if seat.room_id == room_id]

    def get_seats_by_ids(self, seat_ids: list[str]) -> list[Seat]:
        return [self.seats[seat_id] for seat_id in seat_ids if seat_id in self.seats]


class FakeShowtimeRepository:
    def __init__(self) -> None:
        self.items: dict[str, Showtime] = {}
        self.blocked_ids: set[str] = set()

    def get(self, showtime_id: str) -> Showtime | None:
        return self.items.get(showtime_id)

    def list(self, movie_id: str | None, on_date: date | None) -> list[Showtime]:
        values = list(self.items.values())
        if movie_id:
            values = [item for item in values if item.movie_id == movie_id]
        if on_date:
            values = [item for item in values if item.starts_at.date() == on_date]
        return values

    def add(self, showtime: Showtime) -> None:
        self.items[showtime.id] = showtime

    def delete(self, showtime_id: str) -> None:
        self.items.pop(showtime_id)

    def find_overlaps(
        self, room_id: str, starts_at: datetime, ends_at: datetime
    ) -> list[Showtime]:
        return [
            item
            for item in self.items.values()
            if item.room_id == room_id and item.starts_at < ends_at and item.ends_at > starts_at
        ]

    def has_confirmed_bookings(self, showtime_id: str) -> bool:
        return showtime_id in self.blocked_ids


class FakeBookingRepository:
    def __init__(self) -> None:
        self.items: dict[str, Booking] = {}

    def get(self, booking_id: str) -> Booking | None:
        booking = self.items.get(booking_id)
        return deepcopy(booking) if booking else None

    def list_for_user(self, user_id: str) -> list[Booking]:
        return [deepcopy(item) for item in self.items.values() if item.user_id == user_id]

    def booked_seat_ids(self, showtime_id: str) -> set[str]:
        return {
            ticket.seat_id
            for item in self.items.values()
            if item.showtime_id == showtime_id and item.status is BookingStatus.CONFIRMED
            for ticket in item.tickets
        }

    def add(self, booking: Booking) -> None:
        if self.booked_seat_ids(booking.showtime_id).intersection(
            ticket.seat_id for ticket in booking.tickets
        ):
            raise SeatUnavailable("Seat is unavailable")
        self.items[booking.id] = deepcopy(booking)

    def cancel(self, booking: Booking) -> None:
        booking.tickets = []
        self.items[booking.id] = deepcopy(booking)


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.users = FakeUserRepository()
        self.movies = FakeMovieRepository()
        self.rooms = FakeRoomRepository()
        self.showtimes = FakeShowtimeRepository()
        self.bookings = FakeBookingRepository()
        self.committed = False

    def __enter__(self):
        self.committed = False
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_value: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        return None

    def commit(self) -> None:
        self.committed = True


class FakeClock:
    def __init__(self, value: datetime | None = None) -> None:
        self.value = value or datetime(2026, 1, 1, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self.value


class FakeHasher:
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == self.hash(password)


class FakeTokenService:
    def issue(self, user: User) -> tuple[str, int]:
        return f"token:{user.id}:{user.role.value}", 3600

    def decode(self, token: str) -> dict[str, str]:
        _, user_id, role = token.split(":")
        return {"sub": user_id, "role": role}
