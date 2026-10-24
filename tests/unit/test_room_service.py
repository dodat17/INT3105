from datetime import timedelta
from uuid import uuid4

import pytest

from app.domain.auth.model import Actor, Role
from app.domain.cinema.model import SeatType, generate_seats
from app.domain.cinema.service import RoomService
from app.domain.errors import (
    BusinessRuleViolation,
    ForbiddenError,
    NotFoundError,
    RoomNameAlreadyUsedError,
)
from app.domain.scheduling.model import Showtime
from tests.unit.fakes import NOW, FakeUnitOfWork

ADMIN = Actor(uuid4(), Role.ADMIN)
CUSTOMER = Actor(uuid4(), Role.CUSTOMER)


def test_generate_seats_labels_rows_and_numbers_in_order() -> None:
    seats = generate_seats(uuid4(), rows=3, cols=4, vip_rows=set())

    assert len(seats) == 12
    assert [f"{s.row_label}{s.number}" for s in seats[:5]] == ["A1", "A2", "A3", "A4", "B1"]
    assert f"{seats[-1].row_label}{seats[-1].number}" == "C4"
    assert len({s.id for s in seats}) == 12


def test_generate_seats_marks_only_vip_rows() -> None:
    seats = generate_seats(uuid4(), rows=4, cols=2, vip_rows={3, 4})

    vip = {s.row_label for s in seats if s.seat_type is SeatType.VIP}
    standard = {s.row_label for s in seats if s.seat_type is SeatType.STANDARD}
    assert vip == {"C", "D"}
    assert standard == {"A", "B"}


def test_generate_seats_supports_26_rows_up_to_z() -> None:
    seats = generate_seats(uuid4(), rows=26, cols=1, vip_rows={26})

    assert seats[-1].row_label == "Z"
    assert seats[-1].seat_type is SeatType.VIP


@pytest.mark.parametrize(
    ("rows", "cols", "vip_rows"),
    [(0, 5, set()), (27, 5, set()), (5, 0, set()), (5, 31, set()), (5, 5, {6}), (5, 5, {0})],
)
def test_generate_seats_rejects_invalid_layout(rows: int, cols: int, vip_rows: set[int]) -> None:
    with pytest.raises(BusinessRuleViolation):
        generate_seats(uuid4(), rows, cols, vip_rows)


def test_admin_creates_room_with_seats_in_one_commit() -> None:
    uow = FakeUnitOfWork()

    room = RoomService(uow).create_room(ADMIN, name=" Phòng 1 ", rows=2, cols=3, vip_rows={2})

    assert room.name == "Phòng 1"
    assert len(uow.rooms.seats(room.id)) == 6
    assert uow.commits == 1


def test_room_name_must_be_unique() -> None:
    service = RoomService(FakeUnitOfWork())
    service.create_room(ADMIN, name="Phòng 1", rows=2, cols=2, vip_rows=set())

    with pytest.raises(RoomNameAlreadyUsedError):
        service.create_room(ADMIN, name="Phòng 1", rows=3, cols=3, vip_rows=set())


def test_customer_cannot_create_or_list_rooms() -> None:
    service = RoomService(FakeUnitOfWork())

    with pytest.raises(ForbiddenError):
        service.create_room(CUSTOMER, name="Phòng 1", rows=2, cols=2, vip_rows=set())
    with pytest.raises(ForbiddenError):
        service.list_rooms(CUSTOMER)


def test_admin_updates_room_layout() -> None:
    service = RoomService(FakeUnitOfWork())
    room = service.create_room(ADMIN, name="Phòng 1", rows=2, cols=2, vip_rows=set())
    service.create_room(ADMIN, name="Phòng 2", rows=1, cols=1, vip_rows=set())

    service.update_room(ADMIN, room.id, name="Phòng 1A", rows=3, cols=2, vip_rows={3})

    updated, seats = service.get_room(ADMIN, room.id)
    assert (updated.name, updated.rows, updated.cols) == ("Phòng 1A", 3, 2)
    assert {s.row_label for s in seats if s.seat_type is SeatType.VIP} == {"C"}
    with pytest.raises(RoomNameAlreadyUsedError):
        service.update_room(ADMIN, room.id, name="Phòng 2", rows=1, cols=1, vip_rows=set())
    with pytest.raises(NotFoundError):
        service.update_room(ADMIN, uuid4(), name="X", rows=1, cols=1, vip_rows=set())
    with pytest.raises(ForbiddenError):
        service.get_room(CUSTOMER, room.id)


def test_room_with_showtimes_cannot_be_updated() -> None:
    uow = FakeUnitOfWork()
    service = RoomService(uow)
    room = service.create_room(ADMIN, name="Phòng 1", rows=2, cols=2, vip_rows=set())
    uow.showtimes.add(Showtime(uuid4(), uuid4(), room.id, NOW, NOW + timedelta(hours=2), 90_000))

    with pytest.raises(BusinessRuleViolation):
        service.update_room(ADMIN, room.id, name="Phòng 1", rows=3, cols=3, vip_rows=set())
    assert len(uow.rooms.seats(room.id)) == 4
