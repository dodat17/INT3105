from typing import Annotated, cast

from fastapi import Depends, Request

from app.domain.auth.service import AuthService


def get_auth_service(request: Request) -> AuthService:
    return cast(AuthService, request.app.state.auth_service)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
