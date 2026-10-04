from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from app.domain.auth.model import Actor, IssuedToken, Role, User
from app.domain.catalog.model import Movie


@dataclass(frozen=True)
class Page[T]:
    items: list[T]
    page: int
    page_size: int
    total_items: int


class UserRepository(Protocol):
    def get(self, user_id: UUID) -> User | None: ...
    def get_by_email(self, email: str) -> User | None: ...

    def add(self, user: User) -> None:
        """Raise EmailAlreadyUsedError when the email is taken (BR-01)."""


class MovieRepository(Protocol):
    def get(self, movie_id: UUID) -> Movie | None: ...
    def search(self, query: str | None, page: int, page_size: int) -> Page[Movie]: ...
    def add(self, movie: Movie) -> None: ...
    def delete(self, movie_id: UUID) -> None: ...


class UnitOfWork(Protocol):
    @property
    def users(self) -> UserRepository: ...
    @property
    def movies(self) -> MovieRepository: ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Roll back anything not committed."""

    def commit(self) -> None: ...


UnitOfWorkFactory = Callable[[], UnitOfWork]


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...
    def verify(self, password: str, password_hash: str) -> bool: ...


class TokenService(Protocol):
    def issue(self, user_id: UUID, role: Role) -> IssuedToken: ...

    def decode(self, token: str) -> Actor:
        """Raise InvalidTokenError when the token is malformed, forged or expired."""


class Clock(Protocol):
    def now(self) -> datetime: ...
