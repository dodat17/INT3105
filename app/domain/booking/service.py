from dataclasses import replace
from datetime import timedelta
from secrets import token_hex
from uuid import UUID, uuid4

from app.domain.auth.model import Actor, Role
from app.domain.booking.model import Booking, BookingDetail, BookingStatus, Ticket
from app.domain.errors import (
    BookingExpiredError,
    DomainValidationError,
    HoldLimitExceededError,
    InvalidBookingStateError,
    NotFoundError,
    SeatUnavailableError,
    ShowtimeNotBookableError,
)
from app.domain.ports import Page, UnitOfWorkFactory
from app.domain.scheduling.model import seat_price

MIN_SEATS = 1
MAX_SEATS = 8


class BookingService:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        hold_ttl_seconds: int,
        max_active_per_showtime: int,
        max_active_total: int,
    ) -> None:
        self._uow_factory = uow_factory
        self._hold_ttl = timedelta(seconds=hold_ttl_seconds)
        self._max_active_per_showtime = max_active_per_showtime
        self._max_active_total = max_active_total

    def create_booking(self, actor: Actor, showtime_id: UUID, seat_ids: list[UUID]) -> Booking:
        self._validate_seat_ids(seat_ids)
        sorted_seat_ids = sorted(seat_ids, key=str)
        with self._uow_factory() as uow:
            if uow.users.lock(actor.user_id) is None:
                raise NotFoundError
            showtime = uow.showtimes.get(showtime_id)
            if showtime is None:
                raise NotFoundError
            seats = {seat.id: seat for seat in uow.rooms.seats(showtime.room_id)}
            if any(seat_id not in seats for seat_id in sorted_seat_ids):
                raise DomainValidationError("Ghế không tồn tại hoặc không thuộc phòng chiếu.")
            if uow.bookings.lock_inventory(showtime_id, sorted_seat_ids) != len(sorted_seat_ids):
                raise DomainValidationError("Ghế không tồn tại hoặc không thuộc suất chiếu.")
            now = uow.clock.now()
            if now >= showtime.starts_at:
                raise ShowtimeNotBookableError
            per_showtime, total = uow.bookings.count_active_holds(actor.user_id, showtime_id, now)
            if per_showtime >= self._max_active_per_showtime or total >= self._max_active_total:
                raise HoldLimitExceededError

            booking_id = uuid4()
            tickets = tuple(
                Ticket(
                    id=uuid4(),
                    booking_id=booking_id,
                    seat_id=seat_id,
                    unit_price=seat_price(showtime.base_price, seats[seat_id].seat_type),
                )
                for seat_id in sorted_seat_ids
            )
            expires_at = min(now + self._hold_ttl, showtime.starts_at)
            booking = Booking(
                id=booking_id,
                user_id=actor.user_id,
                showtime_id=showtime_id,
                status=BookingStatus.HELD,
                tickets=tickets,
                total_amount=sum(ticket.unit_price for ticket in tickets),
                created_at=now,
                expires_at=expires_at,
            )
            uow.bookings.add(booking)
            uow.bookings.flush()
            unavailable = uow.bookings.acquire_holds(
                showtime_id,
                sorted_seat_ids,
                booking_id,
                expires_at,
                now,
            )
            if unavailable:
                raise SeatUnavailableError([str(seat_id) for seat_id in unavailable])
            uow.commit()
            return booking

    def list_my_bookings(
        self,
        actor: Actor,
        status: BookingStatus | None,
        page: int,
        page_size: int,
    ) -> Page[Booking]:
        with self._uow_factory() as uow:
            now = uow.clock.now()
            return uow.bookings.search(
                actor.user_id,
                status.value if status is not None else None,
                now,
                page,
                page_size,
            )

    def get_booking(self, actor: Actor, booking_id: UUID) -> Booking:
        with self._uow_factory() as uow:
            booking = self._require_access(uow.bookings.get(booking_id), actor, allow_admin=True)
            now = uow.clock.now()
            return replace(booking, status=booking.effective_status(now))

    def get_booking_detail(self, actor: Actor, booking_id: UUID) -> BookingDetail:
        with self._uow_factory() as uow:
            booking = self._require_access(uow.bookings.get(booking_id), actor, allow_admin=True)
            booking = replace(booking, status=booking.effective_status(uow.clock.now()))
            showtime = uow.showtimes.get(booking.showtime_id)
            if showtime is None:
                raise NotFoundError
            movie = uow.movies.get(showtime.movie_id)
            room = uow.rooms.get(showtime.room_id)
            if movie is None or room is None:
                raise NotFoundError
            seats_by_id = {seat.id: seat for seat in uow.rooms.seats(room.id)}
            try:
                seats = tuple(seats_by_id[ticket.seat_id] for ticket in booking.tickets)
            except KeyError as exc:
                raise NotFoundError from exc
            return BookingDetail(booking, movie, showtime, room, seats)

    def confirm_booking(self, actor: Actor, booking_id: UUID) -> Booking:
        with self._uow_factory() as uow:
            booking = self._require_access(
                uow.bookings.get_for_update(booking_id), actor, allow_admin=False
            )
            now = uow.clock.now()
            if booking.status is BookingStatus.CONFIRMED:
                return booking
            if booking.status is BookingStatus.CANCELLED:
                raise InvalidBookingStateError
            if booking.status is BookingStatus.EXPIRED or now >= booking.expires_at:
                raise BookingExpiredError
            showtime = uow.showtimes.get(booking.showtime_id)
            if showtime is None:
                raise NotFoundError
            if now >= showtime.starts_at:
                raise ShowtimeNotBookableError
            if uow.bookings.mark_booked(booking.id, now) != len(booking.tickets):
                raise SeatUnavailableError([str(ticket.seat_id) for ticket in booking.tickets])
            booking_code = token_hex(6).upper()
            uow.bookings.confirm(booking.id, now, booking_code)
            uow.commit()
            return replace(
                booking,
                status=BookingStatus.CONFIRMED,
                confirmed_at=now,
                booking_code=booking_code,
            )

    def cancel_booking(self, actor: Actor, booking_id: UUID) -> None:
        with self._uow_factory() as uow:
            booking = self._require_access(
                uow.bookings.get_for_update(booking_id), actor, allow_admin=True
            )
            now = uow.clock.now()
            if booking.status is BookingStatus.CONFIRMED:
                raise InvalidBookingStateError
            if booking.status in {BookingStatus.CANCELLED, BookingStatus.EXPIRED}:
                return
            if now >= booking.expires_at:
                return
            uow.bookings.release_holds(booking.id)
            uow.bookings.cancel(booking.id, now)
            uow.commit()

    @staticmethod
    def _validate_seat_ids(seat_ids: list[UUID]) -> None:
        if not MIN_SEATS <= len(seat_ids) <= MAX_SEATS:
            raise DomainValidationError("Mỗi booking phải có từ 1 đến 8 ghế.")
        if len(set(seat_ids)) != len(seat_ids):
            raise DomainValidationError("Danh sách ghế không được trùng lặp.")

    @staticmethod
    def _require_access(booking: Booking | None, actor: Actor, *, allow_admin: bool) -> Booking:
        if booking is None or (
            booking.user_id != actor.user_id and not (allow_admin and actor.role is Role.ADMIN)
        ):
            raise NotFoundError
        return booking
