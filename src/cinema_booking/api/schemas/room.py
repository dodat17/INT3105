from pydantic import BaseModel, ConfigDict, Field


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    rows: int = Field(ge=1, le=26)
    cols: int = Field(ge=1, le=100)
    vip_rows: list[int] = Field(default_factory=list)


class RoomResponse(BaseModel):
    id: str
    name: str
    rows: int
    cols: int

    model_config = ConfigDict(from_attributes=True)
