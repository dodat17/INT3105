from typing import Annotated, cast

from fastapi import Depends, Request

from app.domain.auth.service import AuthService
from app.domain.catalog.service import MovieService
from app.domain.cinema.service import RoomService


def get_auth_service(request: Request) -> AuthService:
    return cast(AuthService, request.app.state.auth_service)


def get_movie_service(request: Request) -> MovieService:
    return cast(MovieService, request.app.state.movie_service)


def get_room_service(request: Request) -> RoomService:
    return cast(RoomService, request.app.state.room_service)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
MovieServiceDep = Annotated[MovieService, Depends(get_movie_service)]
RoomServiceDep = Annotated[RoomService, Depends(get_room_service)]
