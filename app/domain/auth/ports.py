from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from app.domain.auth.model import Actor, IssuedToken, Role, User
from app.domain.ports import UnitOfWork


class UserRepository(Protocol):
    def get(self, user_id: UUID) -> User | None: ...
    def get_by_email(self, email: str) -> User | None: ...
    def add(self, user: User) -> None: ...


class AuthUnitOfWork(UnitOfWork, Protocol):
    @property
    def users(self) -> UserRepository: ...


AuthUnitOfWorkFactory = Callable[[], AuthUnitOfWork]


class PasswordHasher(Protocol):
    def hash(self, password: str) -> str: ...
    def verify(self, password: str, password_hash: str) -> bool: ...


class TokenService(Protocol):
    def issue(self, user_id: UUID, role: Role) -> IssuedToken: ...
    def decode(self, token: str) -> Actor: ...
