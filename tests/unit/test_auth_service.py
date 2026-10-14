import pytest

from cinema_booking.domain.errors import BusinessRuleViolation, EmailAlreadyUsed, InvalidCredentials
from cinema_booking.domain.services.auth_service import AuthService
from tests.unit.fakes import FakeClock, FakeHasher, FakeTokenService, FakeUnitOfWork


def test_register_login_and_duplicate_email(uow: FakeUnitOfWork, clock: FakeClock) -> None:
    service = AuthService(uow, FakeHasher(), FakeTokenService(), clock)
    user = service.register("USER@example.com", "password", "Test User")

    token, expires_in = service.login("user@example.com", "password")

    assert user.email == "user@example.com"
    assert token.startswith("token:")
    assert expires_in == 3600
    with pytest.raises(EmailAlreadyUsed):
        service.register("user@example.com", "password", "Other")


def test_password_rules_and_invalid_credentials(uow: FakeUnitOfWork, clock: FakeClock) -> None:
    service = AuthService(uow, FakeHasher(), FakeTokenService(), clock)

    with pytest.raises(BusinessRuleViolation):
        service.register("user@example.com", "short", "Test User")
    with pytest.raises(InvalidCredentials):
        service.login("missing@example.com", "password")
