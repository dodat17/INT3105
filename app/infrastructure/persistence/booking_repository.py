from collections import defaultdict
from datetime import datetime
from typing import Any, cast
from uuid import UUID

from sqlalchemy import and_, case, exists, func, or_, select, update
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.domain.booking.model import Booking, BookingStatus, Ticket
from app.domain.errors import SeatUnavailableError
from app.domain.ports import Page
from app.infrastructure.persistence.booking_mapper import as_utc, to_booking, to_db
from app.infrastructure.persistence.models import BookingModel, ShowtimeSeatModel, TicketModel


class SqlAlchemyBookingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, booking_id: UUID) -> Booking | None:
        row = self._session.get(BookingModel, booking_id)
        return self._booking(row) if row else None

    def get_for_update(self, booking_id: UUID) -> Booking | None:
        row = self._session.scalar(
            select(BookingModel).where(BookingModel.id == booking_id).with_for_update()
        )
        return self._booking(row) if row else None

    def search(
        self,
        user_id: UUID,
        status: str | None,
        now: datetime,
        page: int,
        page_size: int,
    ) -> Page[Booking]:
        now_db = to_db(now)
        stmt = select(BookingModel).where(BookingModel.user_id == user_id)
        if status == BookingStatus.HELD.value:
            stmt = stmt.where(
                BookingModel.status == BookingStatus.HELD.value,
                BookingModel.expires_at > now_db,
            )
        elif status == BookingStatus.EXPIRED.value:
            stmt = stmt.where(
                or_(
                    BookingModel.status == BookingStatus.EXPIRED.value,
                    and_(
                        BookingModel.status == BookingStatus.HELD.value,
                        BookingModel.expires_at <= now_db,
                    ),
                )
            )
        elif status is not None:
            stmt = stmt.where(BookingModel.status == status)
        total = self._session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = list(
            self._session.scalars(
                stmt.order_by(BookingModel.created_at.desc(), BookingModel.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        )
        tickets = self._tickets_by_booking([row.id for row in rows])
        return Page(
            items=[to_booking(row, tickets[row.id], now) for row in rows],
            page=page,
            page_size=page_size,
            total_items=total,
        )

    def add(self, booking: Booking) -> None:
        self._session.add(
            BookingModel(
                id=booking.id,
                user_id=booking.user_id,
                showtime_id=booking.showtime_id,
                status=booking.status.value,
                total_amount=booking.total_amount,
                created_at=to_db(booking.created_at),
                expires_at=to_db(booking.expires_at),
                confirmed_at=(
                    to_db(booking.confirmed_at) if booking.confirmed_at is not None else None
                ),
                cancelled_at=(
                    to_db(booking.cancelled_at) if booking.cancelled_at is not None else None
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

    def flush(self) -> None:
        try:
            self._session.flush()
        except IntegrityError as exc:
            raise SeatUnavailableError from exc

    def count_active_holds(
        self, user_id: UUID, showtime_id: UUID, now: datetime
    ) -> tuple[int, int]:
        per_showtime, total = self._session.execute(
            select(
                func.sum(case((BookingModel.showtime_id == showtime_id, 1), else_=0)),
                func.count(),
            ).where(
                BookingModel.user_id == user_id,
                BookingModel.status == BookingStatus.HELD.value,
                BookingModel.expires_at > to_db(now),
            )
        ).one()
        return int(cast(int, per_showtime or 0)), int(cast(int, total or 0))

    def lock_inventory(self, showtime_id: UUID, seat_ids: list[UUID]) -> int:
        try:
            rows = self._session.scalars(
                select(ShowtimeSeatModel.seat_id)
                .where(
                    ShowtimeSeatModel.showtime_id == showtime_id,
                    ShowtimeSeatModel.seat_id.in_(seat_ids),
                )
                .order_by(ShowtimeSeatModel.seat_id)
                .with_for_update()
            )
            return len(list(rows))
        except OperationalError as exc:
            raise SeatUnavailableError([str(seat_id) for seat_id in seat_ids]) from exc

    def acquire_holds(
        self,
        showtime_id: UUID,
        seat_ids: list[UUID],
        booking_id: UUID,
        expires_at: datetime,
        now: datetime,
    ) -> list[UUID]:
        rows = list(
            self._session.scalars(
                select(ShowtimeSeatModel).where(
                    ShowtimeSeatModel.showtime_id == showtime_id,
                    ShowtimeSeatModel.seat_id.in_(seat_ids),
                )
            )
        )
        unavailable = [
            row.seat_id
            for row in rows
            if row.state == "BOOKED"
            or (
                row.state == "HELD"
                and row.hold_expires_at is not None
                and as_utc(row.hold_expires_at) > now
            )
        ]
        if unavailable:
            return unavailable
        try:
            result = self._session.execute(
                update(ShowtimeSeatModel)
                .where(
                    ShowtimeSeatModel.showtime_id == showtime_id,
                    ShowtimeSeatModel.seat_id.in_(seat_ids),
                    or_(
                        ShowtimeSeatModel.state == "AVAILABLE",
                        and_(
                            ShowtimeSeatModel.state == "HELD",
                            ShowtimeSeatModel.hold_expires_at <= to_db(now),
                        ),
                    ),
                )
                .values(
                    state="HELD",
                    booking_id=booking_id,
                    hold_expires_at=to_db(expires_at),
                )
                .execution_options(synchronize_session=False)
            )
        except (IntegrityError, OperationalError) as exc:
            raise SeatUnavailableError([str(seat_id) for seat_id in seat_ids]) from exc
        rowcount = int(cast(Any, result).rowcount or 0)
        return [] if rowcount == len(seat_ids) else seat_ids

    def mark_booked(self, booking_id: UUID, now: datetime) -> int:
        result = self._session.execute(
            update(ShowtimeSeatModel)
            .where(
                ShowtimeSeatModel.booking_id == booking_id,
                ShowtimeSeatModel.state == "HELD",
                ShowtimeSeatModel.hold_expires_at > to_db(now),
            )
            .values(state="BOOKED", hold_expires_at=None)
            .execution_options(synchronize_session=False)
        )
        return int(cast(Any, result).rowcount or 0)

    def release_holds(self, booking_id: UUID) -> int:
        result = self._session.execute(
            update(ShowtimeSeatModel)
            .where(
                ShowtimeSeatModel.booking_id == booking_id,
                ShowtimeSeatModel.state == "HELD",
            )
            .values(state="AVAILABLE", booking_id=None, hold_expires_at=None)
            .execution_options(synchronize_session=False)
        )
        return int(cast(Any, result).rowcount or 0)

    def confirm(self, booking_id: UUID, confirmed_at: datetime, booking_code: str) -> None:
        self._session.execute(
            update(BookingModel)
            .where(BookingModel.id == booking_id)
            .values(
                status=BookingStatus.CONFIRMED.value,
                confirmed_at=to_db(confirmed_at),
                booking_code=booking_code,
            )
            .execution_options(synchronize_session=False)
        )

    def cancel(self, booking_id: UUID, cancelled_at: datetime) -> None:
        self._session.execute(
            update(BookingModel)
            .where(BookingModel.id == booking_id)
            .values(status=BookingStatus.CANCELLED.value, cancelled_at=to_db(cancelled_at))
            .execution_options(synchronize_session=False)
        )

    def seat_statuses(self, showtime_id: UUID, now: datetime) -> dict[UUID, str]:
        rows = self._session.scalars(
            select(ShowtimeSeatModel).where(ShowtimeSeatModel.showtime_id == showtime_id)
        )
        return {
            row.seat_id: (
                row.state
                if row.state == "BOOKED"
                or (
                    row.state == "HELD"
                    and row.hold_expires_at is not None
                    and as_utc(row.hold_expires_at) > now
                )
                else "AVAILABLE"
            )
            for row in rows
        }

    def exists_for_showtime(self, showtime_id: UUID) -> bool:
        return bool(
            self._session.scalar(select(exists().where(BookingModel.showtime_id == showtime_id)))
        )

    def _booking(self, row: BookingModel) -> Booking:
        return to_booking(row, self._tickets_by_booking([row.id])[row.id])

    def _tickets_by_booking(self, booking_ids: list[UUID]) -> dict[UUID, tuple[Ticket, ...]]:
        grouped: dict[UUID, list[Ticket]] = defaultdict(list)
        if booking_ids:
            rows = self._session.scalars(
                select(TicketModel)
                .where(TicketModel.booking_id.in_(booking_ids))
                .order_by(TicketModel.booking_id, TicketModel.seat_id)
            )
            for row in rows:
                grouped[row.booking_id].append(
                    Ticket(row.id, row.booking_id, row.seat_id, row.unit_price)
                )
        return {booking_id: tuple(grouped[booking_id]) for booking_id in booking_ids}
