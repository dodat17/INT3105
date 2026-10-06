"""Seed ADMIN, sample movies, rooms and showtimes. Development/test only; safe to re-run.

uv run alembic upgrade head
uv run python scripts/seed.py
"""

import os
from datetime import datetime, time, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.bootstrap.settings import get_settings
from app.domain.auth.model import Role, User, normalize_email
from app.domain.catalog.model import Movie
from app.domain.cinema.model import Room, generate_seats
from app.domain.scheduling.model import Showtime
from app.infrastructure.clock import SystemClock
from app.infrastructure.persistence.uow import SqlAlchemyUnitOfWork, create_session_factory
from app.infrastructure.security.passwords import BcryptPasswordHasher

SAMPLE_MOVIES = [
    ("Mai", "Tâm lý, Tình cảm", "T18", 131, "Câu chuyện về Mai, người phụ nữ làm nghề mát-xa."),
    ("Lật Mặt 7: Một Điều Ước", "Gia đình", "K", 138, "Bà Hai và năm người con."),
    ("Dune: Part Two", "Khoa học viễn tưởng", "T13", 166, "Paul Atreides cùng người Fremen."),
    ("Inside Out 2", "Hoạt hình", "P", 96, "Những cảm xúc mới trong tâm trí Riley."),
    ("Oppenheimer", "Tiểu sử, Lịch sử", "T16", 180, "Cha đẻ của bom nguyên tử."),
    ("Đất Rừng Phương Nam", "Phiêu lưu", "T13", 110, "Hành trình tìm cha của bé An."),
]


# name, rows, cols, VIP rows (1 = A)
SAMPLE_ROOMS = [("Phòng 1", 8, 12, {6, 7}), ("Phòng 2", 6, 10, {5})]
# Four slots a day, 4 hours apart: longer than any sample movie, so no overlap (BR-04).
SLOTS = [time(9, 0), time(13, 0), time(17, 0), time(21, 0)]
DAYS = 3


def sample_showtimes(movies: list[Movie], rooms: list[Room], tz: ZoneInfo) -> list[Showtime]:
    """Showtimes from tomorrow (cinema-local) on, so a fresh seed never has past ones."""
    assert all(m.duration_minutes < 240 for m in movies), "a movie would overrun the next slot"
    tomorrow = datetime.now(tz).date() + timedelta(days=1)
    showtimes = []
    for day in range(DAYS):
        for r, room in enumerate(rooms):
            for k, slot in enumerate(SLOTS):
                movie = movies[(day * 5 + r * 3 + k) % len(movies)]
                starts_at = datetime.combine(tomorrow + timedelta(days=day), slot, tzinfo=tz)
                showtimes.append(
                    Showtime(
                        id=uuid4(),
                        movie_id=movie.id,
                        room_id=room.id,
                        starts_at=starts_at,
                        ends_at=starts_at + timedelta(minutes=movie.duration_minutes),
                        base_price=90_000 if slot >= time(17, 0) else 75_000,
                    )
                )
    return showtimes


def main() -> None:
    settings = get_settings()
    if settings.app_env == "production":
        raise SystemExit("Seed chỉ dùng cho development/test, không chạy trên production.")

    admin_email = normalize_email(os.environ.get("SEED_ADMIN_EMAIL", "admin@example.test"))
    admin_password = os.environ.get("SEED_ADMIN_PASSWORD", "admin12345")
    session_factory = create_session_factory(settings.database_url, settings.db_pool_size)

    with SqlAlchemyUnitOfWork(session_factory) as uow:
        if uow.users.get_by_email(admin_email) is None:
            uow.users.add(
                User(
                    id=uuid4(),
                    email=admin_email,
                    password_hash=BcryptPasswordHasher(settings.bcrypt_rounds).hash(admin_password),
                    full_name="Quản trị viên",
                    role=Role.ADMIN,
                    created_at=SystemClock().now(),
                )
            )
            print(f"Đã tạo ADMIN {admin_email}")
        if uow.movies.search(None, 1, 1).total_items == 0:
            for title, genre, age_rating, duration, description in SAMPLE_MOVIES:
                uow.movies.add(
                    Movie(
                        id=uuid4(),
                        title=title,
                        description=description,
                        duration_minutes=duration,
                        genre=genre,
                        age_rating=age_rating,
                    )
                )
            print(f"Đã tạo {len(SAMPLE_MOVIES)} phim mẫu")
        if not uow.rooms.list_all():
            for name, rows, cols, vip_rows in SAMPLE_ROOMS:
                room = Room(id=uuid4(), name=name, rows=rows, cols=cols)
                uow.rooms.add(room, generate_seats(room.id, rows, cols, vip_rows))
            print(f"Đã tạo {len(SAMPLE_ROOMS)} phòng chiếu kèm ghế")
        if uow.showtimes.search(None, None, None, 1, 1).total_items == 0:
            movies = uow.movies.search(None, 1, 100).items
            rooms = uow.rooms.list_all()
            showtimes = sample_showtimes(movies, rooms, ZoneInfo(settings.cinema_timezone))
            for showtime in showtimes:
                uow.showtimes.add(showtime)
            print(f"Đã tạo {len(showtimes)} suất chiếu mẫu")
        uow.commit()


if __name__ == "__main__":
    main()
