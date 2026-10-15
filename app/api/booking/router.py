from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response
from pydantic import Field

from app.api.common.auth import ActorDep
from app.api.common.schemas import CamelModel, PageResponse, RequestModel
from app.api.dependencies import BookingServiceDep
from app.domain.booking.model import Booking, BookingStatus
from app.domain.cinema.model import SeatType

router = APIRouter(tags=["booking"])


class CreateBookingRequest(RequestModel):
    showtime_id: UUID
    seat_ids: Annotated[list[UUID], Field(min_length=1, max_length=8)]


class BookingItemResponse(CamelModel):
    seat_id: UUID
    label: str
    seat_type: SeatType
    unit_price: int


class MovieRef(CamelModel):
    id: UUID
    title: str


class RoomRef(CamelModel):
    id: UUID
    name: str


class ShowtimeRef(CamelModel):
    id: UUID
    starts_at: datetime
    ends_at: datetime
    base_price: int


class BookingResponse(CamelModel):
    id: UUID
    showtime_id: UUID
    status: BookingStatus
    created_at: datetime
    expires_at: datetime
    confirmed_at: datetime | None
    cancelled_at: datetime | None
    total_amount: int
    currency: str = "VND"
    booking_code: str | None
    items: list[BookingItemResponse]

    @classmethod
    def from_domain(cls, booking: Booking) -> "BookingResponse":
        return cls(
            id=booking.id,
            showtime_id=booking.showtime_id,
            status=booking.status,
            created_at=booking.created_at,
            expires_at=booking.expires_at,
            confirmed_at=booking.confirmed_at,
            cancelled_at=booking.cancelled_at,
            total_amount=booking.total_amount,
            booking_code=booking.booking_code,
            items=[
                BookingItemResponse(
                    seat_id=item.seat_id,
                    label=f"{item.row_label}{item.number}",
                    seat_type=item.seat_type,
                    unit_price=item.unit_price,
                )
                for item in booking.items
            ],
        )


class BookingDetailResponse(BookingResponse):
    movie: MovieRef
    room: RoomRef
    showtime: ShowtimeRef


@router.post("/bookings", status_code=201, summary="Giữ ghế")
def create_booking(
    payload: CreateBookingRequest, actor: ActorDep, service: BookingServiceDep, response: Response
) -> BookingResponse:
    booking = service.create(actor, payload.showtime_id, payload.seat_ids)
    response.headers["Location"] = f"/api/v1/bookings/{booking.id}"
    return BookingResponse.from_domain(booking)


@router.get("/me/bookings", summary="Booking của tôi")
def list_bookings(
    actor: ActorDep,
    service: BookingServiceDep,
    status: Annotated[BookingStatus | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
) -> PageResponse[BookingResponse]:
    result = service.list(actor, status, page, page_size)
    return PageResponse[BookingResponse](
        items=[BookingResponse.from_domain(item) for item in result.items],
        page=result.page,
        page_size=result.page_size,
        total_items=result.total_items,
    )


@router.get("/bookings/{booking_id}", summary="Chi tiết booking")
def get_booking(
    booking_id: UUID, actor: ActorDep, service: BookingServiceDep
) -> BookingDetailResponse:
    details = service.details(actor, booking_id)
    booking = BookingResponse.from_domain(details.booking)
    return BookingDetailResponse(
        **booking.model_dump(),
        movie=MovieRef(id=details.movie.id, title=details.movie.title),
        room=RoomRef(id=details.room.id, name=details.room.name),
        showtime=ShowtimeRef(
            id=details.showtime.id,
            starts_at=details.showtime.starts_at,
            ends_at=details.showtime.ends_at,
            base_price=details.showtime.base_price,
        ),
    )


@router.post("/bookings/{booking_id}/confirm", summary="Xác nhận booking")
def confirm_booking(
    booking_id: UUID, actor: ActorDep, service: BookingServiceDep
) -> BookingResponse:
    return BookingResponse.from_domain(service.confirm(actor, booking_id))


@router.delete("/bookings/{booking_id}", status_code=204, summary="Hủy hold")
def cancel_booking(booking_id: UUID, actor: ActorDep, service: BookingServiceDep) -> Response:
    service.cancel(actor, booking_id)
    return Response(status_code=204)
