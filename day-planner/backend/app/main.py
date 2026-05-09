"""FastAPI application entry point for the day planner API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import initialize_catalog
from app.routes import blocks, calendar, catalogs, github, metadata, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables when the app starts.

    This keeps the initial scaffold easy to run. Alembic migrations can replace
    this once the data model starts changing in a more controlled way.
    """

    initialize_catalog()
    yield


app = FastAPI(title="Day Planner API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)
app.include_router(blocks.router)
app.include_router(metadata.router)
app.include_router(calendar.router)
app.include_router(github.router)
app.include_router(catalogs.router)


@app.get("/health")
def health():
    return {"status": "ok"}
