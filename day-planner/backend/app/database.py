"""Database configuration and session helpers.

Each task catalog is a separate SQLite file. The default catalog keeps using
`planner.db`; password-protected catalogs live under `CATALOG_DIR`.
"""

from collections.abc import Generator
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, Request
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.catalogs import DEFAULT_CATALOG, catalog_db_path, catalog_from_token


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


@lru_cache
def get_engine(catalog_name: str = DEFAULT_CATALOG) -> Engine:
    """Return a cached SQLite engine for a catalog database file."""

    db_path = catalog_db_path(catalog_name)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )


def initialize_catalog(catalog_name: str = DEFAULT_CATALOG) -> None:
    """Create tables and apply temporary compatibility columns."""

    from app.schema_compat import ensure_sqlite_schema

    engine = get_engine(catalog_name)
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_schema(engine)


def selected_catalog(request: Request) -> str:
    """Resolve the selected catalog from the signed request token."""

    token = request.headers.get("X-Catalog-Token")
    if not token:
        return DEFAULT_CATALOG
    return catalog_from_token(token)


def get_db(catalog_name: str = Depends(selected_catalog)) -> Generator[Session, None, None]:
    """Provide a database session to FastAPI route dependencies."""

    initialize_catalog(catalog_name)
    session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=get_engine(catalog_name),
    )
    db = session_local()
    try:
        yield db
    finally:
        db.close()
