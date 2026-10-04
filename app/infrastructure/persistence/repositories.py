from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.auth.model import Role, User
from app.domain.catalog.model import Movie
from app.domain.errors import EmailAlreadyUsedError
from app.domain.ports import Page
from app.infrastructure.persistence.models import MovieModel, UserModel


def _utc(value: datetime) -> datetime:
    # SQLite drops the offset; every stored timestamp is UTC.
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _to_user(row: UserModel) -> User:
    return User(
        id=row.id,
        email=row.email,
        password_hash=row.password_hash,
        full_name=row.full_name,
        role=Role(row.role),
        created_at=_utc(row.created_at),
    )


def _to_movie(row: MovieModel) -> Movie:
    return Movie(
        id=row.id,
        title=row.title,
        description=row.description,
        duration_minutes=row.duration_minutes,
        genre=row.genre,
        age_rating=row.age_rating,
    )


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: UUID) -> User | None:
        row = self._session.get(UserModel, user_id)
        return _to_user(row) if row else None

    def get_by_email(self, email: str) -> User | None:
        row = self._session.scalar(select(UserModel).where(UserModel.email == email))
        return _to_user(row) if row else None

    def add(self, user: User) -> None:
        self._session.add(
            UserModel(
                id=user.id,
                email=user.email,
                password_hash=user.password_hash,
                full_name=user.full_name,
                role=user.role.value,
                created_at=user.created_at,
            )
        )
        try:
            # Flush now so a concurrent duplicate surfaces as BR-01, not a 500 at commit.
            self._session.flush()
        except IntegrityError as exc:
            raise EmailAlreadyUsedError from exc


class SqlAlchemyMovieRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, movie_id: UUID) -> Movie | None:
        row = self._session.get(MovieModel, movie_id)
        return _to_movie(row) if row else None

    def search(self, query: str | None, page: int, page_size: int) -> Page[Movie]:
        stmt = select(MovieModel)
        if query:
            stmt = stmt.where(MovieModel.title.icontains(query, autoescape=True))
        total = self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = self._session.scalars(
            stmt.order_by(MovieModel.title, MovieModel.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return Page(
            items=[_to_movie(row) for row in rows],
            page=page,
            page_size=page_size,
            total_items=total,
        )

    def add(self, movie: Movie) -> None:
        self._session.add(
            MovieModel(
                id=movie.id,
                title=movie.title,
                description=movie.description,
                duration_minutes=movie.duration_minutes,
                genre=movie.genre,
                age_rating=movie.age_rating,
            )
        )

    def delete(self, movie_id: UUID) -> None:
        self._session.execute(delete(MovieModel).where(MovieModel.id == movie_id))
