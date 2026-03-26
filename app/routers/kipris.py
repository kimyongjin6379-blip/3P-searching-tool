"""KIPRIS 한국 특허 검색 endpoint."""
from fastapi import APIRouter, HTTPException

from app.schemas.models import KiprisResponse, SearchQuery
from app.services.kipris_service import search_kipris

router = APIRouter(prefix="/api", tags=["KIPRIS"])


@router.post("/kipris", response_model=KiprisResponse)
async def kipris_search(body: SearchQuery):
    try:
        patents = await search_kipris(body.query, body.max_results)
        return KiprisResponse(count=len(patents), patents=patents)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"KIPRIS 검색 실패: {e}")
