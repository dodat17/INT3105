import logging
from functools import partial
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response
from starlette.routing import Match
from starlette.types import Scope

from app.api.common.auth import AuthMiddleware
from app.api.common.errors import register_exception_handlers
from app.api.common.openapi import install_error_responses
from app.api.common.request_body import RequestBodyMiddleware
from app.api.common.request_id import RequestIdMiddleware
from app.api.common.security_headers import SecurityHeadersMiddleware
from app.api.router import root_router
from app.bootstrap.settings import Settings, get_settings
from app.domain.auth.service import AuthService
from app.domain.booking.service import BookingService
from app.domain.catalog.service import MovieService
from app.domain.cinema.service import RoomService
from app.domain.scheduling.service import ShowtimeService
from app.infrastructure.clock import SystemClock
from app.infrastructure.persistence.readiness import DatabaseReadiness
from app.infrastructure.persistence.uow import SqlAlchemyUnitOfWork, create_session_factory
from app.infrastructure.security.passwords import BcryptPasswordHasher
from app.infrastructure.security.tokens import JwtTokenService

API_DESCRIPTION = """Hợp đồng API cho dịch vụ đặt vé xem phim, đối chiếu mục 6 của requirements.md.

**Xác nhận đặt vé là mô phỏng.** `POST /api/v1/bookings/{bookingId}/confirm` không thực hiện
thanh toán và không được hiểu là "thanh toán thành công".

Mọi mốc thời gian lưu ở UTC và trả ở ISO 8601 có timezone. Giá trị tiền là số nguyên VND.
Mọi lỗi JSON có dạng `{"error": {"code", "message", "requestId", "details?"}}`.
Endpoint dưới `/api/v1/admin/` yêu cầu token của tài khoản ADMIN.
"""


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
    # One adapter serves every module; each service sees it only through its own module port.
    uow_factory = partial(SqlAlchemyUnitOfWork, session_factory)
    tokens = JwtTokenService(settings.jwt_secret, settings.jwt_algorithm, settings.jwt_ttl_seconds)

    app = FastAPI(title=settings.app_name, version="0.1.0", description=API_DESCRIPTION)
    app.state.readiness = DatabaseReadiness(session_factory)
    app.state.auth_service = AuthService(
        uow_factory, BcryptPasswordHasher(settings.bcrypt_rounds), tokens, SystemClock()
    )
    app.state.movie_service = MovieService(uow_factory)
    app.state.room_service = RoomService(uow_factory)
    app.state.showtime_service = ShowtimeService(uow_factory, ZoneInfo(settings.cinema_timezone))
    app.state.booking_service = BookingService(
        uow_factory,
        settings.hold_ttl_seconds,
        settings.max_holds_per_showtime,
        settings.max_active_holds,
    )
    # Added last runs first: request ID and security headers also cover authentication errors.
    app.add_middleware(AuthMiddleware, tokens=tokens)
    app.add_middleware(RequestBodyMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)
    install_error_responses(app)
    app.include_router(root_router)
    known_routes = list(app.router.routes)

    # Unknown API and health paths answer with a JSON 404, never the SPA's index.html.
    @app.api_route(
        "/api/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        include_in_schema=False,
    )
    @app.api_route(
        "/health/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        include_in_schema=False,
    )
    def api_not_found(request: Request, path: str) -> None:
        del path
        # The catch-all also matches known paths with a wrong method: that is a 405, not a 404.
        allowed = [
            method
            for method in ("DELETE", "GET", "PATCH", "POST", "PUT")
            if any(
                route.matches({**request.scope, "method": method})[0] is Match.FULL
                for route in known_routes
            )
        ]
        if allowed:
            raise HTTPException(
                status_code=405,
                detail="Method không được hỗ trợ.",
                headers={"Allow": ", ".join(allowed)},
            )
        raise HTTPException(status_code=404, detail="Không tìm thấy tài nguyên.")

    frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if frontend_dist.is_dir():
        app.mount("/", SpaStaticFiles(directory=frontend_dist, html=True), name="frontend")

    return app
