from collections.abc import Callable
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.auth.model import User
from app.domain.booking.model import Booking, BookingStatus, InventorySeat
from app.domain.catalog.model import Movie
from app.domain.cinema.model import Room, Seat
from app.domain.ports import Page, UnitOfWork
from app.domain.scheduling.model import Showtime


class BookingRepository(Protocol):
    def get(self, booking_id: UUID, *, lock: bool = False) -> Booking | None: ...
    def list_for_user(
        self, user_id: UUID, status: BookingStatus | None, now: datetime, page: int, page_size: int
    ) -> Page[Booking]: ...
    def count_effective_holds(
        self, user_id: UUID, now: datetime, showtime_id: UUID | None = None
    ) -> int: ...
    def add(self, booking: Booking) -> None: ...
    def update(self, booking: Booking) -> None: ...


class SeatInventoryRepository(Protocol):
    def lock(self, showtime_id: UUID, seat_ids: list[UUID]) -> list[InventorySeat]: ...
    def acquire(
        self,
        showtime_id: UUID,
        seat_ids: list[UUID],
        booking_id: UUID,
        expires_at: datetime,
        now: datetime,
    ) -> bool: ...
    def mark_booked(self, booking_id: UUID, now: datetime) -> int: ...
    def release(self, booking_id: UUID) -> int: ...
    def statuses(self, showtime_id: UUID, now: datetime) -> dict[UUID, str]: ...


class ShowtimeReader(Protocol):
    def get(self, showtime_id: UUID) -> Showtime | None: ...


class MovieReader(Protocol):
    def get(self, movie_id: UUID) -> Movie | None: ...


class RoomReader(Protocol):
    def get(self, room_id: UUID) -> Room | None: ...
    def seats(self, room_id: UUID) -> list[Seat]: ...


class AccountLock(Protocol):
    """Row lock on the customer, so concurrent holds count against BR-18 one at a time."""

    def lock(self, user_id: UUID) -> User | None: ...


class BookingUnitOfWork(UnitOfWork, Protocol):
    @property
    def bookings(self) -> BookingRepository: ...
    @property
    def inventory(self) -> SeatInventoryRepository: ...
    @property
    def showtimes(self) -> ShowtimeReader: ...
    @property
    def movies(self) -> MovieReader: ...
    @property
    def rooms(self) -> RoomReader: ...
    @property
    def users(self) -> AccountLock: ...


BookingUnitOfWorkFactory = Callable[[], BookingUnitOfWork]
