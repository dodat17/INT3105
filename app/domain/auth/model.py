from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from app.domain.errors import ForbiddenError


class Role(StrEnum):
    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"


@dataclass(frozen=True)
class User:
    id: UUID
    email: str
    password_hash: str
    full_name: str
    role: Role
    created_at: datetime


@dataclass(frozen=True)
class Actor:
    """Authenticated caller, as established by the authentication middleware."""

    user_id: UUID
    role: Role


@dataclass(frozen=True)
class IssuedToken:
    access_token: str
    expires_in: int


def normalize_email(email: str) -> str:
    return email.strip().lower()


def require_admin(actor: Actor) -> None:
    """BR-03: only ADMIN manages the catalog."""
    if actor.role is not Role.ADMIN:
        raise ForbiddenError
