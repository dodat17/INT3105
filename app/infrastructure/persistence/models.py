from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    # Deterministic constraint names so Alembic migrations can reference them.
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('CUSTOMER', 'ADMIN')", name="role"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    full_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class MovieModel(Base):
    __tablename__ = "movies"
    __table_args__ = (CheckConstraint("duration_minutes > 0", name="duration_positive"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    genre: Mapped[str] = mapped_column(String(100))
    age_rating: Mapped[str] = mapped_column(String(10))


class RoomModel(Base):
    __tablename__ = "rooms"
    __table_args__ = (CheckConstraint("rows > 0 AND cols > 0", name="size_positive"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    rows: Mapped[int] = mapped_column(Integer)
    cols: Mapped[int] = mapped_column(Integer)


class SeatModel(Base):
    __tablename__ = "seats"
    __table_args__ = (
        # No two seats share a position in the same room.
        UniqueConstraint("room_id", "row_label", "number", name="uq_seats_position"),
        CheckConstraint("number > 0", name="number_positive"),
        CheckConstraint("seat_type IN ('STANDARD', 'VIP')", name="seat_type"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    room_id: Mapped[UUID] = mapped_column(ForeignKey("rooms.id", ondelete="RESTRICT"))
    row_label: Mapped[str] = mapped_column(String(2))
    number: Mapped[int] = mapped_column(Integer)
    seat_type: Mapped[str] = mapped_column(String(16))


class ShowtimeModel(Base):
    __tablename__ = "showtimes"
    __table_args__ = (
        CheckConstraint("ends_at > starts_at", name="window"),
        CheckConstraint("base_price > 0", name="base_price_positive"),
        Index("ix_showtimes_room_id_starts_at", "room_id", "starts_at"),
        Index("ix_showtimes_movie_id_starts_at", "movie_id", "starts_at"),
        Index("ix_showtimes_starts_at_id", "starts_at", "id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    movie_id: Mapped[UUID] = mapped_column(ForeignKey("movies.id", ondelete="RESTRICT"))
    room_id: Mapped[UUID] = mapped_column(ForeignKey("rooms.id", ondelete="RESTRICT"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    base_price: Mapped[int] = mapped_column(BigInteger)


class BookingModel(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("status IN ('HELD', 'CONFIRMED', 'CANCELLED')", name="status"),
        CheckConstraint("total_amount >= 0", name="total_non_negative"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    showtime_id: Mapped[UUID] = mapped_column(ForeignKey("showtimes.id", ondelete="RESTRICT"), index=True)
    status: Mapped[str] = mapped_column(String(16), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_amount: Mapped[int] = mapped_column(BigInteger)
    booking_code: Mapped[str | None] = mapped_column(String(16), nullable=True, unique=True)


class BookingItemModel(Base):
    __tablename__ = "booking_items"
    __table_args__ = (
        UniqueConstraint("booking_id", "seat_id", name="uq_booking_items_booking_seat"),
        CheckConstraint("unit_price >= 0", name="unit_price_non_negative"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    booking_id: Mapped[UUID] = mapped_column(ForeignKey("bookings.id", ondelete="RESTRICT"), index=True)
    seat_id: Mapped[UUID] = mapped_column(ForeignKey("seats.id", ondelete="RESTRICT"))
    row_label: Mapped[str] = mapped_column(String(2))
    number: Mapped[int] = mapped_column(Integer)
    seat_type: Mapped[str] = mapped_column(String(16))
    unit_price: Mapped[int] = mapped_column(BigInteger)


class ShowtimeSeatModel(Base):
    __tablename__ = "showtime_seats"
    __table_args__ = (
        CheckConstraint("state IN ('AVAILABLE', 'HELD', 'BOOKED')", name="state"),
    )

    showtime_id: Mapped[UUID] = mapped_column(ForeignKey("showtimes.id", ondelete="CASCADE"), primary_key=True)
    seat_id: Mapped[UUID] = mapped_column(ForeignKey("seats.id", ondelete="RESTRICT"), primary_key=True)
    state: Mapped[str] = mapped_column(String(12), default="AVAILABLE")
    booking_id: Mapped[UUID | None] = mapped_column(ForeignKey("bookings.id", ondelete="RESTRICT"), nullable=True, index=True)
    hold_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
