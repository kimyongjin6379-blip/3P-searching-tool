"""Pydantic models for all API request/response schemas."""
from pydantic import BaseModel, Field


# ── Common ──────────────────────────────────────────────
class TranslatedQuery(BaseModel):
    ko: str = Field(description="한국어 검색어")
    en: str = Field(description="영어 검색어")
    detected: str = Field(description="입력 감지 언어 (ko/en)")


class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, examples=["microbial culture peptone optimization"])
    max_results: int = Field(default=15, ge=1, le=100)


# ── PubMed ──────────────────────────────────────────────
class PubMedArticle(BaseModel):
    pmid: str
    title: str
    authors: list[str]
    pub_date: str
    abstract: str
    url: str = Field(default="", description="PubMed 논문 링크")


class PubMedResponse(BaseModel):
    count: int
    articles: list[PubMedArticle]


# ── Patents ─────────────────────────────────────────────
class PatentItem(BaseModel):
    publication_number: str
    title: str
    applicant: str
    abstract: str
    filing_date: str
    country_code: str
    url: str = Field(default="", description="Google Patents 링크")


class PatentsResponse(BaseModel):
    count: int
    patents: list[PatentItem]


# ── KIPRIS ──────────────────────────────────────────────
class KiprisItem(BaseModel):
    application_number: str = Field(description="출원번호")
    title: str = Field(description="발명의 명칭")
    applicant: str = Field(description="출원인")
    abstract: str = Field(description="요약")
    application_date: str = Field(description="출원일")
    url: str = Field(default="", description="KIPRIS 상세 링크")


class KiprisResponse(BaseModel):
    count: int
    patents: list[KiprisItem]


# ── Products ────────────────────────────────────────────
class ProductSearchQuery(BaseModel):
    query: str = Field(..., min_length=1, examples=["peptone for microbial culture"])
    max_results: int = Field(default=5, ge=1, le=20)


class ProductInfo(BaseModel):
    product_name: str = Field(description="제품명")
    manufacturer: str = Field(description="제조사")
    applicable_strains: str = Field(description="적용 가능 균주")
    peptone_enzyme_spec: str = Field(description="펩톤 및 효소 규격")
    key_features: str = Field(description="주요 특장점")
    source_url: str = Field(default="", description="출처 URL")


class ProductsResponse(BaseModel):
    count: int
    products: list[ProductInfo]


# ── Excel Export ────────────────────────────────────────
class ExportRequest(BaseModel):
    articles: list[PubMedArticle] = Field(default_factory=list)
    patents: list[PatentItem] = Field(default_factory=list)
    kipris: list[KiprisItem] = Field(default_factory=list)
    products: list[ProductInfo] = Field(default_factory=list)
