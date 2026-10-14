from typing import Any


class DomainError(Exception):
    code = "DOMAIN_ERROR"

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class BusinessRuleViolation(DomainError):
    code = "BUSINESS_RULE_VIOLATION"


class EmailAlreadyUsed(DomainError):
    code = "EMAIL_ALREADY_USED"


class Forbidden(DomainError):
    code = "FORBIDDEN"


class NotFound(DomainError):
    code = "NOT_FOUND"


class ShowtimeOverlap(DomainError):
    code = "SHOWTIME_OVERLAP"


class ShowtimeAlreadyStarted(DomainError):
    code = "SHOWTIME_ALREADY_STARTED"


class SeatUnavailable(DomainError):
    code = "SEAT_UNAVAILABLE"


class InvalidCredentials(DomainError):
    code = "INVALID_CREDENTIALS"
