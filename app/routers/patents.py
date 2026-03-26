"""Google Patents search endpoint."""
from fastapi import APIRouter, HTTPException

from app.schemas.models import PatentsResponse, SearchQuery
from app.services.patents_service import search_patents

router = APIRouter(prefix="/api", tags=["Patents"])


@router.post("/patents", response_model=PatentsResponse)
async def patents_search(body: SearchQuery):
    try:
        patents = await search_patents(body.query, body.max_results)
        return PatentsResponse(count=len(patents), patents=patents)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"특허 검색 실패: {e}")
