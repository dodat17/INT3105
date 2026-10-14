from dataclasses import dataclass

from fastapi import Request
from sqlalchemy.orm import Session, sessionmaker

from cinema_booking.domain.entities import User
from cinema_booking.domain.ports import Clock, PasswordHasher, TokenService
from cinema_booking.domain.services.auth_service import AuthService
from cinema_booking.domain.services.booking_service import BookingService
from cinema_booking.domain.services.movie_service import MovieService
from cinema_booking.domain.services.room_service import RoomService
from cinema_booking.domain.services.showtime_service import ShowtimeService
from cinema_booking.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


@dataclass(slots=True)
class Container:
    session_factory: sessionmaker[Session]
    hasher: PasswordHasher
    tokens: TokenService
    clock: Clock

    def uow(self) -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(self.session_factory)

    def auth_service(self) -> AuthService:
        return AuthService(self.uow(), self.hasher, self.tokens, self.clock)

    def movie_service(self) -> MovieService:
        return MovieService(self.uow())

    def room_service(self) -> RoomService:
        return RoomService(self.uow())

    def showtime_service(self) -> ShowtimeService:
        return ShowtimeService(self.uow())

    def booking_service(self) -> BookingService:
        return BookingService(self.uow(), self.clock)


def get_container(request: Request) -> Container:
    return request.app.state.container


def get_actor(request: Request) -> User:
    return request.state.actor
