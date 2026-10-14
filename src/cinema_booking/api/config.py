from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./cinema.db"
    jwt_secret: str = "development-only-change-me"
    jwt_expires_minutes: int = 60
    bcrypt_rounds: int = 12
    db_pool_size: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
