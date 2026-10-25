from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """JSON uses camelCase; Python code uses snake_case."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class RequestModel(CamelModel):
    # Reject fields outside the contract so clients cannot set role, id, ...
    model_config = ConfigDict(extra="forbid")


class PageResponse[T](CamelModel):
    items: list[T]
    page: int
    page_size: int
    total_items: int


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str = Field(alias="requestId")
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Envelope of every JSON error (section 6.4); details only when there is extra data."""

    error: ErrorBody


CONFLICT: dict[int | str, dict[str, Any]] = {
    409: {"model": ErrorResponse, "description": "Xung đột nghiệp vụ, xem error.code"}
}
CUSTOMER_ONLY: dict[int | str, dict[str, Any]] = {
    403: {"model": ErrorResponse, "description": "FORBIDDEN: chỉ dành cho CUSTOMER"}
}
