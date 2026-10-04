from uuid import uuid4

from app.domain.auth.model import Actor, IssuedToken, Role, User, normalize_email
from app.domain.errors import (
    BusinessRuleViolation,
    EmailAlreadyUsedError,
    InvalidCredentialsError,
    NotFoundError,
)
from app.domain.ports import Clock, PasswordHasher, TokenService, UnitOfWorkFactory

MIN_PASSWORD_LENGTH = 8


class AuthService:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        hasher: PasswordHasher,
        tokens: TokenService,
        clock: Clock,
    ) -> None:
        self._uow_factory = uow_factory
        self._hasher = hasher
        self._tokens = tokens
        self._clock = clock

    def register(self, email: str, password: str, full_name: str) -> User:
        if len(password) < MIN_PASSWORD_LENGTH:
            raise BusinessRuleViolation(f"Mật khẩu phải có ít nhất {MIN_PASSWORD_LENGTH} ký tự.")
        # Hash outside the transaction so bcrypt never holds a DB connection.
        user = User(
            id=uuid4(),
            email=normalize_email(email),
            password_hash=self._hasher.hash(password),
            full_name=full_name.strip(),
            role=Role.CUSTOMER,
            created_at=self._clock.now(),
        )
        with self._uow_factory() as uow:
            if uow.users.get_by_email(user.email) is not None:
                raise EmailAlreadyUsedError
            uow.users.add(user)
            uow.commit()
        return user

    def login(self, email: str, password: str) -> IssuedToken:
        with self._uow_factory() as uow:
            user = uow.users.get_by_email(normalize_email(email))
        if user is None:
            # Spend the same bcrypt time as a real check so timing does not reveal the account.
            self._hasher.hash(password)
            raise InvalidCredentialsError
        if not self._hasher.verify(password, user.password_hash):
            raise InvalidCredentialsError
        return self._tokens.issue(user.id, user.role)

    def current_user(self, actor: Actor) -> User:
        with self._uow_factory() as uow:
            user = uow.users.get(actor.user_id)
        if user is None:
            raise NotFoundError
        return user
