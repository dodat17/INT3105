from datetime import timedelta

import pytest

from cinema_booking.domain.errors import BusinessRuleViolation, Forbidden, ShowtimeOverlap
from cinema_booking.domain.services.showtime_service import ShowtimeService


def test_create_showtime_calculates_end_and_rejects_overlap(
    uow, clock, admin, customer, cinema_data
) -> None:
    movie, room, _seats, existing = cinema_data
    service = ShowtimeService(uow)

    with pytest.raises(Forbidden):
        service.create(customer, movie.id, room.id, existing.ends_at, 100_000)
    with pytest.raises(ShowtimeOverlap):
        service.create(
            admin,
            movie.id,
            room.id,
            existing.starts_at + timedelta(minutes=30),
            100_000,
        )

    created = service.create(admin, movie.id, room.id, existing.ends_at, 100_000)
    assert created.ends_at == created.starts_at + timedelta(minutes=movie.duration_minutes)


def test_showtime_with_booking_cannot_be_deleted(uow, admin, cinema_data) -> None:
    _movie, _room, _seats, showtime = cinema_data
    uow.showtimes.blocked_ids.add(showtime.id)

    with pytest.raises(BusinessRuleViolation):
        ShowtimeService(uow).delete(admin, showtime.id)
