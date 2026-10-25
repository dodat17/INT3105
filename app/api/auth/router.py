from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query, Response
from pydantic import StringConstraints

from app.api.common.auth import ActorDep
from app.api.common.schemas import CONFLICT, CamelModel, PageResponse, RequestModel
from app.api.dependencies import AuthServiceDep
from app.domain.auth.model import Role, User

router = APIRouter(prefix="/auth", tags=["auth"])
admin_router = APIRouter(prefix="/admin/users", tags=["admin"])

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


class UserUpdateRequest(RequestModel):
    """Email and password stay with the account owner; admins change only these."""

    full_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    role: Role


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


@router.post("/register", status_code=201, summary="Đăng ký tài khoản CUSTOMER", responses=CONFLICT)
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


@admin_router.get("", summary="Danh sách người dùng (ADMIN)")
def list_users(
    actor: ActorDep,
    service: AuthServiceDep,
    q: Annotated[str | None, Query(max_length=100, description="Tìm theo email, họ tên")] = None,
    role: Annotated[Role | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
) -> PageResponse[UserResponse]:
    result = service.list_users(actor, q, role, page, page_size)
    return PageResponse[UserResponse](
        items=[UserResponse.from_domain(user) for user in result.items],
        page=result.page,
        page_size=result.page_size,
        total_items=result.total_items,
    )


@admin_router.get("/{user_id}", summary="Chi tiết người dùng (ADMIN)")
def get_user(user_id: UUID, actor: ActorDep, service: AuthServiceDep) -> UserResponse:
    return UserResponse.from_domain(service.get_user(actor, user_id))


@admin_router.put("/{user_id}", summary="Đổi họ tên, vai trò người dùng (ADMIN)")
def update_user(
    user_id: UUID, payload: UserUpdateRequest, actor: ActorDep, service: AuthServiceDep
) -> UserResponse:
    user = service.update_user(actor, user_id, full_name=payload.full_name, role=payload.role)
    return UserResponse.from_domain(user)


@admin_router.delete(
    "/{user_id}", status_code=204, summary="Xóa người dùng chưa có booking (ADMIN)"
)
def delete_user(user_id: UUID, actor: ActorDep, service: AuthServiceDep) -> Response:
    service.delete_user(actor, user_id)
    return Response(status_code=204)
