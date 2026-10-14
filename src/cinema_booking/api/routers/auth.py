from fastapi import APIRouter, Depends, status

from cinema_booking.api.dependencies import Container, get_actor, get_container
from cinema_booking.api.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from cinema_booking.domain.entities import User

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, container: Container = Depends(get_container)) -> User:
    return container.auth_service().register(payload.email, payload.password, payload.full_name)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, container: Container = Depends(get_container)) -> TokenResponse:
    token, expires_in = container.auth_service().login(payload.email, payload.password)
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=UserResponse)
def me(
    actor: User = Depends(get_actor), container: Container = Depends(get_container)
) -> User:
    return container.auth_service().get_user(actor.id)
