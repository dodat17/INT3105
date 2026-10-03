"""Seed the ADMIN account and sample movies. Development/test only; safe to re-run.

uv run alembic upgrade head
uv run python scripts/seed.py
"""

import os
from uuid import uuid4

from app.bootstrap.settings import get_settings
from app.domain.auth.model import Role, User, normalize_email
from app.domain.catalog.model import Movie
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
        uow.commit()


if __name__ == "__main__":
    main()
