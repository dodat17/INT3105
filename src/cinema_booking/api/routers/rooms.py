from fastapi import APIRouter, Depends, status

from cinema_booking.api.dependencies import Container, get_actor, get_container
from cinema_booking.api.schemas.room import RoomCreate, RoomResponse
from cinema_booking.domain.entities import Room, User

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomResponse])
def list_rooms(
    actor: User = Depends(get_actor), container: Container = Depends(get_container)
) -> list[Room]:
    return container.room_service().list(actor)


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
def create_room(
    payload: RoomCreate,
    actor: User = Depends(get_actor),
    container: Container = Depends(get_container),
) -> Room:
    room, _seats = container.room_service().create(actor, **payload.model_dump())
    return room
