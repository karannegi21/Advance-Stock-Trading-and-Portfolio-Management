"""Application configuration using Pydantic Settings."""

from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="backend/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    ENV: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/stock_platform"
    )
    DATABASE_URL_UNPOOLED: str | None = None

    # Security & Auth
    JWT_SECRET: str = "default_secret_must_be_changed_in_production_32chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:5173,http://localhost:3000"

    # Market Simulator
    SIMULATOR_SPEED_SECONDS: int = 20
    SIMULATOR_AUTO_START: bool = True

    # Trading Fees
    BROKERAGE_FEE_RATE: float = 0.0003  # 0.03% per trade
    STT_FEE_RATE: float = 0.0010        # 0.10% STT on sell trades

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def sync_database_url(self) -> str:
        """Return synchronous database URL for psycopg/alembic, preferring unpooled for DDL."""
        url = self.DATABASE_URL_UNPOOLED or self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        if url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
        return url

    @property
    def async_database_url(self) -> str:
        """Return async database URL for asyncpg stripped of query params."""
        import urllib.parse
        url = self.DATABASE_URL
        parsed = urllib.parse.urlparse(url)
        return urllib.parse.urlunparse(parsed._replace(scheme="postgresql+asyncpg", query=""))


settings = Settings()
