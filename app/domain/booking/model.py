from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from app.domain.catalog.model import Movie
from app.domain.cinema.model import Room, Seat, SeatType
from app.domain.errors import BusinessRuleViolation
from app.domain.scheduling.model import Showtime

MIN_SEATS = 1
MAX_SEATS = 8


class InventoryState(StrEnum):
    AVAILABLE = "AVAILABLE"
    HELD = "HELD"
    BOOKED = "BOOKED"


@dataclass(frozen=True)
class InventorySeat:
    seat: "Seat"
    state: InventoryState
    booking_id: UUID | None
    hold_expires_at: datetime | None


class BookingStatus(StrEnum):
    HELD = "HELD"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class BookingItem:
    seat_id: UUID
    row_label: str
    number: int
    seat_type: SeatType
    unit_price: int


@dataclass(frozen=True)
class Booking:
    id: UUID
    user_id: UUID
    showtime_id: UUID
    status: BookingStatus
    created_at: datetime
    expires_at: datetime
    total_amount: int
    items: list[BookingItem]
    confirmed_at: datetime | None = None
    cancelled_at: datetime | None = None
    booking_code: str | None = None

    def with_status(self, status: BookingStatus) -> "Booking":
        return replace(self, status=status)

    def confirm(self, at: datetime, code: str) -> "Booking":
        return replace(self, status=BookingStatus.CONFIRMED, confirmed_at=at, booking_code=code)

    def cancel(self, at: datetime) -> "Booking":
        return replace(self, status=BookingStatus.CANCELLED, cancelled_at=at)


def validate_seat_ids(seat_ids: list[UUID]) -> list[UUID]:
    if not MIN_SEATS <= len(seat_ids) <= MAX_SEATS:
        raise BusinessRuleViolation("Mỗi booking phải có từ 1 đến 8 ghế.")
    if len(set(seat_ids)) != len(seat_ids):
        raise BusinessRuleViolation("Danh sách ghế không được trùng lặp.")
    return seat_ids


def effective_status(status: BookingStatus, expires_at: datetime, now: datetime) -> BookingStatus:
    if status is BookingStatus.HELD and now >= expires_at:
        return BookingStatus.EXPIRED
    return status


@dataclass(frozen=True)
class BookingDetails:
    booking: Booking
    movie: Movie
    room: Room
    showtime: Showtime
