from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response
from pydantic import AwareDatetime, Field

from app.api.common.auth import ActorDep
from app.api.common.schemas import CONFLICT, CamelModel, PageResponse, RequestModel
from app.api.dependencies import ShowtimeServiceDep
from app.domain.scheduling.model import Showtime

router = APIRouter(prefix="/showtimes", tags=["scheduling"])
admin_router = APIRouter(prefix="/admin/showtimes", tags=["admin"])


class ShowtimeCreateRequest(RequestModel):
    movie_id: UUID
    auditorium_id: UUID
    starts_at: Annotated[AwareDatetime, Field(description="ISO 8601 kèm múi giờ")]
    base_price: Annotated[int, Field(gt=0, le=10_000_000, description="Giá ghế thường, VND")]


class ShowtimeUpdateRequest(ShowtimeCreateRequest):
    is_open_for_booking: bool = True


class ShowtimeResponse(CamelModel):
    id: UUID
    movie_id: UUID
    auditorium_id: UUID
    starts_at: datetime
    ends_at: datetime
    base_price: int
    currency: str = "VND"
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


class MovieRef(CamelModel):
    id: UUID
    title: str


class AuditoriumRef(CamelModel):
    id: UUID
    name: str


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


@admin_router.post("", status_code=201, summary="Tạo suất chiếu (ADMIN)", responses=CONFLICT)
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


@admin_router.put("/{showtime_id}", summary="Cập nhật suất chiếu (ADMIN)", responses=CONFLICT)
def update_showtime(
    showtime_id: UUID,
    payload: ShowtimeUpdateRequest,
    actor: ActorDep,
    service: ShowtimeServiceDep,
) -> ShowtimeResponse:
    showtime = service.update_showtime(
        actor,
        showtime_id,
        movie_id=payload.movie_id,
        room_id=payload.auditorium_id,
        starts_at=payload.starts_at,
        base_price=payload.base_price,
        is_open_for_booking=payload.is_open_for_booking,
    )
    return ShowtimeResponse.from_domain(showtime)


@admin_router.delete("/{showtime_id}", status_code=204, summary="Xóa suất chiếu (ADMIN)")
def delete_showtime(showtime_id: UUID, actor: ActorDep, service: ShowtimeServiceDep) -> Response:
    service.delete_showtime(actor, showtime_id)
    return Response(status_code=204)
