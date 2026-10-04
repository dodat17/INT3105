import logging
from functools import partial
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
from starlette.types import Scope

from app.api.common.auth import AuthMiddleware
from app.api.common.errors import register_exception_handlers
from app.api.common.request_id import RequestIdMiddleware
from app.api.router import root_router
from app.bootstrap.settings import Settings, get_settings
from app.domain.auth.service import AuthService
from app.domain.catalog.service import MovieService
from app.infrastructure.clock import SystemClock
from app.infrastructure.persistence.uow import SqlAlchemyUnitOfWork, create_session_factory
from app.infrastructure.security.passwords import BcryptPasswordHasher
from app.infrastructure.security.tokens import JwtTokenService


class SpaStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            response = await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code != 404:
                raise
            return await super().get_response("index.html", scope)
        if response.status_code == 404:
            return await super().get_response("index.html", scope)
        return response


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(
        level=settings.app_log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    session_factory = create_session_factory(settings.database_url, settings.db_pool_size)
    uow_factory = partial(SqlAlchemyUnitOfWork, session_factory)
    tokens = JwtTokenService(settings.jwt_secret, settings.jwt_algorithm, settings.jwt_ttl_seconds)

    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.state.auth_service = AuthService(
        uow_factory, BcryptPasswordHasher(settings.bcrypt_rounds), tokens, SystemClock()
    )
    app.state.movie_service = MovieService(uow_factory)
    # Added last runs first: request ID wraps authentication so 401s carry it too.
    app.add_middleware(AuthMiddleware, tokens=tokens)
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)
    app.include_router(root_router)

    @app.api_route(
        "/api/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        include_in_schema=False,
    )
    def api_not_found(path: str) -> None:
        del path
        raise HTTPException(status_code=404, detail="Không tìm thấy tài nguyên.")

    frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if frontend_dist.is_dir():
        app.mount("/", SpaStaticFiles(directory=frontend_dist, html=True), name="frontend")

    return app
