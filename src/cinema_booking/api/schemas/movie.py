from pydantic import BaseModel, ConfigDict, Field


class MovieCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    duration_minutes: int = Field(gt=0)
    genre: str = Field(min_length=1, max_length=100)
    age_rating: str = Field(min_length=1, max_length=20)
    description: str | None = None


class MovieResponse(MovieCreate):
    id: str

    model_config = ConfigDict(from_attributes=True)
