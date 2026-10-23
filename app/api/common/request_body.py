from fastapi import HTTPException, Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.common.errors import error_response

MAX_BODY_BYTES = 64 * 1024  # NFR-06
_TOO_LARGE = (413, "PAYLOAD_TOO_LARGE", "Body vượt quá 64 KB.")


class RequestBodyMiddleware:
    """NFR-06: API bodies must be JSON and at most 64 KB.

    Runs before authentication: the contract checks body format first (section 6.4).
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope["path"].startswith("/api/"):
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        length = request.headers.get("content-length")
        has_body = (length is not None and length != "0") or "transfer-encoding" in request.headers
        if has_body:
            media_type = request.headers.get("content-type", "").partition(";")[0].strip()
            if media_type.lower() != "application/json":
                response = error_response(
                    request,
                    status_code=415,
                    code="UNSUPPORTED_MEDIA_TYPE",
                    message="Content-Type phải là application/json.",
                )
                await response(scope, receive, send)
                return
            if length is not None and length.isdigit() and int(length) > MAX_BODY_BYTES:
                status_code, code, message = _TOO_LARGE
                response = error_response(
                    request, status_code=status_code, code=code, message=message
                )
                await response(scope, receive, send)
                return

        received = 0

        # A chunked body has no Content-Length, so it is also counted while being read.
        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > MAX_BODY_BYTES:
                    raise HTTPException(status_code=413, detail=_TOO_LARGE[2])
            return message

        await self.app(scope, limited_receive, send)
