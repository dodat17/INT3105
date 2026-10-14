from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from cinema_booking.domain.enums import BookingStatus


class BookingCreate(BaseModel):
    showtime_id: str
    seat_ids: list[str] = Field(min_length=1, max_length=8)


class TicketResponse(BaseModel):
    id: str
    booking_id: str
    showtime_id: str
    seat_id: str
    price: int

    model_config = ConfigDict(from_attributes=True)


class BookingResponse(BaseModel):
    id: str
    user_id: str
    showtime_id: str
    status: BookingStatus
    total_price: int
    created_at: datetime
    tickets: list[TicketResponse]

    model_config = ConfigDict(from_attributes=True)
