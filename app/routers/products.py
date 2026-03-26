"""Web product research endpoint."""
from fastapi import APIRouter, HTTPException

from app.schemas.models import ProductSearchQuery, ProductsResponse
from app.services.products_service import search_products

router = APIRouter(prefix="/api", tags=["Products"])


@router.post("/products", response_model=ProductsResponse)
async def products_search(body: ProductSearchQuery):
    try:
        products = await search_products(body.query, body.max_results)
        return ProductsResponse(count=len(products), products=products)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"제품 조사 실패: {e}")
