import re
from typing import Annotated

from fastapi import Depends, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.types import ASGIApp, Receive, Scope, Send

from app.api.common.errors import UNAUTHENTICATED, error_response
from app.domain.auth.model import Actor
from app.domain.errors import InvalidTokenError
from app.domain.ports import TokenService

# Everything under /api/ needs a token unless listed here, so a new route is protected
# by default. Paths outside /api/ (health, docs, the SPA) are public.
_PUBLIC_API_ROUTES: list[tuple[frozenset[str], re.Pattern[str]]] = [
    (frozenset({"POST"}), re.compile(r"/api/v1/auth/(register|login)")),
    (frozenset({"GET", "HEAD"}), re.compile(r"/api/v1/movies(/[^/]+)?")),
    (frozenset({"GET", "HEAD"}), re.compile(r"/api/v1/showtimes(/[^/]+(/seats)?)?")),
]


def _is_public(method: str, path: str) -> bool:
    if not path.startswith("/api/"):
        return True
    return any(
        method in methods and pattern.fullmatch(path) for methods, pattern in _PUBLIC_API_ROUTES
    )


class AuthMiddleware:
    """Single place where bearer tokens are verified; routers never read the header."""

    def __init__(self, app: ASGIApp, tokens: TokenService) -> None:
        self.app = app
        self.tokens = tokens

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or _is_public(scope["method"], scope["path"]):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        scheme, _, token = request.headers.get("authorization", "").partition(" ")
        try:
            if scheme.lower() != "bearer" or not token:
                raise InvalidTokenError
            actor = self.tokens.decode(token.strip())
        except InvalidTokenError:
            status_code, code, message = UNAUTHENTICATED
            response = error_response(
                request,
                status_code=status_code,
                code=code,
                message=message,
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return

        scope.setdefault("state", {})["actor"] = actor
        await self.app(scope, receive, send)


# auto_error=False: the middleware has already rejected bad tokens; this only makes
# Swagger show the Authorize button and lock icons on protected operations.
_bearer = HTTPBearer(auto_error=False, description="Dán accessToken từ POST /auth/login.")


def current_actor(
    request: Request,
    _: Annotated[HTTPAuthorizationCredentials | None, Security(_bearer)],
) -> Actor:
    actor = getattr(request.state, "actor", None)
    if not isinstance(actor, Actor):
        raise InvalidTokenError
    return actor


ActorDep = Annotated[Actor, Depends(current_actor)]
