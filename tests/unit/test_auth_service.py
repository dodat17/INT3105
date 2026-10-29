from uuid import UUID

import pytest

from app.domain.auth.model import Actor, Role
from app.domain.auth.service import AuthService
from app.domain.errors import (
    BusinessRuleViolation,
    EmailAlreadyUsedError,
    InvalidCredentialsError,
    NotFoundError,
)
from tests.unit.fakes import NOW, FakeHasher, FakeTokens, FakeUnitOfWork, FixedClock


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


@pytest.fixture
def hasher() -> FakeHasher:
    return FakeHasher()


@pytest.fixture
def service(uow: FakeUnitOfWork, hasher: FakeHasher) -> AuthService:
    return AuthService(uow, hasher, FakeTokens(), FixedClock())


def test_register_creates_customer_with_normalized_email(
    service: AuthService, uow: FakeUnitOfWork
) -> None:
    user = service.register("  An.Nguyen@Example.TEST ", "secret123", "  Nguyễn An ")

    assert user.email == "an.nguyen@example.test"
    assert user.full_name == "Nguyễn An"
    assert user.role is Role.CUSTOMER
    assert user.password_hash == "hashed:secret123"
    assert user.created_at == NOW
    assert uow.users.get(user.id) == user
    assert uow.commits == 1


def test_register_rejects_duplicate_email_ignoring_case(service: AuthService) -> None:
    service.register("an@example.test", "secret123", "An")

    with pytest.raises(EmailAlreadyUsedError):
        service.register("AN@example.test", "another123", "An 2")


@pytest.mark.parametrize("password", ["", "1234567"])
def test_register_rejects_password_shorter_than_8(service: AuthService, password: str) -> None:
    with pytest.raises(BusinessRuleViolation):
        service.register("an@example.test", password, "An")


def test_register_accepts_password_of_exactly_8(service: AuthService) -> None:
    assert service.register("an@example.test", "12345678", "An").email == "an@example.test"


def test_login_returns_token_for_valid_credentials(service: AuthService) -> None:
    user = service.register("an@example.test", "secret123", "An")

    token = service.login(" AN@example.test", "secret123")

    assert token.access_token == f"token:{user.id}:CUSTOMER"


def test_login_rejects_wrong_password(service: AuthService) -> None:
    service.register("an@example.test", "secret123", "An")

    with pytest.raises(InvalidCredentialsError):
        service.login("an@example.test", "wrong-password")


def test_login_unknown_email_still_spends_hash_time(
    service: AuthService, hasher: FakeHasher
) -> None:
    with pytest.raises(InvalidCredentialsError):
        service.login("nobody@example.test", "secret123")

    assert hasher.hash_calls == 1


def test_current_user_of_deleted_account_is_not_found(service: AuthService) -> None:
    user = service.register("an@example.test", "secret123", "An")

    assert service.current_user(Actor(user.id, Role.CUSTOMER)) == user
    with pytest.raises(NotFoundError):
        service.current_user(Actor(UUID(int=0), Role.CUSTOMER))
