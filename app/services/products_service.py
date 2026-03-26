"""Web product research: DuckDuckGo (primary) → Brave (fallback) → scrape → GPT-4o-mini extraction."""
import asyncio
import json
import logging
import random
import time

import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import DuckDuckGoSearchException, RatelimitException
from openai import AsyncOpenAI

from app.core.config import settings
from app.schemas.models import ProductInfo

logger = logging.getLogger(__name__)

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
]

BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"

EXTRACTION_PROMPT = """\
You are a structured data extractor specialising in biotech products.
From the text below, extract ALL products you can identify.
For each product return a JSON object with exactly these keys (in Korean descriptions where applicable):
- product_name: 제품명
- manufacturer: 제조사
- applicable_strains: 적용 가능 균주
- peptone_enzyme_spec: 펩톤 및 효소 규격
- key_features: 주요 특장점

If a field is unknown, use "N/A".
Return a JSON array of objects. Output ONLY valid JSON, no markdown.
"""


# ── Search Engines ──────────────────────────────────────


async def _search_duckduckgo(query: str, max_results: int) -> list[dict]:
    """DuckDuckGo 검색 (1차 시도, 재시도 1회)."""
    loop = asyncio.get_running_loop()

    def _ddg() -> list[dict]:
        for attempt in range(2):
            try:
                ddgs = DDGS()
                results = list(ddgs.text(query, max_results=max_results))
                return [
                    {"url": r.get("href", ""), "title": r.get("title", "")}
                    for r in results
                ]
            except (RatelimitException, DuckDuckGoSearchException) as e:
                if attempt == 0:
                    wait = 5 + random.uniform(1, 3)
                    logger.warning(f"DuckDuckGo rate-limited, {wait:.1f}s 후 재시도...")
                    time.sleep(wait)
                else:
                    logger.warning(f"DuckDuckGo 최종 실패: {e}")
                    return []
            except Exception as e:
                logger.error(f"DuckDuckGo 오류: {e}")
                return []
        return []

    return await loop.run_in_executor(None, _ddg)


async def _search_brave(query: str, max_results: int) -> list[dict]:
    """Brave Search API (폴백)."""
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": settings.brave_search_api_key,
    }
    params = {"q": query, "count": min(max_results, 20)}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(BRAVE_SEARCH_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

    return [
        {"url": item.get("url", ""), "title": item.get("title", "")}
        for item in data.get("web", {}).get("results", [])
    ]


async def _search_urls(query: str, max_results: int) -> list[dict]:
    """DuckDuckGo 우선 → 실패 시 Brave 폴백."""
    # 1차: DuckDuckGo
    results = await _search_duckduckgo(query, max_results)
    if results:
        logger.info(f"DuckDuckGo 검색 성공: {len(results)}건")
        return results

    # 2차: Brave 폴백
    logger.info("DuckDuckGo 실패 → Brave Search 폴백")
    try:
        results = await _search_brave(query, max_results)
        if results:
            logger.info(f"Brave 검색 성공: {len(results)}건")
            return results
    except Exception as e:
        logger.error(f"Brave 검색도 실패: {e}")

    return []


# ── Scraping & LLM ──────────────────────────────────────


async def _scrape_page(url: str) -> str:
    """Scrape visible text from a single URL with random User-Agent and 10s timeout."""
    headers = {"User-Agent": random.choice(_USER_AGENTS)}
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    return text[:6000]


async def _extract_with_llm(text: str, source_url: str) -> list[ProductInfo]:
    """Send scraped text to GPT-4o-mini and parse structured output."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": text},
        ],
        temperature=0,
    )

    raw = response.choices[0].message.content or "[]"
    parsed = json.loads(raw)

    if isinstance(parsed, dict):
        items = parsed.get("products", list(parsed.values())[0] if parsed else [])
    elif isinstance(parsed, list):
        items = parsed
    else:
        items = []

    products: list[ProductInfo] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        products.append(
            ProductInfo(
                product_name=item.get("product_name", "N/A"),
                manufacturer=item.get("manufacturer", "N/A"),
                applicable_strains=item.get("applicable_strains", "N/A"),
                peptone_enzyme_spec=item.get("peptone_enzyme_spec", "N/A"),
                key_features=item.get("key_features", "N/A"),
                source_url=source_url,
            )
        )
    return products


# ── Main Pipeline ───────────────────────────────────────


async def search_products(query: str, max_results: int = 5) -> list[ProductInfo]:
    """Full pipeline: DuckDuckGo/Brave → scrape → LLM extract."""
    search_results = await _search_urls(query, max_results)

    if not search_results:
        return []

    all_products: list[ProductInfo] = []

    for i, result in enumerate(search_results):
        url = result.get("url", "")
        if not url:
            continue
        # Stagger requests to avoid DNS/rate issues
        if i > 0:
            await asyncio.sleep(0.5)
        for attempt in range(2):
            try:
                text = await _scrape_page(url)
                if len(text.strip()) < 50:
                    break
                products = await _extract_with_llm(text, url)
                all_products.extend(products)
                break
            except Exception as e:
                if attempt == 0:
                    logger.warning(f"페이지 처리 재시도 ({url}): {e}")
                    await asyncio.sleep(1)
                else:
                    logger.warning(f"페이지 처리 최종 실패 ({url}): {e}")

    return all_products
