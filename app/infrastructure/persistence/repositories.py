from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, delete, exists, func, or_, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.auth.model import Role, User
from app.domain.booking.model import (
    Booking,
    BookingItem,
    BookingStatus,
    InventorySeat,
    InventoryState,
)
from app.domain.catalog.model import Movie
from app.domain.cinema.model import Room, Seat, SeatType
from app.domain.errors import EmailAlreadyUsedError, RoomNameAlreadyUsedError
from app.domain.ports import Page
from app.domain.scheduling.model import Showtime
from app.infrastructure.persistence.models import (
    BookingItemModel,
    BookingModel,
    MovieModel,
    RoomModel,
    SeatModel,
    ShowtimeModel,
    ShowtimeSeatModel,
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

    def lock(self, user_id: UUID) -> User | None:
        row = self._session.scalar(
            select(UserModel).where(UserModel.id == user_id).with_for_update()
        )
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

    def update(self, movie: Movie) -> None:
        self._session.execute(
            update(MovieModel)
            .where(MovieModel.id == movie.id)
            .values(
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
        is_open_for_booking=row.is_open_for_booking,
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
        self._add_seats(seats)

    def _add_seats(self, seats: list[Seat]) -> None:
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
                is_open_for_booking=showtime.is_open_for_booking,
            )
        )

    def update(self, showtime: Showtime) -> None:
        self._session.execute(
            update(ShowtimeModel)
            .where(ShowtimeModel.id == showtime.id)
            .values(
                movie_id=showtime.movie_id,
                room_id=showtime.room_id,
                starts_at=_to_db(showtime.starts_at),
                ends_at=_to_db(showtime.ends_at),
                base_price=showtime.base_price,
                is_open_for_booking=showtime.is_open_for_booking,
            )
        )

    def delete(self, showtime_id: UUID) -> None:
        self._session.execute(delete(ShowtimeModel).where(ShowtimeModel.id == showtime_id))


def _to_booking(row: BookingModel, items: list[BookingItemModel]) -> Booking:
    return Booking(
        id=row.id,
        user_id=row.user_id,
        showtime_id=row.showtime_id,
        status=BookingStatus(row.status),
        created_at=_utc(row.created_at),
        expires_at=_utc(row.expires_at),
        total_amount=row.total_amount,
        items=[
            BookingItem(
                item.seat_id, item.row_label, item.number, SeatType(item.seat_type), item.unit_price
            )
            for item in items
        ],
        confirmed_at=_utc(row.confirmed_at) if row.confirmed_at else None,
        cancelled_at=_utc(row.cancelled_at) if row.cancelled_at else None,
        booking_code=row.booking_code,
    )


class SqlAlchemyBookingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _items(self, booking_id: UUID) -> list[BookingItemModel]:
        return list(
            self._session.scalars(
                select(BookingItemModel)
                .where(BookingItemModel.booking_id == booking_id)
                .order_by(BookingItemModel.row_label, BookingItemModel.number)
            )
        )

    def get(self, booking_id: UUID, *, lock: bool = False) -> Booking | None:
        stmt = select(BookingModel).where(BookingModel.id == booking_id)
        if lock:
            stmt = stmt.with_for_update()
        row = self._session.scalar(stmt)
        return _to_booking(row, self._items(row.id)) if row else None

    def list_for_user(
        self, user_id: UUID, status: BookingStatus | None, now: datetime, page: int, page_size: int
    ) -> Page[Booking]:
        stmt = select(BookingModel).where(BookingModel.user_id == user_id)
        decision_instant = _to_db(now)
        if status is BookingStatus.HELD:
            stmt = stmt.where(
                BookingModel.status == BookingStatus.HELD.value,
                BookingModel.expires_at > decision_instant,
            )
        elif status is BookingStatus.EXPIRED:
            stmt = stmt.where(
                BookingModel.status == BookingStatus.HELD.value,
                BookingModel.expires_at <= decision_instant,
            )
        elif status is not None:
            stmt = stmt.where(BookingModel.status == status.value)

        total = self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = list(
            self._session.scalars(
                stmt.order_by(BookingModel.created_at.desc(), BookingModel.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        bookings = [_to_booking(row, self._items(row.id)) for row in rows]
        effective = [
            booking.with_status(BookingStatus.EXPIRED)
            if booking.status is BookingStatus.HELD and booking.expires_at <= now
            else booking
            for booking in bookings
        ]
        return Page(effective, page, page_size, int(total))

    def count_effective_holds(
        self, user_id: UUID, now: datetime, showtime_id: UUID | None = None
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(BookingModel)
            .where(
                BookingModel.user_id == user_id,
                BookingModel.status == BookingStatus.HELD.value,
                BookingModel.expires_at > _to_db(now),
            )
        )
        if showtime_id is not None:
            stmt = stmt.where(BookingModel.showtime_id == showtime_id)
        return int(self._session.scalar(stmt) or 0)

    def exists_for_showtime(self, showtime_id: UUID) -> bool:
        return bool(
            self._session.scalar(select(exists().where(BookingModel.showtime_id == showtime_id)))
        )

    def add(self, booking: Booking) -> None:
        self._session.add(
            BookingModel(
                id=booking.id,
                user_id=booking.user_id,
                showtime_id=booking.showtime_id,
                status=booking.status.value,
                created_at=_to_db(booking.created_at),
                expires_at=_to_db(booking.expires_at),
                total_amount=booking.total_amount,
                confirmed_at=booking.confirmed_at,
                cancelled_at=booking.cancelled_at,
                booking_code=booking.booking_code,
            )
        )
        self._session.flush()
        self._session.add_all(
            BookingItemModel(
                id=__import__("uuid").uuid4(),
                booking_id=booking.id,
                seat_id=item.seat_id,
                row_label=item.row_label,
                number=item.number,
                seat_type=item.seat_type.value,
                unit_price=item.unit_price,
            )
            for item in booking.items
        )
        self._session.flush()

    def update(self, booking: Booking) -> None:
        self._session.execute(
            update(BookingModel)
            .where(BookingModel.id == booking.id)
            .values(
                status=booking.status.value,
                confirmed_at=booking.confirmed_at,
                cancelled_at=booking.cancelled_at,
                booking_code=booking.booking_code,
            )
        )


class SqlAlchemySeatInventoryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def initialize(self, showtime_id: UUID, seats: list[Seat]) -> None:
        self._session.add_all(
            ShowtimeSeatModel(
                showtime_id=showtime_id, seat_id=seat.id, state=InventoryState.AVAILABLE.value
            )
            for seat in seats
        )

    def reset(self, showtime_id: UUID, seats: list[Seat]) -> None:
        self._session.execute(
            delete(ShowtimeSeatModel).where(ShowtimeSeatModel.showtime_id == showtime_id)
        )
        self.initialize(showtime_id, seats)

    def lock(self, showtime_id: UUID, seat_ids: list[UUID]) -> list[InventorySeat]:
        rows = self._session.execute(
            select(ShowtimeSeatModel, SeatModel)
            .join(SeatModel, SeatModel.id == ShowtimeSeatModel.seat_id)
            .where(
                ShowtimeSeatModel.showtime_id == showtime_id,
                ShowtimeSeatModel.seat_id.in_(seat_ids),
            )
            .order_by(ShowtimeSeatModel.seat_id)
            .with_for_update()
        ).all()
        return [
            InventorySeat(
                _to_seat(seat),
                InventoryState(inv.state),
                inv.booking_id,
                _utc(inv.hold_expires_at) if inv.hold_expires_at else None,
            )
            for inv, seat in rows
        ]

    def acquire(
        self,
        showtime_id: UUID,
        seat_ids: list[UUID],
        booking_id: UUID,
        expires_at: datetime,
        now: datetime,
    ) -> bool:
        result = self._session.execute(
            update(ShowtimeSeatModel)
            .where(
                ShowtimeSeatModel.showtime_id == showtime_id,
                ShowtimeSeatModel.seat_id.in_(seat_ids),
                or_(
                    ShowtimeSeatModel.state == InventoryState.AVAILABLE.value,
                    and_(
                        ShowtimeSeatModel.state == InventoryState.HELD.value,
                        ShowtimeSeatModel.hold_expires_at <= _to_db(now),
                    ),
                ),
            )
            .values(
                state=InventoryState.HELD.value,
                booking_id=booking_id,
                hold_expires_at=_to_db(expires_at),
            )
        )
        return isinstance(result, CursorResult) and result.rowcount == len(seat_ids)

    def mark_booked(self, booking_id: UUID, now: datetime) -> int:
        result = self._session.execute(
            update(ShowtimeSeatModel)
            .where(
                ShowtimeSeatModel.booking_id == booking_id,
                ShowtimeSeatModel.state == InventoryState.HELD.value,
                ShowtimeSeatModel.hold_expires_at > _to_db(now),
            )
            .values(state=InventoryState.BOOKED.value, hold_expires_at=None)
        )
        return int(result.rowcount) if isinstance(result, CursorResult) else 0

    def release(self, booking_id: UUID) -> int:
        result = self._session.execute(
            update(ShowtimeSeatModel)
            .where(
                ShowtimeSeatModel.booking_id == booking_id,
                ShowtimeSeatModel.state == InventoryState.HELD.value,
            )
            .values(state=InventoryState.AVAILABLE.value, booking_id=None, hold_expires_at=None)
        )
        return int(result.rowcount) if isinstance(result, CursorResult) else 0

    def statuses(self, showtime_id: UUID, now: datetime) -> dict[UUID, str]:
        rows = self._session.scalars(
            select(ShowtimeSeatModel).where(ShowtimeSeatModel.showtime_id == showtime_id)
        )
        return {
            row.seat_id: (
                InventoryState.AVAILABLE.value
                if row.state == InventoryState.HELD.value
                and row.hold_expires_at is not None
                and _utc(row.hold_expires_at) <= now
                else row.state
            )
            for row in rows
        }
