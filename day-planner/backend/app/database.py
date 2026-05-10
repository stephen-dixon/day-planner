"""Database configuration and session helpers.

Each task catalog is a separate SQLite file. The default catalog uses
`DATABASE_URL`; password-protected catalogs live under `CATALOG_DIR`.
"""

from collections.abc import Generator
from functools import lru_cache
from pathlib import Path

from fastapi import Depends, Request
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.catalogs import DEFAULT_CATALOG, catalog_database_url, catalog_db_path, catalog_from_token


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


@lru_cache
def get_engine(catalog_name: str = DEFAULT_CATALOG) -> Engine:
    """Return a cached SQLite engine for a catalog database file."""

    db_path = catalog_db_path(catalog_name)
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(
        catalog_database_url(catalog_name),
        connect_args={"check_same_thread": False},
    )


def initialize_catalog(catalog_name: str = DEFAULT_CATALOG) -> None:
    """Create tables and apply temporary compatibility columns."""

    from app.schema_compat import ensure_sqlite_schema

    engine = get_engine(catalog_name)
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_schema(engine)
    seed_demo_tasks(engine)


def seed_demo_tasks(engine: Engine) -> None:
    """Create a few planning-cockpit examples for empty development databases."""

    from sqlalchemy import func, select

    from app.models import Task

    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = session_local()
    try:
        if db.scalar(select(func.count(Task.id))) != 0:
            return
        db.add_all(
            [
                Task(
                    title="Plan presentation structure",
                    status="active",
                    estimated_minutes=45,
                    task_phase="clarifying",
                    clarity_progress=30,
                    activation_cost="medium",
                    focus_required="medium",
                    context="planning",
                    starter_step="Open a blank outline and write three possible section headings.",
                ),
                Task(
                    title="Write report methods section",
                    status="active",
                    estimated_minutes=90,
                    task_phase="executable",
                    activation_cost="high",
                    focus_required="deep",
                    energy_required="high",
                    context="writing",
                    starter_step="Open the draft and write one bad bullet.",
                ),
                Task(
                    title="Tidy inbox",
                    status="active",
                    estimated_minutes=25,
                    task_phase="executable",
                    activation_cost="low",
                    focus_required="shallow",
                    energy_required="low",
                    context="admin",
                ),
            ]
        )
        db.commit()
    finally:
        db.close()


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
