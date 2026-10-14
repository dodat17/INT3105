from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

from cinema_booking.domain.entities import Seat, Showtime, User
from cinema_booking.domain.errors import BusinessRuleViolation, NotFound, ShowtimeOverlap
from cinema_booking.domain.ports import UnitOfWork
from cinema_booking.domain.services.common import require_admin


class ShowtimeService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def list(self, movie_id: str | None = None, on_date: date | None = None) -> list[Showtime]:
        with self._uow as uow:
            return uow.showtimes.list(movie_id, on_date)

    def seat_map(self, showtime_id: str) -> tuple[Showtime, list[Seat], set[str]]:
        with self._uow as uow:
            showtime = uow.showtimes.get(showtime_id)
            if showtime is None:
                raise NotFound("Showtime not found", {"showtime_id": showtime_id})
            seats = uow.rooms.get_seats(showtime.room_id)
            booked = uow.bookings.booked_seat_ids(showtime_id)
            return showtime, seats, booked

    def create(
        self,
        actor: User,
        movie_id: str,
        room_id: str,
        starts_at,
        base_price: int,
    ) -> Showtime:
        require_admin(actor)
        if starts_at.tzinfo is None or starts_at.utcoffset() is None:
            raise BusinessRuleViolation("Showtime start must include a timezone")
        if base_price <= 0:
            raise BusinessRuleViolation("Base price must be positive")
        with self._uow as uow:
            movie = uow.movies.get(movie_id)
            if movie is None:
                raise NotFound("Movie not found", {"movie_id": movie_id})
            if uow.rooms.get(room_id) is None:
                raise NotFound("Room not found", {"room_id": room_id})
            ends_at = starts_at + timedelta(minutes=movie.duration_minutes)
            if uow.showtimes.find_overlaps(room_id, starts_at, ends_at):
                raise ShowtimeOverlap("Showtime overlaps another showtime in this room")
            showtime = Showtime(
                id=str(uuid4()),
                movie_id=movie_id,
                room_id=room_id,
                starts_at=starts_at,
                ends_at=ends_at,
                base_price=base_price,
            )
            uow.showtimes.add(showtime)
            uow.commit()
            return showtime

    def delete(self, actor: User, showtime_id: str) -> None:
        require_admin(actor)
        with self._uow as uow:
            if uow.showtimes.get(showtime_id) is None:
                raise NotFound("Showtime not found", {"showtime_id": showtime_id})
            if uow.showtimes.has_confirmed_bookings(showtime_id):
                raise BusinessRuleViolation("Showtime has confirmed bookings")
            uow.showtimes.delete(showtime_id)
            uow.commit()
