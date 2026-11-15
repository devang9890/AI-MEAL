"""Read-only catalog endpoints for the health-preference selectors."""
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.health_catalog import ALLERGY_CATALOG, DISEASE_CATALOG

router = APIRouter(prefix="/api/health", tags=["Health preferences"])


class CatalogEntryOut(BaseModel):
    id: str
    name: str
    category: str
    kind: str


def _filter(catalog: List[dict], search: Optional[str], category: Optional[str]) -> List[dict]:
    result = catalog
    if category:
        result = [item for item in result if item["category"].lower() == category.lower()]
    if search:
        query = search.strip().lower()
        result = [item for item in result if query in item["name"].lower() or query in item["category"].lower()]
    return result


@router.get("/allergies", response_model=List[CatalogEntryOut])
def list_allergies(search: Optional[str] = Query(None), category: Optional[str] = Query(None)):
    """Allergies, intolerances, and sensitivities are labelled separately."""
    return _filter(ALLERGY_CATALOG, search, category)


@router.get("/diseases", response_model=List[CatalogEntryOut])
def list_diseases(search: Optional[str] = Query(None), category: Optional[str] = Query(None)):
    """Diet-relevant condition labels for member-level selection."""
    return _filter(DISEASE_CATALOG, search, category)
