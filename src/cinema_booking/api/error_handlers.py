from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from cinema_booking.domain.errors import (
    BusinessRuleViolation,
    DomainError,
    EmailAlreadyUsed,
    Forbidden,
    InvalidCredentials,
    NotFound,
    SeatUnavailable,
    ShowtimeAlreadyStarted,
    ShowtimeOverlap,
)

STATUS_BY_ERROR: dict[type[DomainError], int] = {
    BusinessRuleViolation: 400,
    InvalidCredentials: 401,
    Forbidden: 403,
    NotFound: 404,
    EmailAlreadyUsed: 409,
    SeatUnavailable: 409,
    ShowtimeOverlap: 409,
    ShowtimeAlreadyStarted: 409,
}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(_request: Request, exc: DomainError) -> JSONResponse:
        status = next(
            (value for error_type, value in STATUS_BY_ERROR.items() if isinstance(exc, error_type)),
            400,
        )
        return JSONResponse(
            status_code=status,
            content={"code": exc.code, "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": exc.errors()},
            },
        )
