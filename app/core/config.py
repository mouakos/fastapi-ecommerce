"""Application configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlmodel import Field


class AuthConfig(BaseSettings):
    """Authentication-related configuration settings."""

    jwt_secret_key: str = Field(
        default="",
        description="Secret key for JWT signing",
        alias="JWT_SECRET_KEY",
    )
    jwt_default_exp_minutes: int = Field(
        default=15,
        description="Access token expiration time in minutes",
        alias="JWT_DEFAULT_EXP_MINUTES",
    )
    jwt_algorithm: str = Field(
        default="HS256", description="JWT signing algorithm", alias="JWT_ALGORITHM"
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", frozen=True, extra="ignore"
    )


auth_settings = AuthConfig()


class Config(BaseSettings):
    """Environment variables for the application."""

    # database
    database_url: str = Field(
        default="", alias="DATABASE_URL", description="Database connection URL"
    )
    stripe_webhook_secret: str = Field(
        default="", description="Stripe webhook secret", alias="STRIPE_WEBHOOK_SECRET"
    )
    stripe_api_key: str = Field(default="", description="Stripe API key", alias="STRIPE_API_KEY")
    domain: str = Field(
        default="http://localhost:8080",
        description="Frontend application URL",
        alias="DOMAIN",
    )
    superuser_email: str = Field(..., description="Superuser email", alias="SUPERUSER_EMAIL")
    superuser_password: str = Field(
        ..., description="Superuser password", alias="SUPERUSER_PASSWORD"
    )
    cross_origin_urls: str | None = Field(
        default=None,
        description="Comma-separated list of allowed CORS origins",
        alias="CORS_ORIGINS",
    )
    environment: str = Field(
        default="development",
        description="Application environment (dev, prod)",
        alias="ENVIRONMENT",
    )
    app_version: str = Field(
        default="1.0.0", description="Application version", alias="APP_VERSION"
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", frozen=True, extra="ignore"
    )


settings = Config()
