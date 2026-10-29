from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from app.domain.cinema.model import SeatType

VIP_PRICE_PERCENT = 130  # BR-09: VIP = base x 1.3, kept in integer VND


@dataclass(frozen=True)
class Showtime:
    id: UUID
    movie_id: UUID
    room_id: UUID
    starts_at: datetime
    ends_at: datetime
    base_price: int
    is_open_for_booking: bool = True


def seat_price(base_price: int, seat_type: SeatType) -> int:
    if seat_type is SeatType.VIP:
        return base_price * VIP_PRICE_PERCENT // 100
    return base_price


def overlaps(starts_a: datetime, ends_a: datetime, starts_b: datetime, ends_b: datetime) -> bool:
    """Half-open [starts, ends): a showtime ending at 10:00 does not clash with one at 10:00."""
    return starts_a < ends_b and starts_b < ends_a


def local_day_bounds(day: date, timezone: ZoneInfo) -> tuple[datetime, datetime]:
    """[start, end) of a calendar day in the cinema's timezone."""
    start = datetime.combine(day, time.min, tzinfo=timezone)
    end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=timezone)
    return start, end
