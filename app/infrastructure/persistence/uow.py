from types import TracebackType
from typing import Self

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.clock import DatabaseClock
from app.infrastructure.persistence.repositories import (
    SqlAlchemyBookingRepository,
    SqlAlchemyMovieRepository,
    SqlAlchemyRoomRepository,
    SqlAlchemyShowtimeRepository,
    SqlAlchemySeatInventoryRepository,
    SqlAlchemyUserRepository,
)


def create_session_factory(database_url: str, pool_size: int) -> sessionmaker[Session]:
    engine: Engine = create_engine(database_url, pool_size=pool_size, pool_pre_ping=True)
    return sessionmaker(engine, expire_on_commit=False)


class SqlAlchemyUnitOfWork:
    """One Session and one transaction per use case."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> Self:
        self._session = self._session_factory()
        self.users = SqlAlchemyUserRepository(self._session)
        self.movies = SqlAlchemyMovieRepository(self._session)
        self.rooms = SqlAlchemyRoomRepository(self._session)
        self.showtimes = SqlAlchemyShowtimeRepository(self._session)
        self.bookings = SqlAlchemyBookingRepository(self._session)
        self.inventory = SqlAlchemySeatInventoryRepository(self._session)
        self.clock = DatabaseClock(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._session.rollback()
        self._session.close()

    def commit(self) -> None:
        self._session.commit()
