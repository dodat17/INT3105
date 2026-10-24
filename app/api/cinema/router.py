from string import ascii_uppercase
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from pydantic import Field, StringConstraints

from app.api.common.auth import ActorDep
from app.api.common.schemas import CamelModel, RequestModel
from app.api.dependencies import RoomServiceDep
from app.domain.cinema.model import MAX_COLS, MAX_ROWS, Room, Seat, SeatType

# The domain says "room"; the public contract (requirements section 7) says "auditorium".
router = APIRouter(prefix="/admin/auditoriums", tags=["admin"])


class AuditoriumCreateRequest(RequestModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    rows: Annotated[int, Field(ge=1, le=MAX_ROWS)]
    cols: Annotated[int, Field(ge=1, le=MAX_COLS)]
    vip_rows: Annotated[
        list[int], Field(max_length=MAX_ROWS, description="Số thứ tự hàng VIP, 1 = hàng A")
    ] = []


class AuditoriumUpdateRequest(AuditoriumCreateRequest):
    """PUT replaces the layout; seats are generated again."""


class AuditoriumResponse(CamelModel):
    id: UUID
    name: str
    rows: int
    cols: int
    seat_count: int

    @classmethod
    def from_domain(cls, room: Room) -> "AuditoriumResponse":
        return cls(
            id=room.id,
            name=room.name,
            rows=room.rows,
            cols=room.cols,
            seat_count=room.rows * room.cols,
        )


class AuditoriumDetailResponse(AuditoriumResponse):
    vip_rows: list[int]

    @classmethod
    def from_seats(cls, room: Room, seats: list[Seat]) -> "AuditoriumDetailResponse":
        vip_rows = {
            ascii_uppercase.index(seat.row_label) + 1
            for seat in seats
            if seat.seat_type is SeatType.VIP
        }
        return cls(**AuditoriumResponse.from_domain(room).model_dump(), vip_rows=sorted(vip_rows))


@router.get("", summary="Danh sách phòng chiếu (ADMIN)")
def list_auditoriums(actor: ActorDep, service: RoomServiceDep) -> list[AuditoriumResponse]:
    return [AuditoriumResponse.from_domain(room) for room in service.list_rooms(actor)]


@router.post("", status_code=201, summary="Tạo phòng chiếu và sinh ghế (ADMIN)")
def create_auditorium(
    payload: AuditoriumCreateRequest, actor: ActorDep, service: RoomServiceDep
) -> AuditoriumResponse:
    room = service.create_room(
        actor,
        name=payload.name,
        rows=payload.rows,
        cols=payload.cols,
        vip_rows=set(payload.vip_rows),
    )
    return AuditoriumResponse.from_domain(room)


@router.get("/{auditorium_id}", summary="Chi tiết phòng chiếu (ADMIN)")
def get_auditorium(
    auditorium_id: UUID, actor: ActorDep, service: RoomServiceDep
) -> AuditoriumDetailResponse:
    room, seats = service.get_room(actor, auditorium_id)
    return AuditoriumDetailResponse.from_seats(room, seats)


@router.put("/{auditorium_id}", summary="Cập nhật phòng chiếu chưa có suất chiếu (ADMIN)")
def update_auditorium(
    auditorium_id: UUID,
    payload: AuditoriumUpdateRequest,
    actor: ActorDep,
    service: RoomServiceDep,
) -> AuditoriumDetailResponse:
    service.update_room(
        actor,
        auditorium_id,
        name=payload.name,
        rows=payload.rows,
        cols=payload.cols,
        vip_rows=set(payload.vip_rows),
    )
    room, seats = service.get_room(actor, auditorium_id)
    return AuditoriumDetailResponse.from_seats(room, seats)
