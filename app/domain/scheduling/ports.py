from collections.abc import Callable
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.catalog.model import Movie
from app.domain.cinema.model import Room, Seat
from app.domain.ports import Page, UnitOfWork
from app.domain.scheduling.model import Showtime


class ShowtimeRepository(Protocol):
    def get(self, showtime_id: UUID) -> Showtime | None: ...
    def search(
        self,
        movie_id: UUID | None,
        starts_from: datetime | None,
        starts_before: datetime | None,
        page: int,
        page_size: int,
    ) -> Page[Showtime]: ...
    def find_overlapping(
        self, room_id: UUID, starts_at: datetime, ends_at: datetime
    ) -> list[Showtime]: ...
    def add(self, showtime: Showtime) -> None: ...
    def update(self, showtime: Showtime) -> None: ...
    def delete(self, showtime_id: UUID) -> None: ...


class MovieReader(Protocol):
    def get(self, movie_id: UUID) -> Movie | None: ...


class RoomReader(Protocol):
    def get(self, room_id: UUID) -> Room | None: ...
    def lock(self, room_id: UUID) -> Room | None: ...
    def seats(self, room_id: UUID) -> list[Seat]: ...


class ShowtimeBookings(Protocol):
    """Answered by booking, which owns bookings; scheduling never imports it (BR-29)."""

    def exists_for_showtime(self, showtime_id: UUID) -> bool: ...


class ShowtimeSeats(Protocol):
    """Seat inventory is owned by booking; scheduling only creates or resets it with a showtime."""

    def initialize(self, showtime_id: UUID, seats: list[Seat]) -> None: ...
    def reset(self, showtime_id: UUID, seats: list[Seat]) -> None: ...


class SchedulingUnitOfWork(UnitOfWork, Protocol):
    @property
    def showtimes(self) -> ShowtimeRepository: ...
    @property
    def movies(self) -> MovieReader: ...
    @property
    def rooms(self) -> RoomReader: ...
    @property
    def bookings(self) -> ShowtimeBookings: ...
    @property
    def inventory(self) -> ShowtimeSeats: ...


SchedulingUnitOfWorkFactory = Callable[[], SchedulingUnitOfWork]
