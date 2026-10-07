from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.auth.model import Role, User
from app.domain.catalog.model import Movie
from app.domain.cinema.model import Room, Seat, SeatType
from app.domain.errors import EmailAlreadyUsedError, RoomNameAlreadyUsedError
from app.domain.ports import Page
from app.domain.scheduling.model import Showtime
from app.infrastructure.persistence.models import (
    MovieModel,
    RoomModel,
    SeatModel,
    ShowtimeModel,
    UserModel,
)


def _utc(value: datetime) -> datetime:
    # SQLite drops the offset; every stored timestamp is UTC.
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _to_db(value: datetime) -> datetime:
    # Store and compare in UTC so SQLite (no offset kept) and PostgreSQL agree.
    return value.astimezone(UTC)


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


def _to_room(row: RoomModel) -> Room:
    return Room(id=row.id, name=row.name, rows=row.rows, cols=row.cols)


def _to_seat(row: SeatModel) -> Seat:
    return Seat(
        id=row.id,
        room_id=row.room_id,
        row_label=row.row_label,
        number=row.number,
        seat_type=SeatType(row.seat_type),
    )


def _to_showtime(row: ShowtimeModel) -> Showtime:
    return Showtime(
        id=row.id,
        movie_id=row.movie_id,
        room_id=row.room_id,
        starts_at=_utc(row.starts_at),
        ends_at=_utc(row.ends_at),
        base_price=row.base_price,
    )


class SqlAlchemyRoomRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, room_id: UUID) -> Room | None:
        row = self._session.get(RoomModel, room_id)
        return _to_room(row) if row else None

    def get_by_name(self, name: str) -> Room | None:
        row = self._session.scalar(select(RoomModel).where(RoomModel.name == name))
        return _to_room(row) if row else None

    def list_all(self) -> list[Room]:
        rows = self._session.scalars(select(RoomModel).order_by(RoomModel.name, RoomModel.id))
        return [_to_room(row) for row in rows]

    def lock(self, room_id: UUID) -> Room | None:
        # SELECT ... FOR UPDATE on PostgreSQL; SQLite ignores it (single writer anyway).
        row = self._session.scalar(
            select(RoomModel).where(RoomModel.id == room_id).with_for_update()
        )
        return _to_room(row) if row else None

    def add(self, room: Room, seats: list[Seat]) -> None:
        self._session.add(RoomModel(id=room.id, name=room.name, rows=room.rows, cols=room.cols))
        try:
            # The room must exist before its seats reference it.
            self._session.flush()
        except IntegrityError as exc:
            raise RoomNameAlreadyUsedError from exc
        self._session.add_all(
            SeatModel(
                id=seat.id,
                room_id=seat.room_id,
                row_label=seat.row_label,
                number=seat.number,
                seat_type=seat.seat_type.value,
            )
            for seat in seats
        )

    def seats(self, room_id: UUID) -> list[Seat]:
        rows = self._session.scalars(
            select(SeatModel)
            .where(SeatModel.room_id == room_id)
            .order_by(SeatModel.row_label, SeatModel.number)
        )
        return [_to_seat(row) for row in rows]


class SqlAlchemyShowtimeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, showtime_id: UUID) -> Showtime | None:
        row = self._session.get(ShowtimeModel, showtime_id)
        return _to_showtime(row) if row else None

    def search(
        self,
        movie_id: UUID | None,
        starts_from: datetime | None,
        starts_before: datetime | None,
        page: int,
        page_size: int,
    ) -> Page[Showtime]:
        stmt = select(ShowtimeModel)
        if movie_id is not None:
            stmt = stmt.where(ShowtimeModel.movie_id == movie_id)
        if starts_from is not None:
            stmt = stmt.where(ShowtimeModel.starts_at >= _to_db(starts_from))
        if starts_before is not None:
            stmt = stmt.where(ShowtimeModel.starts_at < _to_db(starts_before))
        total = self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = self._session.scalars(
            stmt.order_by(ShowtimeModel.starts_at, ShowtimeModel.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return Page(
            items=[_to_showtime(row) for row in rows],
            page=page,
            page_size=page_size,
            total_items=total,
        )

    def find_overlapping(
        self, room_id: UUID, starts_at: datetime, ends_at: datetime
    ) -> list[Showtime]:
        rows = self._session.scalars(
            select(ShowtimeModel).where(
                ShowtimeModel.room_id == room_id,
                ShowtimeModel.starts_at < _to_db(ends_at),
                ShowtimeModel.ends_at > _to_db(starts_at),
            )
        )
        return [_to_showtime(row) for row in rows]

    def exists_for_movie(self, movie_id: UUID) -> bool:
        return bool(
            self._session.scalar(select(exists().where(ShowtimeModel.movie_id == movie_id)))
        )

    def add(self, showtime: Showtime) -> None:
        self._session.add(
            ShowtimeModel(
                id=showtime.id,
                movie_id=showtime.movie_id,
                room_id=showtime.room_id,
                starts_at=_to_db(showtime.starts_at),
                ends_at=_to_db(showtime.ends_at),
                base_price=showtime.base_price,
            )
        )

    def delete(self, showtime_id: UUID) -> None:
        self._session.execute(delete(ShowtimeModel).where(ShowtimeModel.id == showtime_id))
