from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://identity:identity@localhost:5432/identity"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "dev-secret-change-me"
    cors_origins: str = "http://localhost:5173,http://localhost:5174"
    frontend_url: str = "http://localhost:5173"
    cookie_domain: str | None = None
    session_ttl_seconds: int = 60 * 60 * 24 * 7
    access_token_ttl_seconds: int = 60 * 60
    refresh_token_ttl_seconds: int = 60 * 60 * 24 * 30
    webauthn_rp_id: str = "localhost"
    webauthn_rp_name: str = "Identity Platform"
    webauthn_origins: str = "http://localhost:5173,http://localhost:5174"
    cookie_secure: bool = False
    cookie_name: str = "sid"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def webauthn_origin_list(self) -> list[str]:
        return [o.strip() for o in self.webauthn_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
