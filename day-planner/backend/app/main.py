"""FastAPI application entry point for the day planner API."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import initialize_catalog
from app.routes import ai, analytics, blocks, calendar, catalogs, github, metadata, steps, support, tasks, work_sessions
from app.settings import get_settings

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("dayplanner")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables when the app starts.

    This keeps the initial scaffold easy to run. Alembic migrations can replace
    this once the data model starts changing in a more controlled way.
    """

    logger.info(
        "Starting dayplanner app_env=%s database_url=%s",
        settings.app_env,
        settings.redacted_database_url,
    )
    initialize_catalog()
    yield


app = FastAPI(title="Day Planner API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def log_unhandled_error(request: Request, exc: Exception):
    logger.exception("Unhandled API error path=%s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


def include_api_routes(prefix: str = "", include_in_schema: bool = True) -> None:
    app.include_router(tasks.router, prefix=prefix, include_in_schema=include_in_schema)
    app.include_router(steps.router, prefix=prefix, include_in_schema=include_in_schema)
    app.include_router(blocks.router, prefix=prefix, include_in_schema=include_in_schema)
    app.include_router(work_sessions.router, prefix=prefix, include_in_schema=include_in_schema)
    app.include_router(support.router, prefix=prefix, include_in_schema=include_in_schema)
    app.include_router(ai.router, prefix=prefix, include_in_schema=include_in_schema)
    app.include_router(analytics.router, prefix=prefix, include_in_schema=include_in_schema)
    app.include_router(metadata.router, prefix=prefix, include_in_schema=include_in_schema)
    app.include_router(calendar.router, prefix=prefix, include_in_schema=include_in_schema)
    app.include_router(github.router, prefix=prefix, include_in_schema=include_in_schema)
    app.include_router(catalogs.router, prefix=prefix, include_in_schema=include_in_schema)


include_api_routes(prefix="/api")
include_api_routes(include_in_schema=False)


@app.get("/health")
def health():
    return {"status": "ok", "app": "dayplanner"}


@app.get("/api/health")
def api_health():
    return health()


@app.get("/api/version")
def api_version():
    return {"app": "dayplanner", "version": "0.1.0", "environment": settings.app_env}
