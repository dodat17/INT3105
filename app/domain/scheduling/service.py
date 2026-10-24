from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from app.domain.auth.model import Actor, require_admin
from app.domain.catalog.model import Movie
from app.domain.cinema.model import Room
from app.domain.errors import BusinessRuleViolation, NotFoundError, ShowtimeOverlapError
from app.domain.ports import Page, UnitOfWorkFactory
from app.domain.scheduling.model import (
    SeatMapEntry,
    SeatStatus,
    Showtime,
    local_day_bounds,
    seat_price,
)


class ShowtimeService:
    def __init__(self, uow_factory: UnitOfWorkFactory, timezone: ZoneInfo) -> None:
        self._uow_factory = uow_factory
        self._timezone = timezone

    def list_showtimes(
        self, movie_id: UUID | None, on_date: date | None, page: int, page_size: int
    ) -> Page[Showtime]:
        # A showtime belongs to the cinema-local day it starts on.
        starts_from, starts_before = (
            local_day_bounds(on_date, self._timezone) if on_date else (None, None)
        )
        with self._uow_factory() as uow:
            return uow.showtimes.search(movie_id, starts_from, starts_before, page, page_size)

    def get_showtime(self, showtime_id: UUID) -> tuple[Showtime, Movie, Room]:
        with self._uow_factory() as uow:
            showtime = uow.showtimes.get(showtime_id)
            if showtime is None:
                raise NotFoundError
            movie = uow.movies.get(showtime.movie_id)
            room = uow.rooms.get(showtime.room_id)
        if movie is None or room is None:
            raise NotFoundError
        return showtime, movie, room

    def create_showtime(
        self,
        actor: Actor,
        *,
        movie_id: UUID,
        room_id: UUID,
        starts_at: datetime,
        base_price: int,
    ) -> Showtime:
        require_admin(actor)
        starts_at = self._checked_start(starts_at, base_price)
        with self._uow_factory() as uow:
            movie = uow.movies.get(movie_id)
            # BR-04 under concurrency: locking the room makes schedule changes for one room
            # run one after another, so the overlap check below always sees the latest rows.
            if movie is None or uow.rooms.lock(room_id) is None:
                raise NotFoundError
            showtime = Showtime(
                id=uuid4(),
                movie_id=movie_id,
                room_id=room_id,
                starts_at=starts_at,
                ends_at=starts_at + timedelta(minutes=movie.duration_minutes),
                base_price=base_price,
            )
            if uow.showtimes.find_overlapping(room_id, showtime.starts_at, showtime.ends_at):
                raise ShowtimeOverlapError
            uow.showtimes.add(showtime)
            uow.inventory.initialize(showtime.id, uow.rooms.seats(room_id))
            uow.commit()
        return showtime

    def update_showtime(
        self,
        actor: Actor,
        showtime_id: UUID,
        *,
        movie_id: UUID,
        room_id: UUID,
        starts_at: datetime,
        base_price: int,
        is_open_for_booking: bool,
    ) -> Showtime:
        require_admin(actor)
        starts_at = self._checked_start(starts_at, base_price)
        with self._uow_factory() as uow:
            current = uow.showtimes.get(showtime_id)
            movie = uow.movies.get(movie_id)
            # Same room lock as create, so the overlap check sees the latest schedule.
            if current is None or movie is None or uow.rooms.lock(room_id) is None:
                raise NotFoundError
            showtime = Showtime(
                id=showtime_id,
                movie_id=movie_id,
                room_id=room_id,
                starts_at=starts_at,
                ends_at=starts_at + timedelta(minutes=movie.duration_minutes),
                base_price=base_price,
                is_open_for_booking=is_open_for_booking,
            )
            rescheduled = (current.movie_id, current.room_id, current.starts_at) != (
                movie_id,
                room_id,
                starts_at,
            )
            # Bookings already name this movie, room and time; price and sale flag may change.
            if rescheduled and uow.bookings.exists_for_showtime(showtime_id):
                raise BusinessRuleViolation(
                    "Không thể đổi phim, phòng hoặc giờ chiếu của suất đã có booking."
                )
            overlapping = uow.showtimes.find_overlapping(
                room_id, showtime.starts_at, showtime.ends_at
            )
            if any(other.id != showtime_id for other in overlapping):
                raise ShowtimeOverlapError
            uow.showtimes.update(showtime)
            if room_id != current.room_id:
                uow.inventory.reset(showtime_id, uow.rooms.seats(room_id))
            uow.commit()
        return showtime

    def delete_showtime(self, actor: Actor, showtime_id: UUID) -> None:
        require_admin(actor)
        # BR-12 (no delete once CONFIRMED tickets exist) needs bookings (milestone D).
        with self._uow_factory() as uow:
            if uow.showtimes.get(showtime_id) is None:
                raise NotFoundError
            uow.showtimes.delete(showtime_id)
            uow.commit()

    @staticmethod
    def _checked_start(starts_at: datetime, base_price: int) -> datetime:
        if starts_at.tzinfo is None:
            raise BusinessRuleViolation("Giờ bắt đầu phải kèm múi giờ.")
        if base_price <= 0:
            raise BusinessRuleViolation("Giá vé phải lớn hơn 0.")
        return starts_at.astimezone(UTC)  # times are kept in UTC

    def seat_map(self, showtime_id: UUID) -> tuple[Showtime, Room, list[SeatMapEntry]]:
        with self._uow_factory() as uow:
            showtime = uow.showtimes.get(showtime_id)
            if showtime is None:
                raise NotFoundError
            room = uow.rooms.get(showtime.room_id)
            if room is None:
                raise NotFoundError
            seats = uow.rooms.seats(room.id)
            now = uow.clock.now()
            statuses = uow.inventory.statuses(showtime.id, now)
        return (
            showtime,
            room,
            [
                SeatMapEntry(
                    seat,
                    seat_price(showtime.base_price, seat.seat_type),
                    SeatStatus(statuses.get(seat.id, "AVAILABLE")),
                )
                for seat in seats
            ],
        )
