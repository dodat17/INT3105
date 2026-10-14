from types import TracebackType

from sqlalchemy.orm import Session, sessionmaker

from cinema_booking.infrastructure.database.repositories import (
    SqlAlchemyBookingRepository,
    SqlAlchemyMovieRepository,
    SqlAlchemyRoomRepository,
    SqlAlchemyShowtimeRepository,
    SqlAlchemyUserRepository,
)


class SqlAlchemyUnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self._session_factory()
        self.users = SqlAlchemyUserRepository(self.session)
        self.movies = SqlAlchemyMovieRepository(self.session)
        self.rooms = SqlAlchemyRoomRepository(self.session)
        self.showtimes = SqlAlchemyShowtimeRepository(self.session)
        self.bookings = SqlAlchemyBookingRepository(self.session)
        self._committed = False
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if not self._committed or exc_type is not None:
            self.session.rollback()
        self.session.close()

    def commit(self) -> None:
        self.session.commit()
        self._committed = True
