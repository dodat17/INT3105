from uuid import uuid4

from cinema_booking.domain.entities import Booking, Ticket, User
from cinema_booking.domain.enums import BookingStatus, SeatType, UserRole
from cinema_booking.domain.errors import (
    BusinessRuleViolation,
    Forbidden,
    NotFound,
    SeatUnavailable,
    ShowtimeAlreadyStarted,
)
from cinema_booking.domain.ports import Clock, UnitOfWork


class BookingService:
    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    def create(self, actor: User, showtime_id: str, seat_ids: list[str]) -> Booking:
        if not 1 <= len(seat_ids) <= 8 or len(set(seat_ids)) != len(seat_ids):
            raise BusinessRuleViolation("A booking must contain 1-8 distinct seats")
        with self._uow as uow:
            showtime = uow.showtimes.get(showtime_id)
            if showtime is None:
                raise NotFound("Showtime not found", {"showtime_id": showtime_id})
            if self._clock.now() >= showtime.starts_at:
                raise ShowtimeAlreadyStarted("Showtime has already started")
            seats = uow.rooms.get_seats_by_ids(seat_ids)
            if len(seats) != len(seat_ids) or any(
                seat.room_id != showtime.room_id for seat in seats
            ):
                raise BusinessRuleViolation("All seats must exist in the showtime room")
            unavailable = sorted(uow.bookings.booked_seat_ids(showtime_id).intersection(seat_ids))
            if unavailable:
                raise SeatUnavailable(
                    "One or more seats are unavailable", {"seat_ids": unavailable}
                )
            booking_id = str(uuid4())
            tickets = [
                Ticket(
                    id=str(uuid4()),
                    booking_id=booking_id,
                    showtime_id=showtime_id,
                    seat_id=seat.id,
                    price=(
                        showtime.base_price
                        if seat.seat_type is SeatType.STANDARD
                        else showtime.base_price * 13 // 10
                    ),
                )
                for seat in seats
            ]
            booking = Booking(
                id=booking_id,
                user_id=actor.id,
                showtime_id=showtime_id,
                status=BookingStatus.CONFIRMED,
                total_price=sum(ticket.price for ticket in tickets),
                created_at=self._clock.now(),
                tickets=tickets,
            )
            uow.bookings.add(booking)
            uow.commit()
            return booking

    def list(self, actor: User) -> list[Booking]:
        with self._uow as uow:
            return uow.bookings.list_for_user(actor.id)

    def get(self, actor: User, booking_id: str) -> Booking:
        with self._uow as uow:
            booking = uow.bookings.get(booking_id)
            if booking is None:
                raise NotFound("Booking not found", {"booking_id": booking_id})
            self._require_owner_or_admin(actor, booking)
            return booking

    def cancel(self, actor: User, booking_id: str) -> None:
        with self._uow as uow:
            booking = uow.bookings.get(booking_id)
            if booking is None:
                raise NotFound("Booking not found", {"booking_id": booking_id})
            self._require_owner_or_admin(actor, booking)
            showtime = uow.showtimes.get(booking.showtime_id)
            if showtime is None:
                raise NotFound("Showtime not found", {"showtime_id": booking.showtime_id})
            if self._clock.now() >= showtime.starts_at:
                raise ShowtimeAlreadyStarted("A booking cannot be cancelled after showtime starts")
            if booking.status is BookingStatus.CANCELLED:
                return
            booking.status = BookingStatus.CANCELLED
            uow.bookings.cancel(booking)
            uow.commit()

    @staticmethod
    def _require_owner_or_admin(actor: User, booking: Booking) -> None:
        if actor.id != booking.user_id and actor.role is not UserRole.ADMIN:
            raise Forbidden("You cannot access this booking")
