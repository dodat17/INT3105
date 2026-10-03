from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter
from pydantic import StringConstraints

from app.api.common.auth import ActorDep
from app.api.common.schemas import CamelModel, RequestModel
from app.api.dependencies import AuthServiceDep
from app.domain.auth.model import Role, User

router = APIRouter(prefix="/auth", tags=["auth"])

Email = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=320, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
]
# Passwords are kept verbatim (no stripping); the minimum length is BR-02 in the domain.
Password = Annotated[str, StringConstraints(min_length=1, max_length=128)]


class RegisterRequest(RequestModel):
    email: Email
    password: Password
    full_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]


class LoginRequest(RequestModel):
    email: Annotated[str, StringConstraints(min_length=1, max_length=320)]
    password: Password


class TokenResponse(CamelModel):
    access_token: str
    token_type: Literal["Bearer"] = "Bearer"
    expires_in: int


class UserResponse(CamelModel):
    id: UUID
    email: str
    full_name: str
    role: Role
    created_at: datetime

    @classmethod
    def from_domain(cls, user: User) -> "UserResponse":
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            created_at=user.created_at,
        )


@router.post("/register", status_code=201, summary="Đăng ký tài khoản CUSTOMER")
def register(payload: RegisterRequest, service: AuthServiceDep) -> UserResponse:
    user = service.register(payload.email, payload.password, payload.full_name)
    return UserResponse.from_domain(user)


@router.post("/login", summary="Đăng nhập, nhận JWT")
def login(payload: LoginRequest, service: AuthServiceDep) -> TokenResponse:
    token = service.login(payload.email, payload.password)
    return TokenResponse(access_token=token.access_token, expires_in=token.expires_in)


@router.get("/me", summary="Thông tin người dùng hiện tại")
def me(actor: ActorDep, service: AuthServiceDep) -> UserResponse:
    return UserResponse.from_domain(service.current_user(actor))
