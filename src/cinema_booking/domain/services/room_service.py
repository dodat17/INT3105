from __future__ import annotations

from string import ascii_uppercase
from uuid import uuid4

from cinema_booking.domain.entities import Room, Seat, User
from cinema_booking.domain.enums import SeatType
from cinema_booking.domain.errors import BusinessRuleViolation
from cinema_booking.domain.ports import UnitOfWork
from cinema_booking.domain.services.common import require_admin


class RoomService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def list(self, actor: User) -> list[Room]:
        require_admin(actor)
        with self._uow as uow:
            return uow.rooms.list()

    def create(
        self, actor: User, name: str, rows: int, cols: int, vip_rows: list[int]
    ) -> tuple[Room, list[Seat]]:
        require_admin(actor)
        if rows < 1 or rows > len(ascii_uppercase) or cols < 1:
            raise BusinessRuleViolation("Room dimensions are invalid")
        if any(row < 1 or row > rows for row in vip_rows):
            raise BusinessRuleViolation("VIP row is outside room dimensions")
        room = Room(id=str(uuid4()), name=name.strip(), rows=rows, cols=cols)
        seats = [
            Seat(
                id=str(uuid4()),
                room_id=room.id,
                row_label=ascii_uppercase[row - 1],
                number=number,
                seat_type=SeatType.VIP if row in vip_rows else SeatType.STANDARD,
            )
            for row in range(1, rows + 1)
            for number in range(1, cols + 1)
        ]
        with self._uow as uow:
            uow.rooms.add(room, seats)
            uow.commit()
        return room, seats
