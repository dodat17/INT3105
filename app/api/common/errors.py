import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.domain.errors import (
    BookingExpiredError,
    BookingValidationError,
    BusinessRuleViolation,
    DomainError,
    EmailAlreadyUsedError,
    ForbiddenError,
    HoldLimitExceededError,
    InvalidBookingStateError,
    InvalidCredentialsError,
    InvalidTokenError,
    NotFoundError,
    RoomNameAlreadyUsedError,
    SeatUnavailableError,
    ShowtimeNotBookableError,
    ShowtimeOverlapError,
)

logger = logging.getLogger("app.error")

UNAUTHENTICATED = (401, "UNAUTHENTICATED", "Yêu cầu đăng nhập.")

_HTTP_ERROR_CODES = {
    400: "VALIDATION_ERROR",
    404: "RESOURCE_NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    413: "PAYLOAD_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    503: "SERVICE_UNAVAILABLE",
}

# status, code, default message
_DOMAIN_ERRORS: dict[type[DomainError], tuple[int, str, str]] = {
    NotFoundError: (404, "RESOURCE_NOT_FOUND", "Không tìm thấy tài nguyên."),
    ForbiddenError: (403, "FORBIDDEN", "Bạn không có quyền thực hiện thao tác này."),
    BusinessRuleViolation: (400, "BUSINESS_RULE_VIOLATION", "Vi phạm quy tắc nghiệp vụ."),
    BookingValidationError: (400, "VALIDATION_ERROR", "Dữ liệu yêu cầu không hợp lệ."),
    EmailAlreadyUsedError: (409, "EMAIL_ALREADY_USED", "Email đã được sử dụng."),
    InvalidCredentialsError: (401, "INVALID_CREDENTIALS", "Email hoặc mật khẩu không đúng."),
    InvalidTokenError: UNAUTHENTICATED,
    RoomNameAlreadyUsedError: (
        409,
        "AUDITORIUM_NAME_ALREADY_USED",
        "Tên phòng chiếu đã tồn tại.",
    ),
    ShowtimeOverlapError: (
        409,
        "SHOWTIME_OVERLAP",
        "Suất chiếu bị trùng giờ với một suất khác trong cùng phòng.",
    ),
    SeatUnavailableError: (409, "SEAT_UNAVAILABLE", "Một hoặc nhiều ghế không còn trống."),
    BookingExpiredError: (409, "BOOKING_EXPIRED", "Booking đã hết hạn."),
    InvalidBookingStateError: (409, "INVALID_BOOKING_STATE", "Trạng thái booking không hợp lệ."),
    ShowtimeNotBookableError: (409, "SHOWTIME_NOT_BOOKABLE", "Suất chiếu không còn nhận đặt chỗ."),
    HoldLimitExceededError: (409, "HOLD_LIMIT_EXCEEDED", "Đã vượt giới hạn booking đang giữ."),
}


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", "unknown"))


def error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: Any | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    error: dict[str, Any] = {
        "code": code,
        "message": message,
        "requestId": _request_id(request),
    }
    if details is not None:
        error["details"] = details
    return JSONResponse(status_code=status_code, content={"error": error}, headers=headers)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        status_code, code, default_message = _DOMAIN_ERRORS[type(exc)]
        details = None
        if isinstance(exc, BookingValidationError):
            details = {"fields": sorted(exc.fields)}
        elif isinstance(exc, SeatUnavailableError) and exc.seat_ids:
            details = {"seatIds": sorted(exc.seat_ids)}
        return error_response(
            request,
            status_code=status_code,
            code=code,
            message=str(exc) or default_message,
            details=details,
        )

    # Starlette's base class also covers routing errors (404, 405) raised outside FastAPI.
    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "Yêu cầu không hợp lệ."
        return error_response(
            request,
            status_code=exc.status_code,
            code=_HTTP_ERROR_CODES.get(exc.status_code, "HTTP_ERROR"),
            message=message,
            headers=dict(exc.headers) if exc.headers else None,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # Stack trace goes to the log only; the client never sees SQL or internals.
        logger.exception("request_id=%s unhandled error", _request_id(request), exc_info=exc)
        return error_response(
            request,
            status_code=500,
            code="INTERNAL_ERROR",
            message="Lỗi hệ thống, vui lòng thử lại sau.",
            # Runs outside RequestIdMiddleware, so the header is added here.
            headers={"x-request-id": _request_id(request)},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        fields = {
            str(error["loc"][1])
            for error in exc.errors()
            if len(error.get("loc", ())) > 1 and error["loc"][0] in {"body", "path", "query"}
        }
        return error_response(
            request,
            status_code=400,
            code="VALIDATION_ERROR",
            message="Dữ liệu yêu cầu không hợp lệ.",
            details={"fields": sorted(fields)},
        )
