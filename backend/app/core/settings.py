from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = Field(alias="APP_NAME")
    app_version: str = Field(alias="APP_VERSION")
    app_env: Literal["development", "testing", "production"] = Field(alias="APP_ENV")
    debug: bool = Field(alias="DEBUG")

    # Server
    host: str = Field(alias="HOST")
    port: int = Field(alias="PORT")

    # PostgreSQL
    postgres_host: str = Field(alias="POSTGRES_HOST")
    postgres_port: int = Field(alias="POSTGRES_PORT")
    postgres_db: str = Field(alias="POSTGRES_DB")
    postgres_user: str = Field(alias="POSTGRES_USER")
    postgres_password: str = Field(alias="POSTGRES_PASSWORD")

    # Redis
    redis_host: str = Field(alias="REDIS_HOST")
    redis_port: int = Field(alias="REDIS_PORT")

    # Logging
    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = Field(alias="LOG_LEVEL")

    # GitLab
    gitlab_webhook_secret: str = Field(alias="GITLAB_WEBHOOK_SECRET")
    gitlab_url: str = Field(alias="GITLAB_URL")
    gitlab_access_token: str = Field(alias="GITLAB_ACCESS_TOKEN")

    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL",
    )

    chroma_path: str = Field(
        default="./data/chroma",
        alias="CHROMA_PATH",
    )

    gemini_api_key: str = Field(
    alias="GEMINI_API_KEY"
    )

    gemini_model: str = Field(
        default="gemini-2.5-flash",
        alias="GEMINI_MODEL",
    )

    # Slack Integration
    slack_bot_token: str = Field(
        default="",
        alias="SLACK_BOT_TOKEN",
    )
    slack_webhook_url: str = Field(
        default="",
        alias="SLACK_WEBHOOK_URL",
    )
    slack_default_channel: str = Field(
        default="#code-reviews",
        alias="SLACK_DEFAULT_CHANNEL",
    )

    # Google Sheets Analytics Integration
    google_sheets_spreadsheet_id: str = Field(
        default="",
        alias="GOOGLE_SHEETS_SPREADSHEET_ID",
    )
    google_sheets_credentials_file: str = Field(
        default="",
        alias="GOOGLE_SHEETS_CREDENTIALS_FILE",
    )
    google_sheets_webhook_url: str = Field(
        default="",
        alias="GOOGLE_SHEETS_WEBHOOK_URL",
    )

    @computed_field
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/"
            f"{self.postgres_db}"
        )

    @computed_field
    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
