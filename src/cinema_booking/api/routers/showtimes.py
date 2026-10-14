from datetime import date

from fastapi import APIRouter, Depends, Response, status

from cinema_booking.api.dependencies import Container, get_actor, get_container
from cinema_booking.api.schemas.showtime import (
    SeatAvailabilityResponse,
    SeatMapResponse,
    ShowtimeCreate,
    ShowtimeResponse,
)
from cinema_booking.domain.entities import Showtime, User
from cinema_booking.domain.enums import SeatType

router = APIRouter(prefix="/showtimes", tags=["showtimes"])


@router.get("", response_model=list[ShowtimeResponse])
def list_showtimes(
    movie_id: str | None = None,
    on_date: date | None = None,
    container: Container = Depends(get_container),
) -> list[Showtime]:
    return container.showtime_service().list(movie_id, on_date)


@router.get("/{showtime_id}/seats", response_model=SeatMapResponse)
def get_seat_map(
    showtime_id: str, container: Container = Depends(get_container)
) -> SeatMapResponse:
    showtime, seats, booked = container.showtime_service().seat_map(showtime_id)
    return SeatMapResponse(
        showtime_id=showtime.id,
        room_id=showtime.room_id,
        seats=[
            SeatAvailabilityResponse(
                id=seat.id,
                label=f"{seat.row_label}{seat.number}",
                seat_type=seat.seat_type,
                price=(
                    showtime.base_price
                    if seat.seat_type is SeatType.STANDARD
                    else showtime.base_price * 13 // 10
                ),
                status="BOOKED" if seat.id in booked else "AVAILABLE",
            )
            for seat in seats
        ],
    )


@router.post("", response_model=ShowtimeResponse, status_code=status.HTTP_201_CREATED)
def create_showtime(
    payload: ShowtimeCreate,
    actor: User = Depends(get_actor),
    container: Container = Depends(get_container),
) -> Showtime:
    return container.showtime_service().create(actor, **payload.model_dump())


@router.delete("/{showtime_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_showtime(
    showtime_id: str,
    actor: User = Depends(get_actor),
    container: Container = Depends(get_container),
) -> Response:
    container.showtime_service().delete(actor, showtime_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
