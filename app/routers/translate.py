"""Query translation endpoint — called once, result shared across searches."""
from fastapi import APIRouter, HTTPException

from app.schemas.models import TranslatedQuery
from app.services.translate_service import translate_query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api", tags=["Translate"])


class TranslateRequest(BaseModel):
    query: str = Field(..., min_length=1)


@router.post("/translate", response_model=TranslatedQuery)
async def translate(body: TranslateRequest):
    try:
        result = await translate_query(body.query)
        return TranslatedQuery(**result)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"번역 실패: {e}")
