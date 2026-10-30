from datetime import timedelta
from secrets import token_hex
from uuid import UUID, uuid4

from app.domain.auth.model import Actor, Role
from app.domain.booking.model import (
    Booking,
    BookingDetails,
    BookingItem,
    BookingStatus,
    InventoryState,
    SeatMap,
    SeatMapEntry,
    SeatStatus,
    effective_status,
    validate_seat_ids,
)
from app.domain.booking.ports import BookingUnitOfWorkFactory
from app.domain.errors import (
    BookingExpiredError,
    BookingValidationError,
    ForbiddenError,
    HoldLimitExceededError,
    InvalidBookingStateError,
    NotFoundError,
    SeatUnavailableError,
    ShowtimeNotBookableError,
)
from app.domain.ports import Page
from app.domain.scheduling.model import seat_price


class BookingService:
    def __init__(
        self,
        uow_factory: BookingUnitOfWorkFactory,
        hold_ttl_seconds: int,
        max_holds_per_showtime: int,
        max_active_holds: int,
    ) -> None:
        self._uow_factory = uow_factory
        self._hold_ttl = timedelta(seconds=hold_ttl_seconds)
        self._max_per_showtime = max_holds_per_showtime
        self._max_active = max_active_holds

    @staticmethod
    def _customer(actor: Actor) -> None:
        if actor.role is not Role.CUSTOMER:
            raise ForbiddenError

    @staticmethod
    def _owned(booking: Booking | None, actor: Actor) -> Booking:
        if booking is None or booking.user_id != actor.user_id:
            raise NotFoundError
        return booking

    def create(self, actor: Actor, showtime_id: UUID, seat_ids: list[UUID]) -> Booking:
        self._customer(actor)
        validate_seat_ids(seat_ids)
        ordered_ids = sorted(seat_ids)
        with self._uow_factory() as uow:
            showtime = uow.showtimes.get(showtime_id)
            if showtime is None:
                raise NotFoundError
            if uow.users.lock(actor.user_id) is None:
                raise NotFoundError
            inventory = uow.inventory.lock(showtime_id, ordered_ids)
            now = uow.clock.now()
            if not showtime.is_open_for_booking or now >= showtime.starts_at:
                raise ShowtimeNotBookableError
            if len(inventory) != len(ordered_ids):
                raise BookingValidationError(
                    "Ghế không tồn tại hoặc không thuộc phòng của suất chiếu.",
                    "seatIds",
                )
            if (
                uow.bookings.count_effective_holds(actor.user_id, now, showtime_id)
                >= self._max_per_showtime
            ):
                raise HoldLimitExceededError
            if uow.bookings.count_effective_holds(actor.user_id, now) >= self._max_active:
                raise HoldLimitExceededError
            unavailable = sorted(
                row.seat.id
                for row in inventory
                if row.state is InventoryState.BOOKED
                or (
                    row.state is InventoryState.HELD
                    and row.hold_expires_at is not None
                    and row.hold_expires_at > now
                )
            )
            if unavailable:
                raise SeatUnavailableError(unavailable)
            expires_at = min(now + self._hold_ttl, showtime.starts_at)
            items = [
                BookingItem(
                    row.seat.id,
                    row.seat.row_label,
                    row.seat.number,
                    row.seat.seat_type,
                    seat_price(showtime.base_price, row.seat.seat_type),
                )
                for row in inventory
            ]
            booking = Booking(
                uuid4(),
                actor.user_id,
                showtime_id,
                BookingStatus.HELD,
                now,
                expires_at,
                sum(item.unit_price for item in items),
                items,
            )
            uow.bookings.add(booking)
            if not uow.inventory.acquire(showtime_id, ordered_ids, booking.id, expires_at, now):
                conflicting = [
                    row.seat.id
                    for row in uow.inventory.lock(showtime_id, ordered_ids)
                    if row.booking_id != booking.id
                    and (
                        row.state is InventoryState.BOOKED
                        or (
                            row.state is InventoryState.HELD
                            and row.hold_expires_at is not None
                            and row.hold_expires_at > now
                        )
                    )
                ]
                raise SeatUnavailableError(conflicting)
            uow.commit()
            return booking

    def get(self, actor: Actor, booking_id: UUID) -> Booking:
        with self._uow_factory() as uow:
            booking = self._owned(uow.bookings.get(booking_id), actor)
            now = uow.clock.now()
        status = effective_status(booking.status, booking.expires_at, now)
        return booking if status is booking.status else booking.with_status(status)

    def details(self, actor: Actor, booking_id: UUID) -> BookingDetails:
        return self._details(self.get(actor, booking_id))

    def seat_map(self, showtime_id: UUID) -> SeatMap:
        with self._uow_factory() as uow:
            showtime = uow.showtimes.get(showtime_id)
            if showtime is None:
                raise NotFoundError
            movie = uow.movies.get(showtime.movie_id)
            room = uow.rooms.get(showtime.room_id)
            if movie is None or room is None:
                raise NotFoundError
            seats = uow.rooms.seats(room.id)
            statuses = uow.inventory.statuses(showtime.id, uow.clock.now())
        entries = [
            SeatMapEntry(
                seat,
                seat_price(showtime.base_price, seat.seat_type),
                SeatStatus(statuses.get(seat.id, SeatStatus.AVAILABLE)),
            )
            for seat in seats
        ]
        return SeatMap(showtime, movie, room, entries)

    def _details(self, booking: Booking) -> BookingDetails:
        with self._uow_factory() as uow:
            showtime = uow.showtimes.get(booking.showtime_id)
            if showtime is None:
                raise NotFoundError
            movie = uow.movies.get(showtime.movie_id)
            room = uow.rooms.get(showtime.room_id)
            if movie is None or room is None:
                raise NotFoundError
        return BookingDetails(booking=booking, movie=movie, room=room, showtime=showtime)

    def list(
        self, actor: Actor, status: BookingStatus | None, page: int, page_size: int
    ) -> Page[Booking]:
        self._customer(actor)
        with self._uow_factory() as uow:
            now = uow.clock.now()
            return uow.bookings.list_for_user(actor.user_id, status, now, page, page_size)

    def confirm(self, actor: Actor, booking_id: UUID) -> Booking:
        with self._uow_factory() as uow:
            booking = self._owned(uow.bookings.get(booking_id, lock=True), actor)
            now = uow.clock.now()
            if booking.status is BookingStatus.CONFIRMED:
                return booking
            if booking.status is not BookingStatus.HELD:
                raise InvalidBookingStateError
            if now >= booking.expires_at:
                raise BookingExpiredError
            showtime = uow.showtimes.get(booking.showtime_id)
            if showtime is None or not showtime.is_open_for_booking or now >= showtime.starts_at:
                raise ShowtimeNotBookableError
            if uow.inventory.mark_booked(booking.id, now) != len(booking.items):
                raise SeatUnavailableError([item.seat_id for item in booking.items])
            confirmed = booking.confirm(now, token_hex(4).upper())
            uow.bookings.update(confirmed)
            uow.commit()
            return confirmed

    def cancel(self, actor: Actor, booking_id: UUID) -> None:
        with self._uow_factory() as uow:
            booking = self._owned(uow.bookings.get(booking_id, lock=True), actor)
            now = uow.clock.now()
            if booking.status is BookingStatus.CONFIRMED:
                raise InvalidBookingStateError
            if booking.status is BookingStatus.CANCELLED:
                return
            uow.inventory.release(booking.id)
            if now < booking.expires_at:
                uow.bookings.update(booking.cancel(now))
            uow.commit()
