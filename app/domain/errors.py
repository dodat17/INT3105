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


class RoomNameAlreadyUsedError(DomainError):
    pass


class ShowtimeOverlapError(DomainError):
    pass


class DomainValidationError(DomainError):
    pass


class SeatUnavailableError(DomainError):
    def __init__(self, seat_ids: list[str] | None = None) -> None:
        super().__init__()
        self.seat_ids = seat_ids or []


class BookingExpiredError(DomainError):
    pass


class InvalidBookingStateError(DomainError):
    pass


class ShowtimeNotBookableError(DomainError):
    pass


class HoldLimitExceededError(DomainError):
    pass
