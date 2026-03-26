"""FastAPI application entry point."""
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routers import export, kipris, patents, products, pubmed, translate

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS

app = FastAPI(
    title="3P Research Searching Tool",
    description="PubMed 논문, Google Patents 특허, 웹 제품 정보를 통합 검색하고 Excel로 추출하는 API",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(pubmed.router)
app.include_router(patents.router)
app.include_router(kipris.router)
app.include_router(products.router)
app.include_router(translate.router)
app.include_router(export.router)

# Serve frontend
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@app.get("/", response_class=HTMLResponse)
async def root():
    index = FRONTEND_DIR / "index.html"
    return HTMLResponse(index.read_text(encoding="utf-8"))

