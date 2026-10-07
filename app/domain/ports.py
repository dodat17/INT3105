from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from app.domain.auth.model import Actor, IssuedToken, Role, User
from app.domain.booking.model import Booking
from app.domain.catalog.model import Movie
from app.domain.cinema.model import Room, Seat
from app.domain.scheduling.model import Showtime


@dataclass(frozen=True)
class Page[T]:
    items: list[T]
    page: int
    page_size: int
    total_items: int


class UserRepository(Protocol):
    def get(self, user_id: UUID) -> User | None: ...
    def get_by_email(self, email: str) -> User | None: ...
    def lock(self, user_id: UUID) -> User | None: ...

    def add(self, user: User) -> None:
        """Raise EmailAlreadyUsedError when the email is taken (BR-01)."""


class MovieRepository(Protocol):
    def get(self, movie_id: UUID) -> Movie | None: ...
    def search(self, query: str | None, page: int, page_size: int) -> Page[Movie]: ...
    def add(self, movie: Movie) -> None: ...
    def delete(self, movie_id: UUID) -> None: ...


class RoomRepository(Protocol):
    def get(self, room_id: UUID) -> Room | None: ...
    def get_by_name(self, name: str) -> Room | None: ...
    def list_all(self) -> list[Room]: ...

    def lock(self, room_id: UUID) -> Room | None:
        """Get the room and hold a row lock until the transaction ends (BR-04)."""

    def add(self, room: Room, seats: list[Seat]) -> None:
        """Raise RoomNameAlreadyUsedError when the name is taken."""

    def seats(self, room_id: UUID) -> list[Seat]:
        """Seats ordered by row label, then number."""


class ShowtimeRepository(Protocol):
    def get(self, showtime_id: UUID) -> Showtime | None: ...

    def search(
        self,
        movie_id: UUID | None,
        starts_from: datetime | None,
        starts_before: datetime | None,
        page: int,
        page_size: int,
    ) -> Page[Showtime]:
        """Ordered by starts_at, then id."""

    def find_overlapping(
        self, room_id: UUID, starts_at: datetime, ends_at: datetime
    ) -> list[Showtime]: ...

    def exists_for_movie(self, movie_id: UUID) -> bool: ...
    def add(self, showtime: Showtime) -> None: ...
    def delete(self, showtime_id: UUID) -> None: ...


class BookingRepository(Protocol):
    def get(self, booking_id: UUID) -> Booking | None: ...
    def get_for_update(self, booking_id: UUID) -> Booking | None: ...

    def search(
        self,
        user_id: UUID,
        status: str | None,
        now: datetime,
        page: int,
        page_size: int,
    ) -> Page[Booking]: ...

    def add(self, booking: Booking) -> None: ...
    def flush(self) -> None: ...
    def count_active_holds(
        self, user_id: UUID, showtime_id: UUID, now: datetime
    ) -> tuple[int, int]: ...
    def lock_inventory(self, showtime_id: UUID, seat_ids: list[UUID]) -> int: ...

    def acquire_holds(
        self,
        showtime_id: UUID,
        seat_ids: list[UUID],
        booking_id: UUID,
        expires_at: datetime,
        now: datetime,
    ) -> list[UUID]: ...

    def mark_booked(self, booking_id: UUID, now: datetime) -> int: ...
    def release_holds(self, booking_id: UUID) -> int: ...
    def confirm(self, booking_id: UUID, confirmed_at: datetime, booking_code: str) -> None: ...
    def cancel(self, booking_id: UUID, cancelled_at: datetime) -> None: ...
    def seat_statuses(self, showtime_id: UUID, now: datetime) -> dict[UUID, str]: ...
    def exists_for_showtime(self, showtime_id: UUID) -> bool: ...


class UnitOfWork(Protocol):
    @property
    def users(self) -> UserRepository: ...
    @property
    def movies(self) -> MovieRepository: ...
    @property
    def rooms(self) -> RoomRepository: ...
    @property
    def showtimes(self) -> ShowtimeRepository: ...
    @property
    def bookings(self) -> BookingRepository: ...
    @property
    def clock(self) -> "Clock": ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Roll back anything not committed."""

    def commit(self) -> None: ...


UnitOfWorkFactory = Callable[[], UnitOfWork]


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...
    def verify(self, password: str, password_hash: str) -> bool: ...


class TokenService(Protocol):
    def issue(self, user_id: UUID, role: Role) -> IssuedToken: ...

    def decode(self, token: str) -> Actor:
        """Raise InvalidTokenError when the token is malformed, forged or expired."""


class Clock(Protocol):
    def now(self) -> datetime: ...
