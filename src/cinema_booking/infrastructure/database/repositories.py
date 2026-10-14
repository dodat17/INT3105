from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from cinema_booking.domain.entities import Booking, Movie, Room, Seat, Showtime, User
from cinema_booking.domain.enums import BookingStatus
from cinema_booking.domain.errors import EmailAlreadyUsed, SeatUnavailable
from cinema_booking.infrastructure.database.mappers import (
    to_booking,
    to_movie,
    to_room,
    to_seat,
    to_showtime,
    to_user,
)
from cinema_booking.infrastructure.database.models import (
    BookingModel,
    MovieModel,
    RoomModel,
    SeatModel,
    ShowtimeModel,
    TicketModel,
    UserModel,
)


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: str) -> User | None:
        model = self._session.get(UserModel, user_id)
        return to_user(model) if model else None

    def get_by_email(self, email: str) -> User | None:
        model = self._session.scalar(select(UserModel).where(UserModel.email == email))
        return to_user(model) if model else None

    def add(self, user: User) -> None:
        self._session.add(UserModel(**vars_from_slots(user)))
        try:
            self._session.flush()
        except IntegrityError as exc:
            raise EmailAlreadyUsed("Email is already registered", {"email": user.email}) from exc


class SqlAlchemyMovieRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, movie_id: str) -> Movie | None:
        model = self._session.get(MovieModel, movie_id)
        return to_movie(model) if model else None

    def list(self, search: str | None, offset: int, limit: int) -> list[Movie]:
        statement = select(MovieModel).order_by(MovieModel.title).offset(offset).limit(limit)
        if search:
            statement = statement.where(MovieModel.title.ilike(f"%{search}%"))
        return [to_movie(model) for model in self._session.scalars(statement)]

    def add(self, movie: Movie) -> None:
        self._session.add(MovieModel(**vars_from_slots(movie)))

    def delete(self, movie_id: str) -> None:
        self._session.execute(delete(MovieModel).where(MovieModel.id == movie_id))

    def has_confirmed_bookings(self, movie_id: str) -> bool:
        count = self._session.scalar(
            select(func.count())
            .select_from(BookingModel)
            .join(ShowtimeModel, BookingModel.showtime_id == ShowtimeModel.id)
            .where(
                ShowtimeModel.movie_id == movie_id,
                BookingModel.status == BookingStatus.CONFIRMED,
            )
        )
        return bool(count)


class SqlAlchemyRoomRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, room_id: str) -> Room | None:
        model = self._session.get(RoomModel, room_id)
        return to_room(model) if model else None

    def list(self) -> list[Room]:
        return [to_room(model) for model in self._session.scalars(select(RoomModel))]

    def add(self, room: Room, seats: list[Seat]) -> None:
        room_model = RoomModel(**vars_from_slots(room))
        room_model.seats = [SeatModel(**vars_from_slots(seat)) for seat in seats]
        self._session.add(room_model)

    def get_seats(self, room_id: str) -> list[Seat]:
        statement = (
            select(SeatModel)
            .where(SeatModel.room_id == room_id)
            .order_by(SeatModel.row_label, SeatModel.number)
        )
        return [to_seat(model) for model in self._session.scalars(statement)]

    def get_seats_by_ids(self, seat_ids: list[str]) -> list[Seat]:
        statement = select(SeatModel).where(SeatModel.id.in_(seat_ids))
        return [to_seat(model) for model in self._session.scalars(statement)]


class SqlAlchemyShowtimeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, showtime_id: str) -> Showtime | None:
        model = self._session.get(ShowtimeModel, showtime_id)
        return to_showtime(model) if model else None

    def list(self, movie_id: str | None, on_date: date | None) -> list[Showtime]:
        statement = select(ShowtimeModel).order_by(ShowtimeModel.starts_at)
        if movie_id:
            statement = statement.where(ShowtimeModel.movie_id == movie_id)
        if on_date:
            start = datetime.combine(on_date, time.min, tzinfo=timezone.utc)
            statement = statement.where(
                ShowtimeModel.starts_at >= start,
                ShowtimeModel.starts_at < start + timedelta(days=1),
            )
        return [to_showtime(model) for model in self._session.scalars(statement)]

    def add(self, showtime: Showtime) -> None:
        self._session.add(ShowtimeModel(**vars_from_slots(showtime)))

    def delete(self, showtime_id: str) -> None:
        self._session.execute(delete(ShowtimeModel).where(ShowtimeModel.id == showtime_id))

    def find_overlaps(
        self, room_id: str, starts_at: datetime, ends_at: datetime
    ) -> list[Showtime]:
        statement = select(ShowtimeModel).where(
            ShowtimeModel.room_id == room_id,
            ShowtimeModel.starts_at < ends_at,
            ShowtimeModel.ends_at > starts_at,
        )
        return [to_showtime(model) for model in self._session.scalars(statement)]

    def has_confirmed_bookings(self, showtime_id: str) -> bool:
        count = self._session.scalar(
            select(func.count()).select_from(BookingModel).where(
                BookingModel.showtime_id == showtime_id,
                BookingModel.status == BookingStatus.CONFIRMED,
            )
        )
        return bool(count)


class SqlAlchemyBookingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, booking_id: str) -> Booking | None:
        model = self._session.scalar(
            select(BookingModel)
            .options(selectinload(BookingModel.tickets))
            .where(BookingModel.id == booking_id)
        )
        return to_booking(model) if model else None

    def list_for_user(self, user_id: str) -> list[Booking]:
        statement = (
            select(BookingModel)
            .options(selectinload(BookingModel.tickets))
            .where(BookingModel.user_id == user_id)
            .order_by(BookingModel.created_at.desc())
        )
        return [to_booking(model) for model in self._session.scalars(statement)]

    def booked_seat_ids(self, showtime_id: str) -> set[str]:
        return set(
            self._session.scalars(
                select(TicketModel.seat_id).where(TicketModel.showtime_id == showtime_id)
            )
        )

    def add(self, booking: Booking) -> None:
        model = BookingModel(
            id=booking.id,
            user_id=booking.user_id,
            showtime_id=booking.showtime_id,
            status=booking.status,
            total_price=booking.total_price,
            created_at=booking.created_at,
        )
        model.tickets = [TicketModel(**vars_from_slots(ticket)) for ticket in booking.tickets]
        self._session.add(model)
        try:
            self._session.flush()
        except IntegrityError as exc:
            raise SeatUnavailable("One or more seats are unavailable") from exc

    def cancel(self, booking: Booking) -> None:
        model = self._session.get(BookingModel, booking.id)
        if model:
            model.status = BookingStatus.CANCELLED
            self._session.execute(
                delete(TicketModel).where(TicketModel.booking_id == booking.id)
            )


def vars_from_slots(instance: object) -> dict[str, object]:
    return {name: getattr(instance, name) for name in instance.__slots__}
