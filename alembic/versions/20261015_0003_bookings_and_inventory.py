"""bookings and per-showtime seat inventory

Revision ID: 0003
Revises: 0002
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
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_amount", sa.BigInteger(), nullable=False),
        sa.Column("booking_code", sa.String(16), nullable=True),
        sa.CheckConstraint("status IN ('HELD', 'CONFIRMED', 'CANCELLED')", name="ck_bookings_status"),
        sa.CheckConstraint("total_amount >= 0", name="ck_bookings_total_non_negative"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["showtime_id"], ["showtimes.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_code"),
    )
    op.create_index("ix_bookings_user_id", "bookings", ["user_id"])
    op.create_index("ix_bookings_showtime_id", "bookings", ["showtime_id"])
    op.create_index("ix_bookings_status", "bookings", ["status"])
    op.create_index("ix_bookings_expires_at", "bookings", ["expires_at"])
    op.create_table(
        "booking_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("booking_id", sa.Uuid(), nullable=False),
        sa.Column("seat_id", sa.Uuid(), nullable=False),
        sa.Column("row_label", sa.String(2), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("seat_type", sa.String(16), nullable=False),
        sa.Column("unit_price", sa.BigInteger(), nullable=False),
        sa.CheckConstraint("unit_price >= 0", name="ck_booking_items_unit_price_non_negative"),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["seat_id"], ["seats.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_id", "seat_id", name="uq_booking_items_booking_seat"),
    )
    op.create_index("ix_booking_items_booking_id", "booking_items", ["booking_id"])
    op.create_table(
        "showtime_seats",
        sa.Column("showtime_id", sa.Uuid(), nullable=False),
        sa.Column("seat_id", sa.Uuid(), nullable=False),
        sa.Column("state", sa.String(12), nullable=False, server_default="AVAILABLE"),
        sa.Column("booking_id", sa.Uuid(), nullable=True),
        sa.Column("hold_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("state IN ('AVAILABLE', 'HELD', 'BOOKED')", name="ck_showtime_seats_state"),
        sa.ForeignKeyConstraint(["showtime_id"], ["showtimes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["seat_id"], ["seats.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("showtime_id", "seat_id"),
    )
    op.create_index("ix_showtime_seats_booking_id", "showtime_seats", ["booking_id"])
    op.execute(sa.text("""INSERT INTO showtime_seats (showtime_id, seat_id, state)
        SELECT st.id, s.id, 'AVAILABLE' FROM showtimes st JOIN seats s ON s.room_id = st.room_id"""))


def downgrade() -> None:
    op.drop_table("showtime_seats")
    op.drop_table("booking_items")
    op.drop_table("bookings")
