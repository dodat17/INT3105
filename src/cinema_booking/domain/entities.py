from dataclasses import dataclass, field
from datetime import datetime

from cinema_booking.domain.enums import BookingStatus, SeatType, UserRole


@dataclass(slots=True)
class User:
    id: str
    email: str
    password_hash: str
    full_name: str
    role: UserRole
    created_at: datetime


@dataclass(slots=True)
class Movie:
    id: str
    title: str
    duration_minutes: int
    genre: str
    age_rating: str
    description: str | None = None


@dataclass(slots=True)
class Room:
    id: str
    name: str
    rows: int
    cols: int


@dataclass(slots=True)
class Seat:
    id: str
    room_id: str
    row_label: str
    number: int
    seat_type: SeatType


@dataclass(slots=True)
class Showtime:
    id: str
    movie_id: str
    room_id: str
    starts_at: datetime
    ends_at: datetime
    base_price: int


@dataclass(slots=True)
class Ticket:
    id: str
    booking_id: str
    showtime_id: str
    seat_id: str
    price: int


@dataclass(slots=True)
class Booking:
    id: str
    user_id: str
    showtime_id: str
    status: BookingStatus
    total_price: int
    created_at: datetime
    tickets: list[Ticket] = field(default_factory=list)
