from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from app.domain.catalog.model import Movie
from app.domain.ports import Page, UnitOfWork


class MovieRepository(Protocol):
    def get(self, movie_id: UUID) -> Movie | None: ...
    def search(self, query: str | None, page: int, page_size: int) -> Page[Movie]: ...
    def add(self, movie: Movie) -> None: ...
    def update(self, movie: Movie) -> None: ...
    def delete(self, movie_id: UUID) -> None: ...


class MovieUsage(Protocol):
    """Answered by scheduling, which owns showtimes; catalog never imports it (BR-27)."""

    def exists_for_movie(self, movie_id: UUID) -> bool: ...


class CatalogUnitOfWork(UnitOfWork, Protocol):
    @property
    def movies(self) -> MovieRepository: ...
    @property
    def showtimes(self) -> MovieUsage: ...


CatalogUnitOfWorkFactory = Callable[[], CatalogUnitOfWork]
