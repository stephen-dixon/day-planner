"""Task catalog routes.

Catalogs are separate SQLite database files. Loading a catalog returns a signed
token that the frontend sends on normal API requests.
"""

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from app.catalogs import catalog_from_token, create_catalog, issue_catalog_token, list_catalogs
from app.database import initialize_catalog

router = APIRouter(prefix="/catalogs", tags=["catalogs"])


class CatalogCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=4, max_length=200)


class CatalogLoad(BaseModel):
    name: str
    password: str = ""


@router.get("")
def get_catalogs():
    return list_catalogs()


@router.post("")
def post_catalog(payload: CatalogCreate):
    catalog = create_catalog(payload.name, payload.password)
    initialize_catalog(catalog["name"])
    return catalog


@router.post("/load")
def load_catalog(payload: CatalogLoad):
    token = issue_catalog_token(payload.name, payload.password)
    catalog_name = catalog_from_token(token)
    initialize_catalog(catalog_name)
    return {"name": catalog_name, "token": token}


@router.get("/current")
def current_catalog(x_catalog_token: str | None = Header(default=None)):
    name = catalog_from_token(x_catalog_token) if x_catalog_token else "default"
    return {"name": name}
