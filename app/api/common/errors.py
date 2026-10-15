from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.errors import (
    BookingExpiredError,
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

UNAUTHORIZED = (401, "UNAUTHORIZED", "Yêu cầu đăng nhập.")

# status, code, default message
_DOMAIN_ERRORS: dict[type[DomainError], tuple[int, str, str]] = {
    NotFoundError: (404, "NOT_FOUND", "Không tìm thấy tài nguyên."),
    ForbiddenError: (403, "FORBIDDEN", "Bạn không có quyền thực hiện thao tác này."),
    BusinessRuleViolation: (400, "BUSINESS_RULE_VIOLATION", "Vi phạm quy tắc nghiệp vụ."),
    EmailAlreadyUsedError: (409, "EMAIL_ALREADY_USED", "Email đã được sử dụng."),
    InvalidCredentialsError: (401, "INVALID_CREDENTIALS", "Email hoặc mật khẩu không đúng."),
    InvalidTokenError: UNAUTHORIZED,
    RoomNameAlreadyUsedError: (409, "ROOM_NAME_ALREADY_USED", "Tên phòng đã tồn tại."),
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
        return error_response(
            request,
            status_code=status_code,
            code=code,
            message=str(exc) or default_message,
        )

    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "Yêu cầu không hợp lệ."
        return error_response(
            request,
            status_code=exc.status_code,
            code="HTTP_ERROR",
            message=message,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return error_response(
            request,
            status_code=400,
            code="VALIDATION_ERROR",
            message="Dữ liệu yêu cầu không hợp lệ.",
            details=exc.errors(),
        )
