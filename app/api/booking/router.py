from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query, Response
from pydantic import Field, field_validator

from app.api.common.auth import ActorDep
from app.api.common.schemas import CamelModel, PageResponse, RequestModel
from app.api.dependencies import BookingServiceDep
from app.domain.booking.model import Booking, BookingDetail, BookingStatus, Ticket

router = APIRouter(tags=["booking"])


class BookingCreateRequest(RequestModel):
    showtime_id: UUID
    seat_ids: Annotated[list[UUID], Field(min_length=1, max_length=8)]

    @field_validator("seat_ids")
    @classmethod
    def reject_duplicate_seats(cls, seat_ids: list[UUID]) -> list[UUID]:
        if len(set(seat_ids)) != len(seat_ids):
            raise ValueError("Danh sách ghế không được trùng lặp.")
        return seat_ids


class TicketResponse(CamelModel):
    seat_id: UUID
    unit_price: int

    @classmethod
    def from_domain(cls, ticket: Ticket) -> "TicketResponse":
        return cls(seat_id=ticket.seat_id, unit_price=ticket.unit_price)


class BookingResponse(CamelModel):
    id: UUID
    showtime_id: UUID
    status: BookingStatus
    items: list[TicketResponse]
    total_amount: int
    currency: Literal["VND"] = "VND"
    created_at: datetime
    expires_at: datetime
    confirmed_at: datetime | None
    cancelled_at: datetime | None
    booking_code: str | None

    @classmethod
    def from_domain(cls, booking: Booking) -> "BookingResponse":
        return cls(
            id=booking.id,
            showtime_id=booking.showtime_id,
            status=booking.status,
            items=[TicketResponse.from_domain(ticket) for ticket in booking.tickets],
            total_amount=booking.total_amount,
            created_at=booking.created_at,
            expires_at=booking.expires_at,
            confirmed_at=booking.confirmed_at,
            cancelled_at=booking.cancelled_at,
            booking_code=booking.booking_code,
        )


class MovieRef(CamelModel):
    id: UUID
    title: str


class ShowtimeRef(CamelModel):
    id: UUID
    starts_at: datetime
    ends_at: datetime


class RoomRef(CamelModel):
    id: UUID
    name: str


class BookedSeatResponse(CamelModel):
    seat_id: UUID
    row_label: str
    number: int
    unit_price: int


class BookingDetailResponse(BookingResponse):
    movie: MovieRef
    showtime: ShowtimeRef
    room: RoomRef
    seats: list[BookedSeatResponse]

    @classmethod
    def from_detail(cls, detail: BookingDetail) -> "BookingDetailResponse":
        booking = detail.booking
        prices = {ticket.seat_id: ticket.unit_price for ticket in booking.tickets}
        return cls(
            **BookingResponse.from_domain(booking).model_dump(),
            movie=MovieRef(id=detail.movie.id, title=detail.movie.title),
            showtime=ShowtimeRef(
                id=detail.showtime.id,
                starts_at=detail.showtime.starts_at,
                ends_at=detail.showtime.ends_at,
            ),
            room=RoomRef(id=detail.room.id, name=detail.room.name),
            seats=[
                BookedSeatResponse(
                    seat_id=seat.id,
                    row_label=seat.row_label,
                    number=seat.number,
                    unit_price=prices[seat.id],
                )
                for seat in detail.seats
            ],
        )


@router.post("/bookings", status_code=201, summary="Tạo booking và giữ ghế")
def create_booking(
    payload: BookingCreateRequest,
    response: Response,
    actor: ActorDep,
    service: BookingServiceDep,
) -> BookingResponse:
    booking = service.create_booking(actor, payload.showtime_id, payload.seat_ids)
    response.headers["Location"] = f"/api/v1/bookings/{booking.id}"
    return BookingResponse.from_domain(booking)


@router.get("/me/bookings", summary="Danh sách booking của tôi")
def list_my_bookings(
    actor: ActorDep,
    service: BookingServiceDep,
    status: BookingStatus | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
) -> PageResponse[BookingResponse]:
    result = service.list_my_bookings(actor, status, page, page_size)
    return PageResponse[BookingResponse](
        items=[BookingResponse.from_domain(booking) for booking in result.items],
        page=result.page,
        page_size=result.page_size,
        total_items=result.total_items,
    )


@router.get("/bookings/{booking_id}", summary="Chi tiết booking")
def get_booking(
    booking_id: UUID, actor: ActorDep, service: BookingServiceDep
) -> BookingDetailResponse:
    return BookingDetailResponse.from_detail(service.get_booking_detail(actor, booking_id))


@router.post("/bookings/{booking_id}/confirm", summary="Xác nhận booking")
def confirm_booking(
    booking_id: UUID, actor: ActorDep, service: BookingServiceDep
) -> BookingResponse:
    return BookingResponse.from_domain(service.confirm_booking(actor, booking_id))


@router.delete("/bookings/{booking_id}", status_code=204, summary="Hủy booking")
def cancel_booking(booking_id: UUID, actor: ActorDep, service: BookingServiceDep) -> Response:
    service.cancel_booking(actor, booking_id)
    return Response(status_code=204)
