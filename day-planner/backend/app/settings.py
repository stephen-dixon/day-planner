"""Central environment-based settings."""

import os
from functools import lru_cache
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Small settings object to keep this prototype dependency-light."""

    app_env: str = os.getenv("APP_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    secret_key: str = os.getenv("SECRET_KEY", "local-dev-only")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./dayplanner-dev.db")
    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]

    google_client_id: str | None = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret: str | None = os.getenv("GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str | None = os.getenv("GOOGLE_REDIRECT_URI")

    microsoft_client_id: str | None = os.getenv("MICROSOFT_CLIENT_ID")
    microsoft_client_secret: str | None = os.getenv("MICROSOFT_CLIENT_SECRET")
    microsoft_redirect_uri: str | None = os.getenv("MICROSOFT_REDIRECT_URI")
    microsoft_tenant: str = os.getenv("MICROSOFT_TENANT", "common")

    github_token: str | None = os.getenv("GITHUB_TOKEN")
    github_default_owner: str | None = os.getenv("GITHUB_DEFAULT_OWNER")
    github_default_repo: str | None = os.getenv("GITHUB_DEFAULT_REPO")

    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-5.5-mini")
    llm_api_key: str | None = os.getenv("LLM_API_KEY")
    llm_base_url: str | None = os.getenv("LLM_BASE_URL")

    oauth_state_secret: str = os.getenv("OAUTH_STATE_SECRET", "local-dev-only")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")
    timezone: str = os.getenv("APP_TIMEZONE", "Europe/London")
    catalog_dir: str = os.getenv("CATALOG_DIR", "catalogs")
    catalog_token_secret: str = os.getenv("CATALOG_TOKEN_SECRET", os.getenv("OAUTH_STATE_SECRET", "local-dev-only"))

    @property
    def redacted_database_url(self) -> str:
        parsed = urlparse(self.database_url)
        if parsed.password:
            return self.database_url.replace(parsed.password, "***")
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
