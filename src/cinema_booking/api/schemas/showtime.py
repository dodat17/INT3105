from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from cinema_booking.domain.enums import SeatType


class ShowtimeCreate(BaseModel):
    movie_id: str
    room_id: str
    starts_at: datetime
    base_price: int = Field(gt=0)


class ShowtimeResponse(BaseModel):
    id: str
    movie_id: str
    room_id: str
    starts_at: datetime
    ends_at: datetime
    base_price: int

    model_config = ConfigDict(from_attributes=True)


class SeatAvailabilityResponse(BaseModel):
    id: str
    label: str
    seat_type: SeatType
    price: int
    status: str


class SeatMapResponse(BaseModel):
    showtime_id: str
    room_id: str
    seats: list[SeatAvailabilityResponse]
