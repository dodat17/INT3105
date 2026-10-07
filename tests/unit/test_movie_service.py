from datetime import timedelta
from uuid import uuid4

import pytest

from app.domain.auth.model import Actor, Role
from app.domain.catalog.service import MovieService
from app.domain.errors import BusinessRuleViolation, ForbiddenError, NotFoundError
from app.domain.scheduling.model import Showtime
from tests.unit.fakes import NOW, FakeUnitOfWork

ADMIN = Actor(uuid4(), Role.ADMIN)
CUSTOMER = Actor(uuid4(), Role.CUSTOMER)
MOVIE = {
    "title": " Mai ",
    "description": "",
    "duration_minutes": 131,
    "genre": "Tâm lý",
    "age_rating": "T18",
}


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def service(uow: FakeUnitOfWork) -> MovieService:
    return MovieService(uow)


def test_admin_creates_movie(service: MovieService, uow: FakeUnitOfWork) -> None:
    movie = service.create_movie(ADMIN, **MOVIE)

    assert movie.title == "Mai"
    assert uow.movies.get(movie.id) == movie
    assert uow.commits == 1


def test_customer_cannot_create_or_delete_movie(service: MovieService) -> None:
    movie = service.create_movie(ADMIN, **MOVIE)

    with pytest.raises(ForbiddenError):
        service.create_movie(CUSTOMER, **MOVIE)
    with pytest.raises(ForbiddenError):
        service.delete_movie(CUSTOMER, movie.id)
    assert service.get_movie(movie.id) == movie


def test_create_rejects_non_positive_duration(service: MovieService) -> None:
    with pytest.raises(BusinessRuleViolation):
        service.create_movie(ADMIN, **{**MOVIE, "duration_minutes": 0})


def test_admin_deletes_movie(service: MovieService) -> None:
    movie = service.create_movie(ADMIN, **MOVIE)

    service.delete_movie(ADMIN, movie.id)

    with pytest.raises(NotFoundError):
        service.get_movie(movie.id)
    with pytest.raises(NotFoundError):
        service.delete_movie(ADMIN, movie.id)


def test_movie_with_showtimes_cannot_be_deleted(service: MovieService, uow: FakeUnitOfWork) -> None:
    movie = service.create_movie(ADMIN, **MOVIE)
    uow.showtimes.add(Showtime(uuid4(), movie.id, uuid4(), NOW, NOW + timedelta(hours=2), 90_000))

    with pytest.raises(BusinessRuleViolation):
        service.delete_movie(ADMIN, movie.id)
    assert service.get_movie(movie.id) == movie


def test_blank_search_means_no_filter(service: MovieService, uow: FakeUnitOfWork) -> None:
    service.list_movies("   ", 1, 20)

    assert uow.movies.last_query is None
