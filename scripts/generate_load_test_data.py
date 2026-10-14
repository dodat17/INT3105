import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

from cinema_booking.api.config import Settings
from cinema_booking.domain.entities import User
from cinema_booking.domain.enums import UserRole
from cinema_booking.infrastructure.database.models import (
    MovieModel,
    RoomModel,
    ShowtimeModel,
    UserModel,
)
from cinema_booking.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
    create_tables,
)
from cinema_booking.infrastructure.security.jwt_service import JwtTokenService
from cinema_booking.infrastructure.security.password_hasher import BcryptPasswordHasher


def main() -> None:
    settings = Settings()
    count = int(os.environ.get("LOAD_TEST_USER_COUNT", "2000"))
    password = os.environ.get("LOAD_TEST_PASSWORD", "load-test-password")
    output = Path(os.environ.get("LOAD_TEST_TOKEN_FILE", "load_tests/tokens.json"))
    engine = create_database_engine(settings.database_url, settings.db_pool_size)
    create_tables(engine)
    factory = create_session_factory(engine)
    password_hash = BcryptPasswordHasher(settings.bcrypt_rounds).hash(password)
    token_service = JwtTokenService(settings.jwt_secret, settings.jwt_expires_minutes)
    tokens: list[dict[str, str]] = []
    with factory() as session:
        for index in range(count):
            email = f"load{index:04d}@example.com"
            model = session.scalar(select(UserModel).where(UserModel.email == email))
            if model is None:
                model = UserModel(
                    id=str(uuid4()),
                    email=email,
                    password_hash=password_hash,
                    full_name=f"Load User {index}",
                    role=UserRole.CUSTOMER,
                    created_at=datetime.now(timezone.utc),
                )
                session.add(model)
                session.flush()
            user = User(
                model.id,
                model.email,
                model.password_hash,
                model.full_name,
                model.role,
                model.created_at,
            )
            token, _ = token_service.issue(user)
            tokens.append({"email": email, "password": password, "token": token})
        showtime_ids = list(session.scalars(select(ShowtimeModel.id).limit(50)))
        if len(showtime_ids) < 50:
            movie = session.scalar(select(MovieModel).limit(1))
            room = session.scalar(select(RoomModel).limit(1))
            if movie is None or room is None:
                raise RuntimeError("Run scripts/seed.py before generating load-test data")
            first_start = (datetime.now(timezone.utc) + timedelta(days=2)).replace(
                hour=19, minute=0, second=0, microsecond=0
            )
            for index in range(len(showtime_ids), 50):
                starts_at = first_start + timedelta(days=index)
                showtime = ShowtimeModel(
                    id=str(uuid4()),
                    movie_id=movie.id,
                    room_id=room.id,
                    starts_at=starts_at,
                    ends_at=starts_at + timedelta(minutes=movie.duration_minutes),
                    base_price=100_000,
                )
                session.add(showtime)
                showtime_ids.append(showtime.id)
        session.commit()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps({"users": tokens, "showtime_ids": showtime_ids}, indent=2), encoding="utf-8"
    )
    engine.dispose()
    print(f"Wrote {len(tokens)} users to {output}")


if __name__ == "__main__":
    main()
