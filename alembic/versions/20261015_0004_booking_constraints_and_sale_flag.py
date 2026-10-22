"""booking integrity constraints and showtime sale flag

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("showtimes") as batch:
        batch.add_column(
            sa.Column(
                "is_open_for_booking",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )

    with op.batch_alter_table("bookings") as batch:
        batch.drop_constraint(op.f("ck_bookings_ck_bookings_status"), type_="check")
        batch.create_check_constraint(
            op.f("ck_bookings_status"),
            "status IN ('HELD', 'CONFIRMED', 'CANCELLED', 'EXPIRED')",
        )
        batch.create_check_constraint(
            op.f("ck_bookings_confirmed"),
            "(status = 'CONFIRMED' AND confirmed_at IS NOT NULL AND booking_code IS NOT NULL) "
            "OR (status <> 'CONFIRMED' AND confirmed_at IS NULL AND booking_code IS NULL)",
        )
        batch.create_check_constraint(
            op.f("ck_bookings_cancelled"),
            "(status = 'CANCELLED') = (cancelled_at IS NOT NULL)",
        )

    with op.batch_alter_table("showtime_seats") as batch:
        batch.drop_constraint(op.f("ck_showtime_seats_ck_showtime_seats_state"), type_="check")
        batch.create_check_constraint(
            op.f("ck_showtime_seats_state"),
            "(state = 'AVAILABLE' AND booking_id IS NULL AND hold_expires_at IS NULL) OR "
            "(state = 'HELD' AND booking_id IS NOT NULL AND hold_expires_at IS NOT NULL) OR "
            "(state = 'BOOKED' AND booking_id IS NOT NULL AND hold_expires_at IS NULL)",
        )


def downgrade() -> None:
    with op.batch_alter_table("showtime_seats") as batch:
        batch.drop_constraint(op.f("ck_showtime_seats_state"), type_="check")
        batch.create_check_constraint(
            op.f("ck_showtime_seats_ck_showtime_seats_state"),
            "state IN ('AVAILABLE', 'HELD', 'BOOKED')",
        )

    with op.batch_alter_table("bookings") as batch:
        batch.drop_constraint(op.f("ck_bookings_cancelled"), type_="check")
        batch.drop_constraint(op.f("ck_bookings_confirmed"), type_="check")
        batch.drop_constraint(op.f("ck_bookings_status"), type_="check")
        batch.create_check_constraint(
            op.f("ck_bookings_ck_bookings_status"),
            "status IN ('HELD', 'CONFIRMED', 'CANCELLED')",
        )

    with op.batch_alter_table("showtimes") as batch:
        batch.drop_column("is_open_for_booking")
