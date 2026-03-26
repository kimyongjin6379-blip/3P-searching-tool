"""Excel export endpoint."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.models import ExportRequest
from app.services.export_service import build_excel

router = APIRouter(prefix="/api", tags=["Export"])


@router.post("/export")
async def export_excel(body: ExportRequest):
    try:
        buf = build_excel(body)
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=research_results.xlsx"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel 생성 실패: {e}")
