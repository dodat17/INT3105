from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Movie:
    id: UUID
    title: str
    description: str
    duration_minutes: int
    genre: str
    age_rating: str
