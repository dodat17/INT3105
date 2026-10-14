from datetime import datetime, timedelta, timezone

import jwt

from cinema_booking.domain.entities import User


class JwtTokenService:
    def __init__(self, secret: str, expires_minutes: int = 60) -> None:
        self._secret = secret
        self._expires_minutes = expires_minutes

    def issue(self, user: User) -> tuple[str, int]:
        expires_seconds = self._expires_minutes * 60
        payload = {
            "sub": user.id,
            "role": user.role.value,
            "exp": datetime.now(timezone.utc) + timedelta(seconds=expires_seconds),
        }
        return jwt.encode(payload, self._secret, algorithm="HS256"), expires_seconds

    def decode(self, token: str) -> dict[str, str]:
        return jwt.decode(token, self._secret, algorithms=["HS256"])
