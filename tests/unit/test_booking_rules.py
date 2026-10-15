from datetime import timedelta
from uuid import uuid4

import pytest

from app.domain.booking.model import BookingStatus, effective_status, validate_seat_ids
from app.domain.errors import BusinessRuleViolation
from tests.unit.fakes import NOW


def test_booking_requires_one_to_eight_distinct_seats() -> None:
    seats = [uuid4() for _ in range(8)]

    assert validate_seat_ids(seats) == seats
    with pytest.raises(BusinessRuleViolation):
        validate_seat_ids([])
    with pytest.raises(BusinessRuleViolation):
        validate_seat_ids(seats + [uuid4()])
    with pytest.raises(BusinessRuleViolation):
        validate_seat_ids([seats[0], seats[0]])


def test_held_booking_expires_at_the_boundary() -> None:
    expires_at = NOW + timedelta(minutes=5)

    assert effective_status(BookingStatus.HELD, expires_at, expires_at) is BookingStatus.EXPIRED
    assert (
        effective_status(BookingStatus.HELD, expires_at, expires_at - timedelta(microseconds=1))
        is BookingStatus.HELD
    )


def test_terminal_booking_status_is_not_changed_by_time() -> None:
    expired_long_ago = NOW - timedelta(days=1)

    assert (
        effective_status(BookingStatus.CONFIRMED, expired_long_ago, NOW)
        is BookingStatus.CONFIRMED
    )
    assert (
        effective_status(BookingStatus.CANCELLED, expired_long_ago, NOW)
        is BookingStatus.CANCELLED
    )
