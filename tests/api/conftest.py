import os
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app.bootstrap.application import create_app
from app.bootstrap.settings import Settings
from app.domain.auth.model import Role, User
from app.infrastructure.persistence.models import Base
from app.infrastructure.persistence.uow import SqlAlchemyUnitOfWork, create_session_factory
from app.infrastructure.security.passwords import BcryptPasswordHasher

ROOT = Path(__file__).resolve().parents[2]
JWT_SECRET = "test-only-secret-with-at-least-32-bytes!"
ADMIN_EMAIL = "admin@example.test"
PASSWORD = "secret123"


@pytest.fixture(scope="session")
def database_url(tmp_path_factory: pytest.TempPathFactory) -> str:
    # TEST_DATABASE_URL (PostgreSQL in CI) is wiped between tests; never point it at real data.
    url = os.environ.get("TEST_DATABASE_URL") or (
        f"sqlite:///{tmp_path_factory.mktemp('db') / 'test.db'}"
    )
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.upgrade(config, "head")
    return url


@pytest.fixture
def settings(database_url: str) -> Settings:
    return Settings(
        app_env="test", database_url=database_url, jwt_secret=JWT_SECRET, bcrypt_rounds=4
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    with TestClient(create_app(settings)) as test_client:
        yield test_client
    engine = create_engine(settings.database_url)
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
    engine.dispose()


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login(client: TestClient, email: str, password: str = PASSWORD) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return str(response.json()["accessToken"])


@pytest.fixture
def customer_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "customer@example.test", "password": PASSWORD, "fullName": "Khách"},
    )
    assert response.status_code == 201, response.text
    return login(client, "customer@example.test")


@pytest.fixture
def admin_token(client: TestClient, settings: Settings) -> str:
    # ADMIN accounts only come from seeding; there is no API that grants the role.
    with SqlAlchemyUnitOfWork(create_session_factory(settings.database_url, 1)) as uow:
        uow.users.add(
            User(
                id=uuid4(),
                email=ADMIN_EMAIL,
                password_hash=BcryptPasswordHasher(4).hash(PASSWORD),
                full_name="Quản trị viên",
                role=Role.ADMIN,
                created_at=datetime.now(UTC),
            )
        )
        uow.commit()
    return login(client, ADMIN_EMAIL)


def create_room(client: TestClient, token: str, **overrides: Any) -> Any:
    body = {"name": "Phòng 1", "rows": 5, "cols": 8, "vipRows": [4, 5]}
    return client.post("/api/v1/rooms", json={**body, **overrides}, headers=auth_header(token))


def create_showtime(
    client: TestClient, token: str, setup: dict[str, str], starts_at: str, **overrides: Any
) -> Any:
    body = {
        "movieId": setup["movie"],
        "roomId": setup["room"],
        "startsAt": starts_at,
        "basePrice": 90000,
    }
    return client.post("/api/v1/showtimes", json={**body, **overrides}, headers=auth_header(token))


@pytest.fixture
def setup(client: TestClient, admin_token: str) -> dict[str, str]:
    """One 120-minute movie, "Phòng 1" (3x4, row C is VIP) and a 1-seat "Phòng 2"."""
    movie = client.post(
        "/api/v1/movies",
        json={"title": "Mai", "durationMinutes": 120},
        headers=auth_header(admin_token),
    ).json()
    room = create_room(client, admin_token, rows=3, cols=4, vipRows=[3]).json()
    other = create_room(client, admin_token, name="Phòng 2", rows=1, cols=1, vipRows=[]).json()
    return {"movie": movie["id"], "room": room["id"], "other_room": other["id"]}
