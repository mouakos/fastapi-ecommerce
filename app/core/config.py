"""Application configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlmodel import Field


class Settings(BaseSettings):
    """Environment variables for the application."""

    # database
    database_url: str = Field(
        default="", alias="DATABASE_URL", description="Database connection URL"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
