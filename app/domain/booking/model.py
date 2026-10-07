from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class BookingStatus(StrEnum):
    HELD = "HELD"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class Ticket:
    id: UUID
    booking_id: UUID
    seat_id: UUID
    unit_price: int


@dataclass(frozen=True)
class Booking:
    id: UUID
    user_id: UUID
    showtime_id: UUID
    status: BookingStatus
    tickets: tuple[Ticket, ...]
    total_amount: int
    created_at: datetime
    expires_at: datetime
    confirmed_at: datetime | None = None
    cancelled_at: datetime | None = None
    booking_code: str | None = None

    def effective_status(self, now: datetime) -> BookingStatus:
        """Return EXPIRED for a HELD booking whose hold is no longer effective."""
        if self.status is BookingStatus.HELD and now >= self.expires_at:
            return BookingStatus.EXPIRED
        return self.status
