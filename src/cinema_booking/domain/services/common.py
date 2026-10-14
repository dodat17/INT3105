from cinema_booking.domain.entities import User
from cinema_booking.domain.enums import UserRole
from cinema_booking.domain.errors import Forbidden


def require_admin(actor: User) -> None:
    if actor.role is not UserRole.ADMIN:
        raise Forbidden("Administrator access is required")
