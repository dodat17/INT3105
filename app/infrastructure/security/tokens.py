from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.domain.auth.model import Actor, IssuedToken, Role
from app.domain.errors import InvalidTokenError

_CLOCK_SKEW_SECONDS = 60


class JwtTokenService:
    """HS256 JWT with claims sub, role, iat, exp. The algorithm is pinned server-side."""

    def __init__(self, secret: str, algorithm: str, ttl_seconds: int) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._ttl_seconds = ttl_seconds

    def issue(self, user_id: UUID, role: Role) -> IssuedToken:
        now = datetime.now(UTC)
        claims = {
            "sub": str(user_id),
            "role": role.value,
            "iat": now,
            "exp": now + timedelta(seconds=self._ttl_seconds),
        }
        token = jwt.encode(claims, self._secret, algorithm=self._algorithm)
        return IssuedToken(access_token=token, expires_in=self._ttl_seconds)

    def decode(self, token: str) -> Actor:
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
                leeway=_CLOCK_SKEW_SECONDS,
                options={"require": ["sub", "role", "iat", "exp"]},
            )
            return Actor(user_id=UUID(claims["sub"]), role=Role(claims["role"]))
        except (jwt.InvalidTokenError, ValueError, TypeError) as exc:
            raise InvalidTokenError from exc
