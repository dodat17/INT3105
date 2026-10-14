from uuid import uuid4

from cinema_booking.domain.entities import Movie, User
from cinema_booking.domain.errors import BusinessRuleViolation, NotFound
from cinema_booking.domain.ports import UnitOfWork
from cinema_booking.domain.services.common import require_admin


class MovieService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def list(self, search: str | None = None, offset: int = 0, limit: int = 20) -> list[Movie]:
        with self._uow as uow:
            return uow.movies.list(search, offset, limit)

    def get(self, movie_id: str) -> Movie:
        with self._uow as uow:
            movie = uow.movies.get(movie_id)
            if movie is None:
                raise NotFound("Movie not found", {"movie_id": movie_id})
            return movie

    def create(
        self,
        actor: User,
        title: str,
        duration_minutes: int,
        genre: str,
        age_rating: str,
        description: str | None,
    ) -> Movie:
        require_admin(actor)
        if duration_minutes <= 0:
            raise BusinessRuleViolation("Movie duration must be positive")
        movie = Movie(
            id=str(uuid4()),
            title=title.strip(),
            duration_minutes=duration_minutes,
            genre=genre.strip(),
            age_rating=age_rating.strip(),
            description=description,
        )
        with self._uow as uow:
            uow.movies.add(movie)
            uow.commit()
        return movie

    def delete(self, actor: User, movie_id: str) -> None:
        require_admin(actor)
        with self._uow as uow:
            if uow.movies.get(movie_id) is None:
                raise NotFound("Movie not found", {"movie_id": movie_id})
            if uow.movies.has_confirmed_bookings(movie_id):
                raise BusinessRuleViolation("Movie has confirmed bookings")
            uow.movies.delete(movie_id)
            uow.commit()
