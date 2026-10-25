from typing import Any

from fastapi import FastAPI

_ERROR_REF = {"$ref": "#/components/schemas/ErrorResponse"}


def _error(description: str) -> dict[str, Any]:
    return {"description": description, "content": {"application/json": {"schema": _ERROR_REF}}}


def install_error_responses(app: FastAPI) -> None:
    """Document the error envelope the runtime really returns (section 6.4).

    FastAPI advertises 422 for every operation with parameters, but validation errors
    are answered with 400 VALIDATION_ERROR, so the generated schema is rewritten once.
    """
    generate = app.openapi

    def openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        schema = generate()
        for path, operations in schema["paths"].items():
            if not path.startswith("/api/"):
                continue
            for operation in operations.values():
                responses = operation["responses"]
                if responses.pop("422", None) is not None:
                    responses.setdefault("400", _error("VALIDATION_ERROR: dữ liệu không hợp lệ"))
                if "requestBody" in operation:
                    responses.setdefault("413", _error("PAYLOAD_TOO_LARGE: body vượt 64 KB"))
                    responses.setdefault(
                        "415", _error("UNSUPPORTED_MEDIA_TYPE: body không phải JSON")
                    )
                if operation.get("security"):
                    responses.setdefault("401", _error("UNAUTHENTICATED: thiếu hoặc sai token"))
                if path.startswith("/api/v1/admin/"):
                    responses.setdefault("403", _error("FORBIDDEN: yêu cầu vai trò ADMIN"))
                if "{" in path:
                    responses.setdefault("404", _error("RESOURCE_NOT_FOUND"))
                responses.setdefault("500", _error("INTERNAL_ERROR"))
        components = schema.get("components", {}).get("schemas", {})
        components.pop("HTTPValidationError", None)
        components.pop("ValidationError", None)
        return schema

    app.openapi = openapi  # type: ignore[method-assign]
