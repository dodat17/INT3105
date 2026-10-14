import re

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from cinema_booking.domain.entities import User
from cinema_booking.domain.enums import UserRole

PUBLIC_EXACT = {
    ("GET", "/health"),
    ("POST", "/auth/register"),
    ("POST", "/auth/login"),
    ("GET", "/movies"),
    ("GET", "/showtimes"),
    ("GET", "/docs"),
    ("GET", "/redoc"),
    ("GET", "/openapi.json"),
}
PUBLIC_PATTERNS = (
    re.compile(r"^/movies/[^/]+$"),
    re.compile(r"^/showtimes/[^/]+/seats$"),
)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if self._is_public(request) or request.method == "OPTIONS":
            return await call_next(request)
        authorization = request.headers.get("Authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return self._unauthorized("Bearer token is required")
        try:
            payload = request.app.state.container.tokens.decode(token)
            request.state.actor = User(
                id=str(payload["sub"]),
                email="",
                password_hash="",
                full_name="",
                role=UserRole(payload["role"]),
                created_at=request.app.state.container.clock.now(),
            )
        except Exception:
            return self._unauthorized("Token is invalid or expired")
        return await call_next(request)

    @staticmethod
    def _is_public(request: Request) -> bool:
        key = (request.method, request.url.path)
        return key in PUBLIC_EXACT or (
            request.method == "GET"
            and any(pattern.fullmatch(request.url.path) for pattern in PUBLIC_PATTERNS)
        )

    @staticmethod
    def _unauthorized(message: str) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
            content={"code": "UNAUTHORIZED", "message": message, "details": {}},
        )
