from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from pydantic import Field, StringConstraints

from app.api.common.auth import ActorDep
from app.api.common.schemas import CamelModel, RequestModel
from app.api.dependencies import RoomServiceDep
from app.domain.cinema.model import MAX_COLS, MAX_ROWS, Room

router = APIRouter(prefix="/rooms", tags=["cinema"])


class RoomCreateRequest(RequestModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    rows: Annotated[int, Field(ge=1, le=MAX_ROWS)]
    cols: Annotated[int, Field(ge=1, le=MAX_COLS)]
    vip_rows: Annotated[
        list[int], Field(max_length=MAX_ROWS, description="Số thứ tự hàng VIP, 1 = hàng A")
    ] = []


class RoomResponse(CamelModel):
    id: UUID
    name: str
    rows: int
    cols: int
    seat_count: int

    @classmethod
    def from_domain(cls, room: Room) -> "RoomResponse":
        return cls(
            id=room.id,
            name=room.name,
            rows=room.rows,
            cols=room.cols,
            seat_count=room.rows * room.cols,
        )


@router.get("", summary="Danh sách phòng chiếu (ADMIN)")
def list_rooms(actor: ActorDep, service: RoomServiceDep) -> list[RoomResponse]:
    return [RoomResponse.from_domain(room) for room in service.list_rooms(actor)]


@router.post("", status_code=201, summary="Tạo phòng chiếu và sinh ghế (ADMIN)")
def create_room(
    payload: RoomCreateRequest, actor: ActorDep, service: RoomServiceDep
) -> RoomResponse:
    room = service.create_room(
        actor,
        name=payload.name,
        rows=payload.rows,
        cols=payload.cols,
        vip_rows=set(payload.vip_rows),
    )
    return RoomResponse.from_domain(room)
