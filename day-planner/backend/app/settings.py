"""Environment-based settings for external integrations."""

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Small settings object to keep this prototype dependency-light."""

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

    oauth_state_secret: str = os.getenv("OAUTH_STATE_SECRET", "local-dev-only")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://127.0.0.1:5173")
    timezone: str = os.getenv("APP_TIMEZONE", "Europe/London")
    catalog_dir: str = os.getenv("CATALOG_DIR", "catalogs")
    catalog_token_secret: str = os.getenv("CATALOG_TOKEN_SECRET", os.getenv("OAUTH_STATE_SECRET", "local-dev-only"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
