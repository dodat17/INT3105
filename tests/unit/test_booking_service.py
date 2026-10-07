from dataclasses import replace
from datetime import timedelta
from uuid import uuid4

import pytest

from app.domain.auth.model import Actor, Role, User
from app.domain.booking.model import BookingStatus
from app.domain.booking.service import BookingService
from app.domain.cinema.model import Room, Seat, generate_seats
from app.domain.errors import (
    BookingExpiredError,
    DomainValidationError,
    InvalidBookingStateError,
    NotFoundError,
    SeatUnavailableError,
    ShowtimeNotBookableError,
)
from app.domain.scheduling.model import Showtime
from tests.unit.fakes import NOW, FakeUnitOfWork

CUSTOMER = Actor(uuid4(), Role.CUSTOMER)
OTHER = Actor(uuid4(), Role.CUSTOMER)


@pytest.fixture
def uow() -> FakeUnitOfWork:
    uow = FakeUnitOfWork()
    uow.users.add(User(CUSTOMER.user_id, "a@test", "hash", "A", Role.CUSTOMER, NOW))
    uow.users.add(User(OTHER.user_id, "b@test", "hash", "B", Role.CUSTOMER, NOW))
    room = Room(uuid4(), "Phòng 1", 2, 5)
    seats = generate_seats(room.id, room.rows, room.cols, {2})
    uow.rooms.add(room, seats)
    showtime = Showtime(
        uuid4(), uuid4(), room.id, NOW + timedelta(hours=1), NOW + timedelta(hours=3), 90_000
    )
    uow.showtimes.add(showtime)
    for seat in seats:
        uow.bookings.inventory[(showtime.id, seat.id)] = ("AVAILABLE", None, None)
    return uow


@pytest.fixture
def service(uow: FakeUnitOfWork) -> BookingService:
    return BookingService(uow, 300, 2, 5)


def _showtime_and_seats(uow: FakeUnitOfWork) -> tuple[Showtime, list[Seat]]:
    showtime = next(iter(uow.showtimes.rows.values()))
    return showtime, list(uow.rooms.seat_rows[showtime.room_id])


def test_create_booking_calculates_prices_and_holds_all_seats(
    service: BookingService, uow: FakeUnitOfWork
) -> None:
    showtime, seats = _showtime_and_seats(uow)

    booking = service.create_booking(CUSTOMER, showtime.id, [seats[0].id, seats[5].id])

    assert booking.status is BookingStatus.HELD
    assert {ticket.unit_price for ticket in booking.tickets} == {90_000, 117_000}
    assert booking.total_amount == 207_000
    assert booking.expires_at == NOW + timedelta(minutes=5)
    assert {
        uow.bookings.inventory[(showtime.id, ticket.seat_id)][0] for ticket in booking.tickets
    } == {"HELD"}
    assert uow.commits == 1


def test_create_booking_rejects_invalid_seats_and_started_showtime(
    service: BookingService, uow: FakeUnitOfWork
) -> None:
    showtime, seats = _showtime_and_seats(uow)
    with pytest.raises(DomainValidationError):
        service.create_booking(CUSTOMER, showtime.id, [])
    with pytest.raises(DomainValidationError):
        service.create_booking(CUSTOMER, showtime.id, [seat.id for seat in seats[:9]])
    with pytest.raises(DomainValidationError):
        service.create_booking(CUSTOMER, showtime.id, [seats[0].id, seats[0].id])
    with pytest.raises(DomainValidationError):
        service.create_booking(CUSTOMER, showtime.id, [uuid4()])

    started = replace(showtime, id=uuid4(), starts_at=NOW, ends_at=NOW + timedelta(hours=2))
    uow.showtimes.add(started)
    uow.bookings.inventory[(started.id, seats[0].id)] = ("AVAILABLE", None, None)
    with pytest.raises(ShowtimeNotBookableError):
        service.create_booking(CUSTOMER, started.id, [seats[0].id])


def test_occupied_seat_rolls_back_without_holding_the_rest(
    service: BookingService, uow: FakeUnitOfWork
) -> None:
    showtime, seats = _showtime_and_seats(uow)
    service.create_booking(CUSTOMER, showtime.id, [seats[0].id])

    with pytest.raises(SeatUnavailableError):
        service.create_booking(OTHER, showtime.id, [seats[0].id, seats[1].id])

    assert uow.bookings.inventory[(showtime.id, seats[1].id)][0] == "AVAILABLE"


def test_confirm_is_idempotent_and_checks_owner(
    service: BookingService, uow: FakeUnitOfWork
) -> None:
    showtime, seats = _showtime_and_seats(uow)
    booking = service.create_booking(CUSTOMER, showtime.id, [seats[0].id])

    with pytest.raises(NotFoundError):
        service.confirm_booking(OTHER, booking.id)
    confirmed = service.confirm_booking(CUSTOMER, booking.id)
    repeated = service.confirm_booking(CUSTOMER, booking.id)

    assert confirmed.status is BookingStatus.CONFIRMED
    assert repeated.booking_code == confirmed.booking_code
    assert uow.bookings.inventory[(showtime.id, seats[0].id)][0] == "BOOKED"
    with pytest.raises(InvalidBookingStateError):
        service.cancel_booking(CUSTOMER, booking.id)


def test_cancel_releases_seat_and_keeps_ticket_history(
    service: BookingService, uow: FakeUnitOfWork
) -> None:
    showtime, seats = _showtime_and_seats(uow)
    booking = service.create_booking(CUSTOMER, showtime.id, [seats[0].id])

    service.cancel_booking(CUSTOMER, booking.id)
    service.cancel_booking(CUSTOMER, booking.id)
    cancelled = service.get_booking(CUSTOMER, booking.id)
    replacement = service.create_booking(CUSTOMER, showtime.id, [seats[0].id])

    assert cancelled.status is BookingStatus.CANCELLED
    assert cancelled.tickets == booking.tickets
    assert replacement.id != booking.id


def test_expired_hold_cannot_be_confirmed_and_reads_as_expired(
    service: BookingService, uow: FakeUnitOfWork
) -> None:
    showtime, seats = _showtime_and_seats(uow)
    booking = service.create_booking(CUSTOMER, showtime.id, [seats[0].id])
    uow.bookings.rows[booking.id] = replace(booking, expires_at=NOW)
    uow.bookings.inventory[(showtime.id, seats[0].id)] = ("HELD", booking.id, NOW)

    with pytest.raises(BookingExpiredError):
        service.confirm_booking(CUSTOMER, booking.id)
    service.cancel_booking(CUSTOMER, booking.id)

    assert service.get_booking(CUSTOMER, booking.id).status is BookingStatus.EXPIRED
    expired = service.list_my_bookings(CUSTOMER, BookingStatus.EXPIRED, 1, 20)
    assert [item.id for item in expired.items] == [booking.id]
