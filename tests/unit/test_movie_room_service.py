import pytest

from cinema_booking.domain.errors import BusinessRuleViolation, Forbidden
from cinema_booking.domain.services.movie_service import MovieService
from cinema_booking.domain.services.room_service import RoomService
from tests.unit.fakes import FakeUnitOfWork


def test_admin_crud_and_customer_forbidden(uow, admin, customer) -> None:
    movies = MovieService(uow)
    rooms = RoomService(uow)

    with pytest.raises(Forbidden):
        movies.create(customer, "Movie", 90, "Drama", "P", None)
    movie = movies.create(admin, "Movie", 90, "Drama", "P", None)
    room, seats = rooms.create(admin, "Room", 2, 2, [2])

    assert movies.get(movie.id) == movie
    assert room.rows == 2
    assert len(seats) == 4
    assert sum(seat.seat_type.value == "VIP" for seat in seats) == 2


def test_movie_with_booking_cannot_be_deleted(uow: FakeUnitOfWork, admin) -> None:
    service = MovieService(uow)
    movie = service.create(admin, "Movie", 90, "Drama", "P", None)
    uow.movies.blocked_ids.add(movie.id)

    with pytest.raises(BusinessRuleViolation):
        service.delete(admin, movie.id)
