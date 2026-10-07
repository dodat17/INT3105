from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select, update

from app.bootstrap.settings import Settings
from app.domain.booking.model import Booking, BookingStatus, Ticket
from app.infrastructure.persistence.models import BookingModel, SeatModel, ShowtimeSeatModel
from app.infrastructure.persistence.uow import SqlAlchemyUnitOfWork, create_session_factory
from tests.api.conftest import create_showtime


def test_booking_repository_round_trip_and_showtime_inventory(
    client: TestClient,
    settings: Settings,
    admin_token: str,
    customer_token: str,
    setup: dict[str, str],
) -> None:
    showtime = create_showtime(client, admin_token, setup, "2026-10-20T19:00:00+07:00").json()
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {customer_token}"}).json()
    user_id = UUID(me["id"])
    showtime_id = UUID(showtime["id"])
    session_factory = create_session_factory(settings.database_url, 1)

    with session_factory() as session:
        seat_ids = tuple(
            sorted(
                session.scalars(
                    select(SeatModel.id)
                    .where(SeatModel.room_id == UUID(setup["room"]))
                    .order_by(SeatModel.row_label, SeatModel.number)
                    .limit(2)
                )
            )
        )
        inventory_count = session.scalar(
            select(func.count())
            .select_from(ShowtimeSeatModel)
            .where(ShowtimeSeatModel.showtime_id == showtime_id)
        )

    assert inventory_count == 12
    created_at = datetime(2026, 10, 20, 11, 0, tzinfo=UTC)
    booking_id = uuid4()
    tickets = tuple(
        Ticket(
            id=uuid4(),
            booking_id=booking_id,
            seat_id=seat_id,
            unit_price=90_000,
        )
        for seat_id in seat_ids
    )
    booking = Booking(
        id=booking_id,
        user_id=user_id,
        showtime_id=showtime_id,
        status=BookingStatus.HELD,
        tickets=tickets,
        total_amount=180_000,
        created_at=created_at,
        expires_at=created_at + timedelta(minutes=5),
    )

    with SqlAlchemyUnitOfWork(session_factory) as uow:
        uow.bookings.add(booking)
        uow.commit()
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        assert uow.bookings.get(booking_id) == booking

    cancelled_at = created_at + timedelta(minutes=1)
    with session_factory.begin() as session:
        session.execute(
            update(BookingModel)
            .where(BookingModel.id == booking_id)
            .values(status=BookingStatus.CANCELLED.value, cancelled_at=cancelled_at)
        )
    with SqlAlchemyUnitOfWork(session_factory) as uow:
        cancelled = uow.bookings.get(booking_id)
    assert cancelled is not None
    assert cancelled.status is BookingStatus.CANCELLED
    assert cancelled.tickets == tickets
