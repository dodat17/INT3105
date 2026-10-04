from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response
from pydantic import Field, StringConstraints

from app.api.common.auth import ActorDep
from app.api.common.schemas import CamelModel, PageResponse, RequestModel
from app.api.dependencies import MovieServiceDep
from app.domain.catalog.model import Movie

router = APIRouter(prefix="/movies", tags=["catalog"])


class MovieCreateRequest(RequestModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
    description: Annotated[str, StringConstraints(max_length=5000)] = ""
    duration_minutes: Annotated[int, Field(ge=1, le=600)]
    genre: Annotated[str, StringConstraints(max_length=100)] = ""
    age_rating: Annotated[str, StringConstraints(max_length=10)] = ""


class MovieResponse(CamelModel):
    id: UUID
    title: str
    description: str
    duration_minutes: int
    genre: str
    age_rating: str

    @classmethod
    def from_domain(cls, movie: Movie) -> "MovieResponse":
        return cls(
            id=movie.id,
            title=movie.title,
            description=movie.description,
            duration_minutes=movie.duration_minutes,
            genre=movie.genre,
            age_rating=movie.age_rating,
        )


@router.get("", summary="Danh sách phim (tìm theo tên, phân trang)")
def list_movies(
    service: MovieServiceDep,
    q: Annotated[str | None, Query(max_length=100, description="Tìm theo tên phim")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
) -> PageResponse[MovieResponse]:
    result = service.list_movies(q, page, page_size)
    return PageResponse[MovieResponse](
        items=[MovieResponse.from_domain(movie) for movie in result.items],
        page=result.page,
        page_size=result.page_size,
        total_items=result.total_items,
    )


@router.get("/{movie_id}", summary="Chi tiết phim")
def get_movie(movie_id: UUID, service: MovieServiceDep) -> MovieResponse:
    return MovieResponse.from_domain(service.get_movie(movie_id))


@router.post("", status_code=201, summary="Thêm phim (ADMIN)")
def create_movie(
    payload: MovieCreateRequest, actor: ActorDep, service: MovieServiceDep
) -> MovieResponse:
    movie = service.create_movie(
        actor,
        title=payload.title,
        description=payload.description,
        duration_minutes=payload.duration_minutes,
        genre=payload.genre,
        age_rating=payload.age_rating,
    )
    return MovieResponse.from_domain(movie)


@router.delete("/{movie_id}", status_code=204, summary="Xóa phim (ADMIN)")
def delete_movie(movie_id: UUID, actor: ActorDep, service: MovieServiceDep) -> Response:
    service.delete_movie(actor, movie_id)
    return Response(status_code=204)
