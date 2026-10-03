from uuid import UUID, uuid4

from app.domain.auth.model import Actor, require_admin
from app.domain.catalog.model import Movie
from app.domain.errors import BusinessRuleViolation, NotFoundError
from app.domain.ports import Page, UnitOfWorkFactory


class MovieService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    def list_movies(self, query: str | None, page: int, page_size: int) -> Page[Movie]:
        with self._uow_factory() as uow:
            return uow.movies.search((query or "").strip() or None, page, page_size)

    def get_movie(self, movie_id: UUID) -> Movie:
        with self._uow_factory() as uow:
            movie = uow.movies.get(movie_id)
        if movie is None:
            raise NotFoundError
        return movie

    def create_movie(
        self,
        actor: Actor,
        *,
        title: str,
        description: str,
        duration_minutes: int,
        genre: str,
        age_rating: str,
    ) -> Movie:
        require_admin(actor)
        if duration_minutes <= 0:
            raise BusinessRuleViolation("Thời lượng phim phải lớn hơn 0.")
        movie = Movie(
            id=uuid4(),
            title=title.strip(),
            description=description.strip(),
            duration_minutes=duration_minutes,
            genre=genre.strip(),
            age_rating=age_rating.strip(),
        )
        with self._uow_factory() as uow:
            uow.movies.add(movie)
            uow.commit()
        return movie

    def delete_movie(self, actor: Actor, movie_id: UUID) -> None:
        require_admin(actor)
        # BR-12 (no delete once CONFIRMED tickets exist) needs showtimes/bookings,
        # which arrive in milestones C/D; the check goes here then.
        with self._uow_factory() as uow:
            if uow.movies.get(movie_id) is None:
                raise NotFoundError
            uow.movies.delete(movie_id)
            uow.commit()
