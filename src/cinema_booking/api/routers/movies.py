from fastapi import APIRouter, Depends, Query, Response, status

from cinema_booking.api.dependencies import Container, get_actor, get_container
from cinema_booking.api.schemas.movie import MovieCreate, MovieResponse
from cinema_booking.domain.entities import Movie, User

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("", response_model=list[MovieResponse])
def list_movies(
    search: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    container: Container = Depends(get_container),
) -> list[Movie]:
    return container.movie_service().list(search, offset, limit)


@router.get("/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: str, container: Container = Depends(get_container)) -> Movie:
    return container.movie_service().get(movie_id)


@router.post("", response_model=MovieResponse, status_code=status.HTTP_201_CREATED)
def create_movie(
    payload: MovieCreate,
    actor: User = Depends(get_actor),
    container: Container = Depends(get_container),
) -> Movie:
    return container.movie_service().create(actor, **payload.model_dump())


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(
    movie_id: str,
    actor: User = Depends(get_actor),
    container: Container = Depends(get_container),
) -> Response:
    container.movie_service().delete(actor, movie_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
