from datetime import UTC, date, datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from app.domain.auth.model import Actor, Role
from app.domain.booking.model import Booking, BookingStatus, SeatStatus
from app.domain.booking.service import BookingService
from app.domain.catalog.model import Movie
from app.domain.cinema.model import Room, SeatType, generate_seats
from app.domain.errors import (
    BusinessRuleViolation,
    ForbiddenError,
    NotFoundError,
    ShowtimeOverlapError,
)
from app.domain.scheduling.model import Showtime, overlaps, seat_price
from app.domain.scheduling.service import ShowtimeService
from tests.unit.fakes import FakeUnitOfWork

ADMIN = Actor(uuid4(), Role.ADMIN)
CUSTOMER = Actor(uuid4(), Role.CUSTOMER)
HCM = ZoneInfo("Asia/Ho_Chi_Minh")
T = datetime(2026, 10, 20, 10, 0, tzinfo=UTC)


def at(minutes: int) -> datetime:
    return T + timedelta(minutes=minutes)


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        ((0, 120), (60, 180), True),  # partial overlap
        ((0, 120), (30, 60), True),  # b inside a
        ((30, 60), (0, 120), True),  # a inside b
        ((0, 120), (0, 120), True),  # identical
        ((0, 120), (120, 240), False),  # back to back: a ends when b starts
        ((120, 240), (0, 120), False),  # back to back, other order
        ((0, 120), (121, 200), False),  # gap
    ],
)
def test_overlaps(a: tuple[int, int], b: tuple[int, int], expected: bool) -> None:
    assert overlaps(at(a[0]), at(a[1]), at(b[0]), at(b[1])) is expected


def test_vip_price_is_base_times_1_3_in_whole_vnd() -> None:
    assert seat_price(90_000, SeatType.STANDARD) == 90_000
    assert seat_price(90_000, SeatType.VIP) == 117_000
    assert seat_price(75_005, SeatType.VIP) == 97_506  # rounds down, no floats


@pytest.fixture
def uow() -> FakeUnitOfWork:
    uow = FakeUnitOfWork()
    uow.movies.add(Movie(uuid4(), "Mai", "", 120, "", ""))
    room = Room(uuid4(), "Phòng 1", 2, 2)
    uow.rooms.add(room, generate_seats(room.id, 2, 2, {2}))
    uow.rooms.add(Room(uuid4(), "Phòng 2", 1, 1), [])
    return uow


@pytest.fixture
def service(uow: FakeUnitOfWork) -> ShowtimeService:
    return ShowtimeService(uow, HCM)


def _create(
    service: ShowtimeService, uow: FakeUnitOfWork, start: datetime, room: str = "Phòng 1"
) -> Showtime:
    movie = next(iter(uow.movies.rows.values()))
    room_id = next(r.id for r in uow.rooms.rows.values() if r.name == room)
    return service.create_showtime(
        ADMIN, movie_id=movie.id, room_id=room_id, starts_at=start, base_price=90_000
    )


def test_create_computes_ends_at_from_movie_duration(
    service: ShowtimeService, uow: FakeUnitOfWork
) -> None:
    showtime = _create(service, uow, at(0))

    assert showtime.ends_at == at(120)
    assert uow.showtimes.get(showtime.id) == showtime


def test_create_rejects_overlap_in_same_room(service: ShowtimeService, uow: FakeUnitOfWork) -> None:
    _create(service, uow, at(0))

    with pytest.raises(ShowtimeOverlapError):
        _create(service, uow, at(119))
    with pytest.raises(ShowtimeOverlapError):
        _create(service, uow, at(-119))


def test_back_to_back_and_other_room_are_allowed(
    service: ShowtimeService, uow: FakeUnitOfWork
) -> None:
    _create(service, uow, at(0))

    _create(service, uow, at(120))
    _create(service, uow, at(-120))
    _create(service, uow, at(30), room="Phòng 2")

    assert len(uow.showtimes.rows) == 4


def test_create_requires_admin_existing_refs_and_aware_time(
    service: ShowtimeService, uow: FakeUnitOfWork
) -> None:
    movie_id = next(iter(uow.movies.rows))
    room_id = next(iter(uow.rooms.rows))
    args = {"movie_id": movie_id, "room_id": room_id, "starts_at": at(0), "base_price": 90_000}

    with pytest.raises(ForbiddenError):
        service.create_showtime(CUSTOMER, **args)
    with pytest.raises(NotFoundError):
        service.create_showtime(ADMIN, **{**args, "movie_id": uuid4()})
    with pytest.raises(NotFoundError):
        service.create_showtime(ADMIN, **{**args, "room_id": uuid4()})
    with pytest.raises(BusinessRuleViolation):
        naive = at(0).replace(tzinfo=None)
        service.create_showtime(ADMIN, **{**args, "starts_at": naive})


def test_date_filter_uses_cinema_local_day(service: ShowtimeService, uow: FakeUnitOfWork) -> None:
    service.list_showtimes(None, date(2026, 10, 20), 1, 20)

    _, starts_from, starts_before = uow.showtimes.last_search
    # 20/10 in Asia/Ho_Chi_Minh (UTC+7) is 19/10 17:00 UTC to 20/10 17:00 UTC.
    assert starts_from == datetime(2026, 10, 19, 17, 0, tzinfo=UTC)
    assert starts_before == datetime(2026, 10, 20, 17, 0, tzinfo=UTC)


def test_seat_map_prices_vip_rows_and_keeps_seat_order(
    service: ShowtimeService, uow: FakeUnitOfWork
) -> None:
    showtime = _create(service, uow, at(0))

    # The seat map belongs to booking, which owns the inventory scheduling created.
    seat_map = BookingService(uow, 300, 2, 5).seat_map(showtime.id)

    assert seat_map.showtime == showtime
    assert seat_map.movie.id == showtime.movie_id
    assert seat_map.room.name == "Phòng 1"
    entries = seat_map.seats
    assert [f"{e.seat.row_label}{e.seat.number}" for e in entries] == ["A1", "A2", "B1", "B2"]
    assert [e.price for e in entries] == [90_000, 90_000, 117_000, 117_000]
    assert {e.status for e in entries} == {SeatStatus.AVAILABLE}


def test_delete_showtime(service: ShowtimeService, uow: FakeUnitOfWork) -> None:
    showtime = _create(service, uow, at(0))

    with pytest.raises(ForbiddenError):
        service.delete_showtime(CUSTOMER, showtime.id)
    service.delete_showtime(ADMIN, showtime.id)

    assert uow.showtimes.get(showtime.id) is None
    with pytest.raises(NotFoundError):
        service.delete_showtime(ADMIN, showtime.id)


def _update(
    service: ShowtimeService, showtime: Showtime, start: datetime, **overrides: object
) -> Showtime:
    fields: dict[str, object] = {
        "movie_id": showtime.movie_id,
        "room_id": showtime.room_id,
        "starts_at": start,
        "base_price": showtime.base_price,
        "is_open_for_booking": True,
        **overrides,
    }
    return service.update_showtime(ADMIN, showtime.id, **fields)  # type: ignore[arg-type]


def test_update_moves_showtime_and_checks_overlap(
    service: ShowtimeService, uow: FakeUnitOfWork
) -> None:
    first = _create(service, uow, at(0))
    second = _create(service, uow, at(240))

    moved = _update(service, first, at(30), base_price=100_000)

    assert (moved.starts_at, moved.ends_at, moved.base_price) == (at(30), at(150), 100_000)
    assert uow.showtimes.get(first.id) == moved
    with pytest.raises(ShowtimeOverlapError):
        _update(service, second, at(100))
    with pytest.raises(NotFoundError):
        service.update_showtime(
            ADMIN,
            uuid4(),
            movie_id=first.movie_id,
            room_id=first.room_id,
            starts_at=at(0),
            base_price=1,
            is_open_for_booking=True,
        )


def test_update_to_other_room_rebuilds_inventory(
    service: ShowtimeService, uow: FakeUnitOfWork
) -> None:
    showtime = _create(service, uow, at(0))
    other_room = Room(uuid4(), "Phòng 3", 1, 3)
    uow.rooms.add(other_room, generate_seats(other_room.id, 1, 3, set()))

    _update(service, showtime, at(0), room_id=other_room.id)

    inventory = {
        seat_id for showtime_id, seat_id in uow.inventory.rows if showtime_id == showtime.id
    }
    assert inventory == {seat.id for seat in uow.rooms.seats(other_room.id)}


def test_booked_showtime_only_changes_price_and_sale_flag(
    service: ShowtimeService, uow: FakeUnitOfWork
) -> None:
    showtime = _create(service, uow, at(0))
    uow.bookings.add(
        Booking(uuid4(), uuid4(), showtime.id, BookingStatus.HELD, at(-60), at(-55), 0, [])
    )

    closed = _update(service, showtime, at(0), base_price=80_000, is_open_for_booking=False)

    assert (closed.base_price, closed.is_open_for_booking) == (80_000, False)
    with pytest.raises(BusinessRuleViolation):
        _update(service, showtime, at(30))
