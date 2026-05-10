"""Task catalog registry and password/token helpers."""

import hashlib
import json
import re
import secrets
from pathlib import Path
from urllib.parse import unquote
from typing import Any

from fastapi import HTTPException
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.settings import get_settings

DEFAULT_CATALOG = "default"
CATALOG_TOKEN_MAX_AGE = 60 * 60 * 24 * 30


def catalog_root() -> Path:
    root = Path(get_settings().catalog_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def registry_path() -> Path:
    return catalog_root() / "catalogs.json"


def catalog_db_path(name: str) -> Path:
    if name == DEFAULT_CATALOG:
        return sqlite_path_from_url(get_settings().database_url)
    return catalog_root() / f"{safe_catalog_name(name)}.db"


def catalog_database_url(name: str) -> str:
    if name == DEFAULT_CATALOG:
        return get_settings().database_url
    return f"sqlite:///{catalog_db_path(name)}"


def sqlite_path_from_url(database_url: str) -> Path:
    if database_url == "sqlite:///:memory:":
        raise RuntimeError("In-memory SQLite is not supported for persistent planner catalogs.")
    if database_url.startswith("sqlite:////"):
        raw_path = "/" + database_url.removeprefix("sqlite:////")
    elif database_url.startswith("sqlite:///"):
        raw_path = database_url.removeprefix("sqlite:///")
    else:
        raise RuntimeError("Only SQLite DATABASE_URL values are supported by this app.")
    if not raw_path:
        raise RuntimeError("SQLite DATABASE_URL must include a database path.")
    return Path(unquote(raw_path))


def list_catalogs() -> list[dict[str, Any]]:
    registry = read_registry()
    names = sorted({DEFAULT_CATALOG, *registry.keys()})
    return [
        {
            "name": name,
            "locked": name != DEFAULT_CATALOG,
            "db_path": str(catalog_db_path(name)),
        }
        for name in names
    ]


def create_catalog(name: str, password: str) -> dict[str, Any]:
    name = safe_catalog_name(name)
    if name == DEFAULT_CATALOG:
        raise HTTPException(status_code=400, detail="default catalog already exists")
    if len(password) < 4:
        raise HTTPException(status_code=422, detail="Password must be at least 4 characters")

    registry = read_registry()
    if name in registry:
        raise HTTPException(status_code=409, detail="Catalog already exists")

    salt = secrets.token_hex(16)
    registry[name] = {
        "salt": salt,
        "password_hash": hash_password(password, salt),
        "db_path": str(catalog_db_path(name)),
    }
    write_registry(registry)
    return {"name": name, "locked": True, "db_path": str(catalog_db_path(name))}


def issue_catalog_token(name: str, password: str) -> str:
    name = safe_catalog_name(name)
    if name == DEFAULT_CATALOG:
        return signer().dumps({"catalog": DEFAULT_CATALOG})

    registry = read_registry()
    record = registry.get(name)
    if record is None:
        raise HTTPException(status_code=404, detail="Catalog not found")
    expected = record["password_hash"]
    actual = hash_password(password, record["salt"])
    if not secrets.compare_digest(expected, actual):
        raise HTTPException(status_code=401, detail="Incorrect catalog password")
    return signer().dumps({"catalog": name})


def catalog_from_token(token: str) -> str:
    try:
        payload = signer().loads(token, max_age=CATALOG_TOKEN_MAX_AGE)
    except BadSignature as exc:
        raise HTTPException(status_code=401, detail="Invalid catalog token") from exc

    name = safe_catalog_name(payload.get("catalog", DEFAULT_CATALOG))
    if name != DEFAULT_CATALOG and name not in read_registry():
        raise HTTPException(status_code=404, detail="Catalog not found")
    return name


def safe_catalog_name(name: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip()).strip("-").lower()
    if not clean:
        raise HTTPException(status_code=422, detail="Catalog name is required")
    return clean


def read_registry() -> dict[str, Any]:
    path = registry_path()
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def write_registry(registry: dict[str, Any]) -> None:
    registry_path().write_text(json.dumps(registry, indent=2, sort_keys=True))


def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()


def signer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(get_settings().catalog_token_secret)
