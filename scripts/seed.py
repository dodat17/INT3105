import os
from datetime import datetime, timedelta, timezone

from cinema_booking.api.config import Settings
from cinema_booking.domain.entities import User
from cinema_booking.domain.enums import UserRole
from cinema_booking.domain.services.movie_service import MovieService
from cinema_booking.domain.services.room_service import RoomService
from cinema_booking.domain.services.showtime_service import ShowtimeService
from cinema_booking.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
    create_tables,
)
from cinema_booking.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from cinema_booking.infrastructure.security.password_hasher import BcryptPasswordHasher


def main() -> None:
    settings = Settings()
    password = os.environ.get("SEED_ADMIN_PASSWORD")
    if not password:
        raise RuntimeError("SEED_ADMIN_PASSWORD must be set")
    engine = create_database_engine(settings.database_url, settings.db_pool_size)
    create_tables(engine)
    factory = create_session_factory(engine)
    hasher = BcryptPasswordHasher(settings.bcrypt_rounds)

    with SqlAlchemyUnitOfWork(factory) as uow:
        admin = uow.users.get_by_email("admin@example.com")
        if admin is None:
            admin = User(
                id="00000000-0000-0000-0000-000000000001",
                email="admin@example.com",
                password_hash=hasher.hash(password),
                full_name="Cinema Admin",
                role=UserRole.ADMIN,
                created_at=datetime.now(timezone.utc),
            )
            uow.users.add(admin)
            uow.commit()

    movies = MovieService(SqlAlchemyUnitOfWork(factory))
    rooms = RoomService(SqlAlchemyUnitOfWork(factory))
    showtimes = ShowtimeService(SqlAlchemyUnitOfWork(factory))
    existing_movies = movies.list(search="The Sample Movie", limit=1)
    movie = existing_movies[0] if existing_movies else movies.create(
        admin, "The Sample Movie", 120, "Drama", "P", "Seed data"
    )
    existing_rooms = rooms.list(admin)
    room = next((item for item in existing_rooms if item.name == "Room 1"), None)
    if room is None:
        room, _ = rooms.create(admin, "Room 1", 8, 10, [7, 8])
    existing_showtimes = showtimes.list(movie.id)
    if not existing_showtimes:
        starts_at = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
            hour=19, minute=0, second=0, microsecond=0
        )
        showtimes.create(admin, movie.id, room.id, starts_at, 100_000)
    engine.dispose()
    print("Seed complete. Admin email: admin@example.com")


if __name__ == "__main__":
    main()
