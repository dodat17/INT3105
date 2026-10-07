from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.domain.booking.model import Booking, BookingStatus


def test_held_booking_expires_at_the_boundary() -> None:
    expires_at = datetime(2026, 10, 15, 12, 5, tzinfo=UTC)
    booking = Booking(
        id=uuid4(),
        user_id=uuid4(),
        showtime_id=uuid4(),
        status=BookingStatus.HELD,
        tickets=(),
        total_amount=0,
        created_at=expires_at - timedelta(minutes=5),
        expires_at=expires_at,
    )

    assert booking.effective_status(expires_at - timedelta(microseconds=1)) is BookingStatus.HELD
    assert booking.effective_status(expires_at) is BookingStatus.EXPIRED
    assert booking.effective_status(expires_at + timedelta(seconds=1)) is BookingStatus.EXPIRED
    assert replace(booking, status=BookingStatus.CONFIRMED).effective_status(expires_at) is (
        BookingStatus.CONFIRMED
    )
