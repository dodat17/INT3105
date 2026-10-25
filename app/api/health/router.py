from collections.abc import Callable
from typing import Literal, cast

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.common.errors import error_response
from app.api.common.schemas import ErrorResponse

router = APIRouter(tags=["ops"])

CheckStatus = Literal["ok", "fail"]


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ReadinessResponse(BaseModel):
    status: Literal["ok"]
    checks: dict[str, CheckStatus]


@router.get("/health", response_model=HealthResponse)
@router.get("/health/live", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={
        503: {"model": ErrorResponse, "description": "DB lỗi hoặc schema chưa ở migration mới nhất"}
    },
)
def ready(request: Request) -> ReadinessResponse | JSONResponse:
    readiness = cast(Callable[[], dict[str, bool]], request.app.state.readiness)
    # Only check names and ok/fail: never connection strings, hosts or versions.
    checks: dict[str, CheckStatus] = {
        name: "ok" if passed else "fail" for name, passed in readiness().items()
    }
    if all(status == "ok" for status in checks.values()):
        return ReadinessResponse(status="ok", checks=checks)
    return error_response(
        request,
        status_code=503,
        code="SERVICE_UNAVAILABLE",
        message="Dịch vụ chưa sẵn sàng.",
        details={"checks": checks},
    )
