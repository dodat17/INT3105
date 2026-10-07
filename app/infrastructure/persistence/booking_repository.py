from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.booking.model import Booking, BookingStatus, Ticket
from app.infrastructure.persistence.models import BookingModel, TicketModel


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _to_db(value: datetime) -> datetime:
    return value.astimezone(UTC)


def _to_booking(row: BookingModel, tickets: tuple[Ticket, ...]) -> Booking:
    return Booking(
        id=row.id,
        user_id=row.user_id,
        showtime_id=row.showtime_id,
        status=BookingStatus(row.status),
        tickets=tickets,
        total_amount=row.total_amount,
        created_at=_utc(row.created_at),
        expires_at=_utc(row.expires_at),
        confirmed_at=_utc(row.confirmed_at) if row.confirmed_at else None,
        cancelled_at=_utc(row.cancelled_at) if row.cancelled_at else None,
        booking_code=row.booking_code,
    )


class SqlAlchemyBookingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, booking_id: UUID) -> Booking | None:
        row = self._session.get(BookingModel, booking_id)
        if row is None:
            return None
        ticket_rows = self._session.scalars(
            select(TicketModel)
            .where(TicketModel.booking_id == booking_id)
            .order_by(TicketModel.seat_id)
        )
        tickets = tuple(
            Ticket(
                id=ticket.id,
                booking_id=ticket.booking_id,
                seat_id=ticket.seat_id,
                unit_price=ticket.unit_price,
            )
            for ticket in ticket_rows
        )
        return _to_booking(row, tickets)

    def add(self, booking: Booking) -> None:
        self._session.add(
            BookingModel(
                id=booking.id,
                user_id=booking.user_id,
                showtime_id=booking.showtime_id,
                status=booking.status.value,
                total_amount=booking.total_amount,
                created_at=_to_db(booking.created_at),
                expires_at=_to_db(booking.expires_at),
                confirmed_at=(
                    _to_db(booking.confirmed_at) if booking.confirmed_at is not None else None
                ),
                cancelled_at=(
                    _to_db(booking.cancelled_at) if booking.cancelled_at is not None else None
                ),
                booking_code=booking.booking_code,
            )
        )
        self._session.add_all(
            TicketModel(
                id=ticket.id,
                booking_id=ticket.booking_id,
                seat_id=ticket.seat_id,
                unit_price=ticket.unit_price,
            )
            for ticket in booking.tickets
        )
