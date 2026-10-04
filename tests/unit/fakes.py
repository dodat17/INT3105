from datetime import UTC, datetime
from typing import Any, Self
from uuid import UUID

from app.domain.auth.model import IssuedToken, Role, User
from app.domain.catalog.model import Movie
from app.domain.errors import EmailAlreadyUsedError
from app.domain.ports import Page

NOW = datetime(2026, 10, 15, 3, 0, tzinfo=UTC)


class InMemoryUsers:
    def __init__(self) -> None:
        self.rows: dict[UUID, User] = {}

    def get(self, user_id: UUID) -> User | None:
        return self.rows.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.rows.values() if u.email == email), None)

    def add(self, user: User) -> None:
        if self.get_by_email(user.email):
            raise EmailAlreadyUsedError
        self.rows[user.id] = user


class InMemoryMovies:
    def __init__(self) -> None:
        self.rows: dict[UUID, Movie] = {}

    def get(self, movie_id: UUID) -> Movie | None:
        return self.rows.get(movie_id)

    def search(self, query: str | None, page: int, page_size: int) -> Page[Movie]:
        self.last_query = query
        found = [m for m in self.rows.values() if not query or query.lower() in m.title.lower()]
        start = (page - 1) * page_size
        return Page(found[start : start + page_size], page, page_size, len(found))

    def add(self, movie: Movie) -> None:
        self.rows[movie.id] = movie

    def delete(self, movie_id: UUID) -> None:
        del self.rows[movie_id]


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.users = InMemoryUsers()
        self.movies = InMemoryMovies()
        self.commits = 0

    def __call__(self) -> Self:
        return self

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    def commit(self) -> None:
        self.commits += 1


class FakeHasher:
    def __init__(self) -> None:
        self.hash_calls = 0

    def hash(self, password: str) -> str:
        self.hash_calls += 1
        return f"hashed:{password}"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{password}"


class FakeTokens:
    def issue(self, user_id: UUID, role: Role) -> IssuedToken:
        return IssuedToken(access_token=f"token:{user_id}:{role}", expires_in=60)

    def decode(self, token: str) -> Any:
        raise NotImplementedError


class FixedClock:
    def now(self) -> datetime:
        return NOW
