from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    app_name: str = "Movie Booking"
    app_log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://movie_booking:movie_booking@localhost/movie_booking"
    jwt_secret: str = Field(default="development-only-secret-change-me-123456")
    jwt_algorithm: str = "HS256"
    jwt_ttl_seconds: int = 3600
    bcrypt_rounds: int = 12
    hold_ttl_seconds: int = 300
    hold_max_active_per_showtime: int = 2
    hold_max_active_total: int = 5
    db_pool_size: int = 10
    cinema_timezone: str = "Asia/Ho_Chi_Minh"


@lru_cache
def get_settings() -> Settings:
    return Settings()
