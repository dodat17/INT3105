from uuid import UUID, uuid4

from app.domain.auth.model import Actor, require_admin
from app.domain.catalog.model import Movie
from app.domain.catalog.ports import CatalogUnitOfWorkFactory
from app.domain.errors import BusinessRuleViolation, NotFoundError
from app.domain.ports import Page


class MovieService:
    def __init__(self, uow_factory: CatalogUnitOfWorkFactory) -> None:
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

    def update_movie(
        self,
        actor: Actor,
        movie_id: UUID,
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
            id=movie_id,
            title=title.strip(),
            description=description.strip(),
            duration_minutes=duration_minutes,
            genre=genre.strip(),
            age_rating=age_rating.strip(),
        )
        with self._uow_factory() as uow:
            current = uow.movies.get(movie_id)
            if current is None:
                raise NotFoundError
            # Scheduled showtimes computed their end from the old duration.
            if current.duration_minutes != duration_minutes and uow.showtimes.exists_for_movie(
                movie_id
            ):
                raise BusinessRuleViolation("Không thể đổi thời lượng của phim đang có suất chiếu.")
            uow.movies.update(movie)
            uow.commit()
        return movie

    def delete_movie(self, actor: Actor, movie_id: UUID) -> None:
        require_admin(actor)
        with self._uow_factory() as uow:
            if uow.movies.get(movie_id) is None:
                raise NotFoundError
            # Stricter than BR-12 until bookings exist: a scheduled movie is never deleted,
            # so no showtime is left pointing at a missing movie.
            if uow.showtimes.exists_for_movie(movie_id):
                raise BusinessRuleViolation("Không thể xóa phim đang có suất chiếu.")
            uow.movies.delete(movie_id)
            uow.commit()
