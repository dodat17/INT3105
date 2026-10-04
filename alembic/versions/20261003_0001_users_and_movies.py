"""users and movies

Revision ID: 0001
Revises:
Create Date: 2026-10-03 14:10:00+07:00
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=100), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('CUSTOMER', 'ADMIN')", name="ck_users_role"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "movies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("genre", sa.String(length=100), nullable=False),
        sa.Column("age_rating", sa.String(length=10), nullable=False),
        sa.CheckConstraint("duration_minutes > 0", name="ck_movies_duration_positive"),
        sa.PrimaryKeyConstraint("id", name="pk_movies"),
    )
    op.create_index("ix_movies_title", "movies", ["title"])


def downgrade() -> None:
    op.drop_index("ix_movies_title", table_name="movies")
    op.drop_table("movies")
    op.drop_table("users")
