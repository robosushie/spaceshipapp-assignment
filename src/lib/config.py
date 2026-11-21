from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    jwt_secret: str
    jwt_issuer: str = "spaceship"
    jwt_audience: str = "spaceship-web"
    anthropic_api_key: str = ""
    cors_origins: str = "http://localhost:5173"
    cookie_secure: bool = False
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    bootstrap_admin_email: str = ""
    bootstrap_admin_password: str = ""

    @field_validator("jwt_secret")
    @classmethod
    def jwt_secret_length(cls, value: str) -> str:
        if len(value.encode("utf-8")) < 32:
            raise ValueError("JWT_SECRET must be at least 32 bytes")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
