"""rooms, seats and showtimes

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-05 15:20:00+07:00
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rooms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("rows", sa.Integer(), nullable=False),
        sa.Column("cols", sa.Integer(), nullable=False),
        sa.CheckConstraint("rows > 0 AND cols > 0", name="ck_rooms_size_positive"),
        sa.PrimaryKeyConstraint("id", name="pk_rooms"),
        sa.UniqueConstraint("name", name="uq_rooms_name"),
    )
    op.create_table(
        "seats",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.Column("row_label", sa.String(length=2), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("seat_type", sa.String(length=16), nullable=False),
        sa.CheckConstraint("number > 0", name="ck_seats_number_positive"),
        sa.CheckConstraint("seat_type IN ('STANDARD', 'VIP')", name="ck_seats_seat_type"),
        sa.ForeignKeyConstraint(
            ["room_id"], ["rooms.id"], name="fk_seats_room_id_rooms", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_seats"),
        sa.UniqueConstraint("room_id", "row_label", "number", name="uq_seats_position"),
    )
    op.create_table(
        "showtimes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("movie_id", sa.Uuid(), nullable=False),
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("base_price", sa.BigInteger(), nullable=False),
        sa.CheckConstraint("ends_at > starts_at", name="ck_showtimes_window"),
        sa.CheckConstraint("base_price > 0", name="ck_showtimes_base_price_positive"),
        sa.ForeignKeyConstraint(
            ["movie_id"], ["movies.id"], name="fk_showtimes_movie_id_movies", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["room_id"], ["rooms.id"], name="fk_showtimes_room_id_rooms", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_showtimes"),
    )
    op.create_index("ix_showtimes_room_id_starts_at", "showtimes", ["room_id", "starts_at"])
    op.create_index("ix_showtimes_movie_id_starts_at", "showtimes", ["movie_id", "starts_at"])
    op.create_index("ix_showtimes_starts_at_id", "showtimes", ["starts_at", "id"])


def downgrade() -> None:
    op.drop_table("showtimes")
    op.drop_table("seats")
    op.drop_table("rooms")
