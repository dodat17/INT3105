from dataclasses import replace
from uuid import UUID, uuid4

from app.domain.auth.model import (
    Actor,
    IssuedToken,
    Role,
    User,
    normalize_email,
    require_admin,
)
from app.domain.errors import (
    BusinessRuleViolation,
    EmailAlreadyUsedError,
    InvalidCredentialsError,
    NotFoundError,
)
from app.domain.ports import Clock, Page, PasswordHasher, TokenService, UnitOfWorkFactory

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

    def list_users(
        self, actor: Actor, query: str | None, role: Role | None, page: int, page_size: int
    ) -> Page[User]:
        require_admin(actor)
        with self._uow_factory() as uow:
            return uow.users.search((query or "").strip() or None, role, page, page_size)

    def get_user(self, actor: Actor, user_id: UUID) -> User:
        require_admin(actor)
        with self._uow_factory() as uow:
            user = uow.users.get(user_id)
        if user is None:
            raise NotFoundError
        return user

    def update_user(self, actor: Actor, user_id: UUID, *, full_name: str, role: Role) -> User:
        require_admin(actor)
        # An admin demoting themselves could leave the system without any admin.
        if user_id == actor.user_id and role is not actor.role:
            raise BusinessRuleViolation("Không thể tự đổi vai trò của chính mình.")
        with self._uow_factory() as uow:
            current = uow.users.lock(user_id)
            if current is None:
                raise NotFoundError
            # ponytail: role lives in the JWT, so a change applies from the next login;
            # add token revocation if instant demotion is required.
            user = replace(current, full_name=full_name.strip(), role=role)
            uow.users.update(user)
            uow.commit()
        return user

    def delete_user(self, actor: Actor, user_id: UUID) -> None:
        require_admin(actor)
        if user_id == actor.user_id:
            raise BusinessRuleViolation("Không thể tự xóa tài khoản của chính mình.")
        with self._uow_factory() as uow:
            if uow.users.lock(user_id) is None:
                raise NotFoundError
            # Bookings are history (BR-12): a user who has booked is kept.
            if uow.bookings.exists_for_user(user_id):
                raise BusinessRuleViolation("Không thể xóa người dùng đã có booking.")
            uow.users.delete(user_id)
            uow.commit()
