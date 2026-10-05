from dataclasses import dataclass
from enum import StrEnum
from string import ascii_uppercase
from uuid import UUID, uuid4

from app.domain.errors import BusinessRuleViolation

MAX_ROWS = len(ascii_uppercase)  # one letter per row: A..Z
MAX_COLS = 30


class SeatType(StrEnum):
    STANDARD = "STANDARD"
    VIP = "VIP"


@dataclass(frozen=True)
class Room:
    id: UUID
    name: str
    rows: int
    cols: int


@dataclass(frozen=True)
class Seat:
    id: UUID
    room_id: UUID
    row_label: str
    number: int
    seat_type: SeatType


def generate_seats(room_id: UUID, rows: int, cols: int, vip_rows: set[int]) -> list[Seat]:
    """Seats A1..{row}{cols}; vip_rows are 1-based row numbers (1 = A)."""
    if not 1 <= rows <= MAX_ROWS or not 1 <= cols <= MAX_COLS:
        raise BusinessRuleViolation(f"Phòng phải có 1–{MAX_ROWS} hàng và 1–{MAX_COLS} cột.")
    if any(not 1 <= row <= rows for row in vip_rows):
        raise BusinessRuleViolation("Hàng VIP nằm ngoài số hàng của phòng.")
    return [
        Seat(
            id=uuid4(),
            room_id=room_id,
            row_label=ascii_uppercase[row - 1],
            number=number,
            seat_type=SeatType.VIP if row in vip_rows else SeatType.STANDARD,
        )
        for row in range(1, rows + 1)
        for number in range(1, cols + 1)
    ]
