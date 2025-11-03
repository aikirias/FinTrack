from functools import lru_cache
from typing import List

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    database_url: str = Field(..., alias="DATABASE_URL")
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60 * 24, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    cookie_domain: str | None = Field(default=None, alias="COOKIE_DOMAIN")
    cors_origins: List[str] = Field(default_factory=list, alias="CORS_ORIGINS")

    scheduler_timezone: str = Field(default="UTC", alias="SCHEDULER_TIMEZONE")
    rate_refresh_hour: int = Field(default=3, alias="RATE_REFRESH_HOUR")
    rate_refresh_minute: int = Field(default=0, alias="RATE_REFRESH_MINUTE")

    dolar_api_url: HttpUrl = Field(default="https://dolarapi.com/v1/dolares", alias="DOLAR_API_URL")
    coingecko_api_url: HttpUrl = Field(
        default="https://api.coingecko.com/api/v3/simple/price", alias="COINGECKO_API_URL"
    )

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: str | List[str]) -> List[str]:
        if isinstance(value, list):
            return value
        if not value:
            return []
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
