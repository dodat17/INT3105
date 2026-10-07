from datetime import UTC, datetime

from app.domain.booking.model import Booking, BookingStatus, Ticket
from app.infrastructure.persistence.models import BookingModel


def as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def to_db(value: datetime) -> datetime:
    return value.astimezone(UTC)


def to_booking(
    row: BookingModel, tickets: tuple[Ticket, ...], now: datetime | None = None
) -> Booking:
    status = BookingStatus(row.status)
    expires_at = as_utc(row.expires_at)
    if now is not None and status is BookingStatus.HELD and now >= expires_at:
        status = BookingStatus.EXPIRED
    return Booking(
        id=row.id,
        user_id=row.user_id,
        showtime_id=row.showtime_id,
        status=status,
        tickets=tickets,
        total_amount=row.total_amount,
        created_at=as_utc(row.created_at),
        expires_at=expires_at,
        confirmed_at=as_utc(row.confirmed_at) if row.confirmed_at else None,
        cancelled_at=as_utc(row.cancelled_at) if row.cancelled_at else None,
        booking_code=row.booking_code,
    )
