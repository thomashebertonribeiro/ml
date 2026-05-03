"""
Application settings loaded from environment variables and .env file.
Uses pydantic-settings for validation and type coercion.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the ML Category Web backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ------------------------------------------------------------------ #
    # Database
    # ------------------------------------------------------------------ #
    DATABASE_URL: str
    """Async PostgreSQL DSN, e.g. postgresql+asyncpg://user:pass@host/db"""

    # ------------------------------------------------------------------ #
    # Redis
    # ------------------------------------------------------------------ #
    REDIS_URL: str = "redis://redis:6379/0"
    """Redis connection URL used for cache and Celery broker."""

    # ------------------------------------------------------------------ #
    # Security
    # ------------------------------------------------------------------ #
    SECRET_KEY: str
    """Random secret used to sign JWT tokens. Must be at least 32 chars."""

    ACCESS_TOKEN_EXPIRE_SECONDS: int = 86400
    """JWT expiry in seconds (default: 24 h)."""

    # ------------------------------------------------------------------ #
    # Application
    # ------------------------------------------------------------------ #
    ENVIRONMENT: str = "development"
    """One of: development | staging | production"""

    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    """CORS allowed origins. Comma-separated string is also accepted."""

    # ------------------------------------------------------------------ #
    # Rate limiting
    # ------------------------------------------------------------------ #
    RATE_LIMIT_PER_MINUTE: int = 60
    """Maximum requests per minute per IP for the public API."""

    # ------------------------------------------------------------------ #
    # Validators
    # ------------------------------------------------------------------ #
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Accept both a JSON list and a comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ------------------------------------------------------------------ #
    # Celery
    # ------------------------------------------------------------------ #
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    """Celery broker URL (Redis)."""

    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"
    """Celery result backend URL (Redis)."""

    # ------------------------------------------------------------------ #
    # ML API
    # ------------------------------------------------------------------ #
    ML_API_BASE_URL: str = "https://api.mercadolibre.com"
    """Base URL for the Mercado Livre public API."""

    ML_REQUEST_DELAY_SECONDS: float = 0.3
    """Delay between consecutive ML API requests to avoid rate limiting."""

    ML_MAX_RETRIES: int = 3
    """Maximum number of retry attempts for ML API requests."""

    # ------------------------------------------------------------------ #
    # Validators
    # ------------------------------------------------------------------ #
    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_min_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("ENVIRONMENT")
    @classmethod
    def environment_valid(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v


# Module-level singleton — import this everywhere instead of instantiating Settings()
settings = Settings()
