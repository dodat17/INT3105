from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from cinema_booking.domain.enums import BookingStatus, SeatType, UserRole


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MovieModel(Base):
    __tablename__ = "movies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    genre: Mapped[str] = mapped_column(String(100))
    age_rating: Mapped[str] = mapped_column(String(20))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class RoomModel(Base):
    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    rows: Mapped[int] = mapped_column(Integer)
    cols: Mapped[int] = mapped_column(Integer)
    seats: Mapped[list["SeatModel"]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )


class SeatModel(Base):
    __tablename__ = "seats"
    __table_args__ = (UniqueConstraint("room_id", "row_label", "number"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"), index=True)
    row_label: Mapped[str] = mapped_column(String(2))
    number: Mapped[int] = mapped_column(Integer)
    seat_type: Mapped[SeatType] = mapped_column(Enum(SeatType))
    room: Mapped[RoomModel] = relationship(back_populates="seats")


class ShowtimeModel(Base):
    __tablename__ = "showtimes"
    __table_args__ = (
        Index("ix_showtimes_room_starts", "room_id", "starts_at"),
        Index("ix_showtimes_movie_starts", "movie_id", "starts_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    movie_id: Mapped[str] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"))
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    base_price: Mapped[int] = mapped_column(Integer)


class BookingModel(Base):
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    showtime_id: Mapped[str] = mapped_column(ForeignKey("showtimes.id"), index=True)
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus))
    total_price: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    tickets: Mapped[list["TicketModel"]] = relationship(
        back_populates="booking", cascade="all, delete-orphan", lazy="selectin"
    )


class TicketModel(Base):
    __tablename__ = "tickets"
    __table_args__ = (UniqueConstraint("showtime_id", "seat_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"))
    showtime_id: Mapped[str] = mapped_column(ForeignKey("showtimes.id"), index=True)
    seat_id: Mapped[str] = mapped_column(ForeignKey("seats.id"), index=True)
    price: Mapped[int] = mapped_column(Integer)
    booking: Mapped[BookingModel] = relationship(back_populates="tickets")
