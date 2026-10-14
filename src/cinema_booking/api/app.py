from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from cinema_booking.api.config import Settings
from cinema_booking.api.dependencies import Container
from cinema_booking.api.error_handlers import register_error_handlers
from cinema_booking.api.middleware import AuthMiddleware
from cinema_booking.api.routers import auth, bookings, movies, rooms, showtimes
from cinema_booking.infrastructure.clock import SystemClock
from cinema_booking.infrastructure.database.session import (
    create_database_engine,
    create_session_factory,
    create_tables,
)
from cinema_booking.infrastructure.security.jwt_service import JwtTokenService
from cinema_booking.infrastructure.security.password_hasher import BcryptPasswordHasher

PUBLIC_OPENAPI_OPERATIONS = {
    ("/health", "get"),
    ("/auth/register", "post"),
    ("/auth/login", "post"),
    ("/movies", "get"),
    ("/movies/{movie_id}", "get"),
    ("/showtimes", "get"),
    ("/showtimes/{showtime_id}/seats", "get"),
}


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or Settings()
    engine = create_database_engine(app_settings.database_url, app_settings.db_pool_size)
    container = Container(
        session_factory=create_session_factory(engine),
        hasher=BcryptPasswordHasher(app_settings.bcrypt_rounds),
        tokens=JwtTokenService(app_settings.jwt_secret, app_settings.jwt_expires_minutes),
        clock=SystemClock(),
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        create_tables(engine)
        yield
        engine.dispose()

    application = FastAPI(
        title="Cinema Booking API",
        version="1.0.0",
        description="REST API for movies, showtimes, seats, and ticket booking.",
        lifespan=lifespan,
    )
    application.state.container = container
    application.add_middleware(AuthMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(application)
    application.include_router(auth.router)
    application.include_router(movies.router)
    application.include_router(rooms.router)
    application.include_router(showtimes.router)
    application.include_router(bookings.router)

    @application.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    def custom_openapi() -> dict:
        if application.openapi_schema:
            return application.openapi_schema
        schema = get_openapi(
            title=application.title,
            version=application.version,
            description=application.description,
            routes=application.routes,
        )
        schema.setdefault("components", {}).setdefault("securitySchemes", {})["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
        http_methods = {"get", "post", "put", "patch", "delete", "options", "head"}
        for path, methods in schema["paths"].items():
            for method, operation in methods.items():
                if method not in http_methods:
                    continue
                operation["security"] = (
                    [] if (path, method) in PUBLIC_OPENAPI_OPERATIONS else [{"BearerAuth": []}]
                )
        application.openapi_schema = schema
        return schema

    application.openapi = custom_openapi
    return application


app = create_app()
