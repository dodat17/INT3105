from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from cinema_booking.api.app import create_app
from cinema_booking.api.config import Settings
from cinema_booking.domain.enums import UserRole
from cinema_booking.infrastructure.database.models import UserModel


@pytest.fixture
def client(tmp_path) -> TestClient:
    database_path = tmp_path / "api.db"
    app = create_app(
        Settings(
            database_url=f"sqlite:///{database_path.as_posix()}",
            jwt_secret="test-secret-that-is-at-least-32-bytes-long",
            bcrypt_rounds=4,
        )
    )
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_token(client: TestClient) -> str:
    container = client.app.state.container
    admin = UserModel(
        id="admin-id",
        email="admin@example.com",
        password_hash=container.hasher.hash("admin-password"),
        full_name="Admin",
        role=UserRole.ADMIN,
        created_at=datetime.now(timezone.utc),
    )
    with container.session_factory() as session:
        session.add(admin)
        session.commit()
    response = client.post(
        "/auth/login", json={"email": "admin@example.com", "password": "admin-password"}
    )
    return response.json()["access_token"]


@pytest.fixture
def customer_token(client: TestClient) -> str:
    client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password", "full_name": "User"},
    )
    response = client.post(
        "/auth/login", json={"email": "user@example.com", "password": "password"}
    )
    return response.json()["access_token"]


@pytest.fixture
def catalog(client: TestClient, admin_token: str) -> dict[str, object]:
    headers = {"Authorization": f"Bearer {admin_token}"}
    movie = client.post(
        "/movies",
        headers=headers,
        json={
            "title": "API Movie",
            "duration_minutes": 120,
            "genre": "Drama",
            "age_rating": "P",
            "description": "Test",
        },
    ).json()
    room = client.post(
        "/rooms",
        headers=headers,
        json={"name": "API Room", "rows": 2, "cols": 3, "vip_rows": [2]},
    ).json()
    starts_at = datetime.now(timezone.utc).replace(microsecond=0)
    starts_at = starts_at.replace(year=starts_at.year + 1)
    showtime = client.post(
        "/showtimes",
        headers=headers,
        json={
            "movie_id": movie["id"],
            "room_id": room["id"],
            "starts_at": starts_at.isoformat(),
            "base_price": 100000,
        },
    ).json()
    seats = client.get(f"/showtimes/{showtime['id']}/seats").json()["seats"]
    return {"movie": movie, "room": room, "showtime": showtime, "seats": seats}
