from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response
from pydantic import Field, StringConstraints

from app.api.common.auth import ActorDep
from app.api.common.schemas import CamelModel, PageResponse, RequestModel
from app.api.dependencies import MovieServiceDep
from app.domain.auth.model import require_admin
from app.domain.catalog.model import Movie
from app.domain.ports import Page

router = APIRouter(prefix="/movies", tags=["catalog"])
admin_router = APIRouter(prefix="/admin/movies", tags=["admin"])


class MovieCreateRequest(RequestModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
    description: Annotated[str, StringConstraints(max_length=5000)] = ""
    duration_minutes: Annotated[int, Field(ge=1, le=600)]
    genre: Annotated[str, StringConstraints(max_length=100)] = ""
    age_rating: Annotated[str, StringConstraints(max_length=10)] = ""


class MovieUpdateRequest(MovieCreateRequest):
    """PUT replaces the whole movie: omitted optional fields are reset to their defaults."""


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


def _movie_page(result: Page[Movie]) -> PageResponse[MovieResponse]:
    return PageResponse[MovieResponse](
        items=[MovieResponse.from_domain(movie) for movie in result.items],
        page=result.page,
        page_size=result.page_size,
        total_items=result.total_items,
    )


QueryParam = Annotated[str | None, Query(max_length=100, description="Tìm theo tên phim")]
PageParam = Annotated[int, Query(ge=1)]
PageSizeParam = Annotated[int, Query(alias="pageSize", ge=1, le=100)]


@router.get("", summary="Danh sách phim (tìm theo tên, phân trang)")
def list_movies(
    service: MovieServiceDep,
    q: QueryParam = None,
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
) -> PageResponse[MovieResponse]:
    return _movie_page(service.list_movies(q, page, page_size))


@router.get("/{movie_id}", summary="Chi tiết phim")
def get_movie(movie_id: UUID, service: MovieServiceDep) -> MovieResponse:
    return MovieResponse.from_domain(service.get_movie(movie_id))


@admin_router.get("", summary="Danh sách phim cho quản trị (ADMIN)")
def admin_list_movies(
    actor: ActorDep,
    service: MovieServiceDep,
    q: QueryParam = None,
    page: PageParam = 1,
    page_size: PageSizeParam = 20,
) -> PageResponse[MovieResponse]:
    require_admin(actor)
    return _movie_page(service.list_movies(q, page, page_size))


@admin_router.post("", status_code=201, summary="Thêm phim (ADMIN)")
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


@admin_router.put("/{movie_id}", summary="Cập nhật phim (ADMIN)")
def update_movie(
    movie_id: UUID, payload: MovieUpdateRequest, actor: ActorDep, service: MovieServiceDep
) -> MovieResponse:
    movie = service.update_movie(
        actor,
        movie_id,
        title=payload.title,
        description=payload.description,
        duration_minutes=payload.duration_minutes,
        genre=payload.genre,
        age_rating=payload.age_rating,
    )
    return MovieResponse.from_domain(movie)


@admin_router.delete("/{movie_id}", status_code=204, summary="Xóa phim (ADMIN)")
def delete_movie(movie_id: UUID, actor: ActorDep, service: MovieServiceDep) -> Response:
    service.delete_movie(actor, movie_id)
    return Response(status_code=204)
