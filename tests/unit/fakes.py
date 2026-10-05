from datetime import UTC, datetime
from typing import Any, Self
from uuid import UUID

from app.domain.auth.model import IssuedToken, Role, User
from app.domain.catalog.model import Movie
from app.domain.cinema.model import Room, Seat
from app.domain.errors import EmailAlreadyUsedError
from app.domain.ports import Page
from app.domain.scheduling.model import Showtime, overlaps

NOW = datetime(2026, 10, 15, 3, 0, tzinfo=UTC)


class InMemoryUsers:
    def __init__(self) -> None:
        self.rows: dict[UUID, User] = {}

    def get(self, user_id: UUID) -> User | None:
        return self.rows.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.rows.values() if u.email == email), None)

    def add(self, user: User) -> None:
        if self.get_by_email(user.email):
            raise EmailAlreadyUsedError
        self.rows[user.id] = user


class InMemoryMovies:
    def __init__(self) -> None:
        self.rows: dict[UUID, Movie] = {}

    def get(self, movie_id: UUID) -> Movie | None:
        return self.rows.get(movie_id)

    def search(self, query: str | None, page: int, page_size: int) -> Page[Movie]:
        self.last_query = query
        found = [m for m in self.rows.values() if not query or query.lower() in m.title.lower()]
        start = (page - 1) * page_size
        return Page(found[start : start + page_size], page, page_size, len(found))

    def add(self, movie: Movie) -> None:
        self.rows[movie.id] = movie

    def delete(self, movie_id: UUID) -> None:
        del self.rows[movie_id]


class InMemoryRooms:
    def __init__(self) -> None:
        self.rows: dict[UUID, Room] = {}
        self.seat_rows: dict[UUID, list[Seat]] = {}

    def get(self, room_id: UUID) -> Room | None:
        return self.rows.get(room_id)

    def get_by_name(self, name: str) -> Room | None:
        return next((r for r in self.rows.values() if r.name == name), None)

    def list_all(self) -> list[Room]:
        return sorted(self.rows.values(), key=lambda r: r.name)

    def lock(self, room_id: UUID) -> Room | None:
        return self.get(room_id)

    def add(self, room: Room, seats: list[Seat]) -> None:
        self.rows[room.id] = room
        self.seat_rows[room.id] = seats

    def seats(self, room_id: UUID) -> list[Seat]:
        return sorted(self.seat_rows.get(room_id, []), key=lambda s: (s.row_label, s.number))


class InMemoryShowtimes:
    def __init__(self) -> None:
        self.rows: dict[UUID, Showtime] = {}

    def get(self, showtime_id: UUID) -> Showtime | None:
        return self.rows.get(showtime_id)

    def search(
        self,
        movie_id: UUID | None,
        starts_from: datetime | None,
        starts_before: datetime | None,
        page: int,
        page_size: int,
    ) -> Page[Showtime]:
        self.last_search = (movie_id, starts_from, starts_before)
        found = sorted(
            (
                s
                for s in self.rows.values()
                if (movie_id is None or s.movie_id == movie_id)
                and (starts_from is None or s.starts_at >= starts_from)
                and (starts_before is None or s.starts_at < starts_before)
            ),
            key=lambda s: (s.starts_at, s.id),
        )
        start = (page - 1) * page_size
        return Page(found[start : start + page_size], page, page_size, len(found))

    def find_overlapping(
        self, room_id: UUID, starts_at: datetime, ends_at: datetime
    ) -> list[Showtime]:
        return [
            s
            for s in self.rows.values()
            if s.room_id == room_id and overlaps(s.starts_at, s.ends_at, starts_at, ends_at)
        ]

    def exists_for_movie(self, movie_id: UUID) -> bool:
        return any(s.movie_id == movie_id for s in self.rows.values())

    def add(self, showtime: Showtime) -> None:
        self.rows[showtime.id] = showtime

    def delete(self, showtime_id: UUID) -> None:
        del self.rows[showtime_id]


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.users = InMemoryUsers()
        self.movies = InMemoryMovies()
        self.rooms = InMemoryRooms()
        self.showtimes = InMemoryShowtimes()
        self.commits = 0

    def __call__(self) -> Self:
        return self

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: Any) -> None:
        pass

    def commit(self) -> None:
        self.commits += 1


class FakeHasher:
    def __init__(self) -> None:
        self.hash_calls = 0

    def hash(self, password: str) -> str:
        self.hash_calls += 1
        return f"hashed:{password}"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hashed:{password}"


class FakeTokens:
    def issue(self, user_id: UUID, role: Role) -> IssuedToken:
        return IssuedToken(access_token=f"token:{user_id}:{role}", expires_in=60)

    def decode(self, token: str) -> Any:
        raise NotImplementedError


class FixedClock:
    def now(self) -> datetime:
        return NOW
