from datetime import timedelta

import pytest

from cinema_booking.domain.errors import (
    BusinessRuleViolation,
    Forbidden,
    SeatUnavailable,
    ShowtimeAlreadyStarted,
)
from cinema_booking.domain.services.booking_service import BookingService


def test_booking_validates_seats_and_calculates_integer_price(
    uow, clock, customer, cinema_data
) -> None:
    _movie, _room, seats, showtime = cinema_data
    service = BookingService(uow, clock)

    booking = service.create(customer, showtime.id, [seats[0].id, seats[1].id])

    assert [ticket.price for ticket in booking.tickets] == [100_000, 130_000]
    assert booking.total_price == 230_000
    with pytest.raises(BusinessRuleViolation):
        service.create(customer, showtime.id, [])
    with pytest.raises(BusinessRuleViolation):
        service.create(customer, showtime.id, [seats[2].id] * 2)
    with pytest.raises(SeatUnavailable):
        service.create(customer, showtime.id, [seats[0].id])


def test_booking_rejects_wrong_room_and_started_showtime(
    uow, clock, customer, cinema_data
) -> None:
    _movie, _room, seats, showtime = cinema_data
    service = BookingService(uow, clock)
    seats[0].room_id = "another-room"

    with pytest.raises(BusinessRuleViolation):
        service.create(customer, showtime.id, [seats[0].id])
    seats[0].room_id = showtime.room_id
    clock.value = showtime.starts_at
    with pytest.raises(ShowtimeAlreadyStarted):
        service.create(customer, showtime.id, [seats[0].id])


def test_booking_ownership_cancel_and_rebook(
    uow, clock, customer, admin, cinema_data
) -> None:
    _movie, _room, seats, showtime = cinema_data
    service = BookingService(uow, clock)
    booking = service.create(customer, showtime.id, [seats[0].id])
    stranger = type(customer)(
        "stranger",
        "stranger@example.com",
        "hash",
        "Stranger",
        customer.role,
        customer.created_at,
    )

    with pytest.raises(Forbidden):
        service.get(stranger, booking.id)
    assert service.get(admin, booking.id).id == booking.id
    service.cancel(customer, booking.id)
    assert service.create(customer, showtime.id, [seats[0].id]).total_price == 100_000


def test_booking_cannot_be_cancelled_after_start(uow, clock, customer, cinema_data) -> None:
    _movie, _room, seats, showtime = cinema_data
    service = BookingService(uow, clock)
    booking = service.create(customer, showtime.id, [seats[0].id])
    clock.value = showtime.starts_at + timedelta(seconds=1)

    with pytest.raises(ShowtimeAlreadyStarted):
        service.cancel(customer, booking.id)
