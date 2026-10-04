class DomainError(Exception):
    """Base class for business errors; the API layer maps each subclass to HTTP."""


class NotFoundError(DomainError):
    pass


class ForbiddenError(DomainError):
    pass


class BusinessRuleViolation(DomainError):
    pass


class EmailAlreadyUsedError(DomainError):
    pass


class InvalidCredentialsError(DomainError):
    pass


class InvalidTokenError(DomainError):
    pass
