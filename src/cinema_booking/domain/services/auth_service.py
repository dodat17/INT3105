from uuid import uuid4

from cinema_booking.domain.entities import User
from cinema_booking.domain.enums import UserRole
from cinema_booking.domain.errors import (
    BusinessRuleViolation,
    EmailAlreadyUsed,
    InvalidCredentials,
    NotFound,
)
from cinema_booking.domain.ports import Clock, PasswordHasher, TokenService, UnitOfWork


class AuthService:
    def __init__(
        self,
        uow: UnitOfWork,
        hasher: PasswordHasher,
        tokens: TokenService,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._hasher = hasher
        self._tokens = tokens
        self._clock = clock

    def register(self, email: str, password: str, full_name: str) -> User:
        normalized_email = email.strip().lower()
        if len(password) < 8:
            raise BusinessRuleViolation("Password must contain at least 8 characters")
        if not full_name.strip():
            raise BusinessRuleViolation("Full name must not be empty")
        with self._uow as uow:
            if uow.users.get_by_email(normalized_email):
                raise EmailAlreadyUsed("Email is already registered", {"email": normalized_email})
            user = User(
                id=str(uuid4()),
                email=normalized_email,
                password_hash=self._hasher.hash(password),
                full_name=full_name.strip(),
                role=UserRole.CUSTOMER,
                created_at=self._clock.now(),
            )
            uow.users.add(user)
            uow.commit()
            return user

    def login(self, email: str, password: str) -> tuple[str, int]:
        with self._uow as uow:
            user = uow.users.get_by_email(email.strip().lower())
            if user is None or not self._hasher.verify(password, user.password_hash):
                raise InvalidCredentials("Email or password is incorrect")
            return self._tokens.issue(user)

    def get_user(self, user_id: str) -> User:
        with self._uow as uow:
            user = uow.users.get(user_id)
            if user is None:
                raise NotFound("User not found", {"user_id": user_id})
            return user
