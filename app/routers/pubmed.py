"""PubMed search endpoint."""
from fastapi import APIRouter, HTTPException

from app.schemas.models import PubMedResponse, SearchQuery
from app.services.pubmed_service import search_pubmed

router = APIRouter(prefix="/api", tags=["PubMed"])


@router.post("/pubmed", response_model=PubMedResponse)
async def pubmed_search(body: SearchQuery):
    try:
        articles = await search_pubmed(body.query, body.max_results)
        return PubMedResponse(count=len(articles), articles=articles)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"PubMed 검색 실패: {e}")
