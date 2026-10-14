from fastapi import APIRouter, Depends, Response, status

from cinema_booking.api.dependencies import Container, get_actor, get_container
from cinema_booking.api.schemas.booking import BookingCreate, BookingResponse
from cinema_booking.domain.entities import Booking, User

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    actor: User = Depends(get_actor),
    container: Container = Depends(get_container),
) -> Booking:
    return container.booking_service().create(actor, payload.showtime_id, payload.seat_ids)


@router.get("", response_model=list[BookingResponse])
def list_bookings(
    actor: User = Depends(get_actor), container: Container = Depends(get_container)
) -> list[Booking]:
    return container.booking_service().list(actor)


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: str,
    actor: User = Depends(get_actor),
    container: Container = Depends(get_container),
) -> Booking:
    return container.booking_service().get(actor, booking_id)


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_booking(
    booking_id: str,
    actor: User = Depends(get_actor),
    container: Container = Depends(get_container),
) -> Response:
    container.booking_service().cancel(actor, booking_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
