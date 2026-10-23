from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response
from pydantic import AwareDatetime, Field

from app.api.common.auth import ActorDep
from app.api.common.schemas import CamelModel, PageResponse, RequestModel
from app.api.dependencies import ShowtimeServiceDep
from app.domain.cinema.model import SeatType
from app.domain.scheduling.model import SeatMapEntry, SeatStatus, Showtime

router = APIRouter(prefix="/showtimes", tags=["scheduling"])
admin_router = APIRouter(prefix="/admin/showtimes", tags=["admin"])


class ShowtimeCreateRequest(RequestModel):
    movie_id: UUID
    auditorium_id: UUID
    starts_at: Annotated[AwareDatetime, Field(description="ISO 8601 kèm múi giờ")]
    base_price: Annotated[int, Field(gt=0, le=10_000_000, description="Giá ghế thường, VND")]


class ShowtimeResponse(CamelModel):
    id: UUID
    movie_id: UUID
    auditorium_id: UUID
    starts_at: datetime
    ends_at: datetime
    base_price: int
    is_open_for_booking: bool

    @classmethod
    def from_domain(cls, showtime: Showtime) -> "ShowtimeResponse":
        return cls(
            id=showtime.id,
            movie_id=showtime.movie_id,
            auditorium_id=showtime.room_id,
            starts_at=showtime.starts_at,
            ends_at=showtime.ends_at,
            base_price=showtime.base_price,
            is_open_for_booking=showtime.is_open_for_booking,
        )


class AuditoriumRef(CamelModel):
    id: UUID
    name: str


class SeatResponse(CamelModel):
    id: UUID
    row_label: str
    number: int
    label: str
    seat_type: SeatType
    price: int
    status: SeatStatus

    @classmethod
    def from_domain(cls, entry: SeatMapEntry) -> "SeatResponse":
        seat = entry.seat
        return cls(
            id=seat.id,
            row_label=seat.row_label,
            number=seat.number,
            label=f"{seat.row_label}{seat.number}",
            seat_type=seat.seat_type,
            price=entry.price,
            status=entry.status,
        )


class SeatMapResponse(CamelModel):
    showtime_id: UUID
    auditorium: AuditoriumRef
    seats: list[SeatResponse]


@router.get("", summary="Lịch chiếu (lọc theo phim, ngày)")
def list_showtimes(
    service: ShowtimeServiceDep,
    movie_id: Annotated[UUID | None, Query(alias="movieId")] = None,
    on_date: Annotated[
        date | None,
        Query(alias="date", description="YYYY-MM-DD, tính theo múi giờ của rạp"),
    ] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
) -> PageResponse[ShowtimeResponse]:
    result = service.list_showtimes(movie_id, on_date, page, page_size)
    return PageResponse[ShowtimeResponse](
        items=[ShowtimeResponse.from_domain(showtime) for showtime in result.items],
        page=result.page,
        page_size=result.page_size,
        total_items=result.total_items,
    )


@router.get("/{showtime_id}/seats", summary="Sơ đồ ghế của suất chiếu")
def seat_map(showtime_id: UUID, service: ShowtimeServiceDep) -> SeatMapResponse:
    showtime, room, entries = service.seat_map(showtime_id)
    return SeatMapResponse(
        showtime_id=showtime.id,
        auditorium=AuditoriumRef(id=room.id, name=room.name),
        seats=[SeatResponse.from_domain(entry) for entry in entries],
    )


@admin_router.post("", status_code=201, summary="Tạo suất chiếu (ADMIN)")
def create_showtime(
    payload: ShowtimeCreateRequest, actor: ActorDep, service: ShowtimeServiceDep
) -> ShowtimeResponse:
    showtime = service.create_showtime(
        actor,
        movie_id=payload.movie_id,
        room_id=payload.auditorium_id,
        starts_at=payload.starts_at,
        base_price=payload.base_price,
    )
    return ShowtimeResponse.from_domain(showtime)


@admin_router.delete("/{showtime_id}", status_code=204, summary="Xóa suất chiếu (ADMIN)")
def delete_showtime(showtime_id: UUID, actor: ActorDep, service: ShowtimeServiceDep) -> Response:
    service.delete_showtime(actor, showtime_id)
    return Response(status_code=204)
