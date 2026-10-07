"""bookings, tickets and showtime seat inventory

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-07 00:00:00+07:00
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bookings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("showtime_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("total_amount", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("booking_code", sa.String(length=16), nullable=True),
        sa.CheckConstraint(
            "status IN ('HELD', 'CONFIRMED', 'CANCELLED', 'EXPIRED')",
            name="ck_bookings_status",
        ),
        sa.CheckConstraint("total_amount >= 0", name="ck_bookings_total_amount_non_negative"),
        sa.CheckConstraint(
            "(status = 'CONFIRMED' AND confirmed_at IS NOT NULL AND booking_code IS NOT NULL) "
            "OR (status <> 'CONFIRMED' AND confirmed_at IS NULL AND booking_code IS NULL)",
            name="ck_bookings_confirmed_fields",
        ),
        sa.CheckConstraint(
            "(status = 'CANCELLED' AND cancelled_at IS NOT NULL) "
            "OR (status <> 'CANCELLED' AND cancelled_at IS NULL)",
            name="ck_bookings_cancelled_fields",
        ),
        sa.ForeignKeyConstraint(
            ["showtime_id"],
            ["showtimes.id"],
            name="fk_bookings_showtime_id_showtimes",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_bookings_user_id_users", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_bookings"),
        sa.UniqueConstraint("booking_code", name="uq_bookings_booking_code"),
    )
    op.create_index(
        "ix_bookings_user_id_created_at_id", "bookings", ["user_id", "created_at", "id"]
    )
    op.create_index(
        "ix_bookings_user_id_status_expires_at",
        "bookings",
        ["user_id", "status", "expires_at"],
    )
    op.create_index(
        "ix_bookings_showtime_id_user_id_status",
        "bookings",
        ["showtime_id", "user_id", "status"],
    )

    op.create_table(
        "tickets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("booking_id", sa.Uuid(), nullable=False),
        sa.Column("seat_id", sa.Uuid(), nullable=False),
        sa.Column("unit_price", sa.BigInteger(), nullable=False),
        sa.CheckConstraint("unit_price >= 0", name="ck_tickets_unit_price_non_negative"),
        sa.ForeignKeyConstraint(
            ["booking_id"],
            ["bookings.id"],
            name="fk_tickets_booking_id_bookings",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["seat_id"], ["seats.id"], name="fk_tickets_seat_id_seats", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tickets"),
        sa.UniqueConstraint("booking_id", "seat_id", name="uq_tickets_booking_seat"),
    )

    op.create_table(
        "showtime_seats",
        sa.Column("showtime_id", sa.Uuid(), nullable=False),
        sa.Column("seat_id", sa.Uuid(), nullable=False),
        sa.Column("state", sa.String(length=12), nullable=False, server_default="AVAILABLE"),
        sa.Column("booking_id", sa.Uuid(), nullable=True),
        sa.Column("hold_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "(state = 'AVAILABLE' AND booking_id IS NULL AND hold_expires_at IS NULL) "
            "OR (state = 'HELD' AND booking_id IS NOT NULL AND hold_expires_at IS NOT NULL) "
            "OR (state = 'BOOKED' AND booking_id IS NOT NULL AND hold_expires_at IS NULL)",
            name="ck_showtime_seats_state_fields",
        ),
        sa.ForeignKeyConstraint(
            ["booking_id"],
            ["bookings.id"],
            name="fk_showtime_seats_booking_id_bookings",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["seat_id"], ["seats.id"], name="fk_showtime_seats_seat_id_seats", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["showtime_id"],
            ["showtimes.id"],
            name="fk_showtime_seats_showtime_id_showtimes",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("showtime_id", "seat_id", name="pk_showtime_seats"),
    )
    op.create_index("ix_showtime_seats_booking_id", "showtime_seats", ["booking_id"])
    op.execute(
        sa.text(
            "INSERT INTO showtime_seats (showtime_id, seat_id, state) "
            "SELECT showtimes.id, seats.id, 'AVAILABLE' FROM showtimes "
            "JOIN seats ON seats.room_id = showtimes.room_id"
        )
    )


def downgrade() -> None:
    op.drop_index("ix_showtime_seats_booking_id", table_name="showtime_seats")
    op.drop_table("showtime_seats")
    op.drop_table("tickets")
    op.drop_index("ix_bookings_showtime_id_user_id_status", table_name="bookings")
    op.drop_index("ix_bookings_user_id_status_expires_at", table_name="bookings")
    op.drop_index("ix_bookings_user_id_created_at_id", table_name="bookings")
    op.drop_table("bookings")
