from datetime import datetime, timezone

from cinema_booking.domain.entities import Booking, Movie, Room, Seat, Showtime, Ticket, User
from cinema_booking.infrastructure.database.models import (
    BookingModel,
    MovieModel,
    RoomModel,
    SeatModel,
    ShowtimeModel,
    UserModel,
)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def to_user(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        password_hash=model.password_hash,
        full_name=model.full_name,
        role=model.role,
        created_at=_aware(model.created_at),
    )


def to_movie(model: MovieModel) -> Movie:
    return Movie(
        id=model.id,
        title=model.title,
        duration_minutes=model.duration_minutes,
        genre=model.genre,
        age_rating=model.age_rating,
        description=model.description,
    )


def to_room(model: RoomModel) -> Room:
    return Room(id=model.id, name=model.name, rows=model.rows, cols=model.cols)


def to_seat(model: SeatModel) -> Seat:
    return Seat(
        id=model.id,
        room_id=model.room_id,
        row_label=model.row_label,
        number=model.number,
        seat_type=model.seat_type,
    )


def to_showtime(model: ShowtimeModel) -> Showtime:
    return Showtime(
        id=model.id,
        movie_id=model.movie_id,
        room_id=model.room_id,
        starts_at=_aware(model.starts_at),
        ends_at=_aware(model.ends_at),
        base_price=model.base_price,
    )


def to_booking(model: BookingModel) -> Booking:
    return Booking(
        id=model.id,
        user_id=model.user_id,
        showtime_id=model.showtime_id,
        status=model.status,
        total_price=model.total_price,
        created_at=_aware(model.created_at),
        tickets=[
            Ticket(
                id=ticket.id,
                booking_id=ticket.booking_id,
                showtime_id=ticket.showtime_id,
                seat_id=ticket.seat_id,
                price=ticket.price,
            )
            for ticket in model.tickets
        ],
    )
