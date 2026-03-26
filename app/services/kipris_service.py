"""KIPRIS 한국 특허 검색 서비스."""
import asyncio
import logging
from functools import partial
from xml.etree import ElementTree

import httpx

from app.core.config import settings
from app.schemas.models import KiprisItem

logger = logging.getLogger(__name__)

KIPRIS_SEARCH_URL = "http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getWordSearch"


def _parse_response(xml_text: str) -> list[dict]:
    """Parse KIPRIS XML response into list of dicts."""
    root = ElementTree.fromstring(xml_text)

    items = []
    for item in root.iter("item"):
        items.append({
            "application_number": _text(item, "applicationNumber"),
            "title": _text(item, "inventionTitle"),
            "applicant": _text(item, "applicantName"),
            "abstract": _text(item, "astrtCont"),
            "application_date": _text(item, "applicationDate"),
            "registration_number": _text(item, "registerNumber"),
        })
    return items


def _text(element: ElementTree.Element, tag: str) -> str:
    """Safely extract text from XML element."""
    el = element.find(tag)
    return el.text.strip() if el is not None and el.text else ""


async def search_kipris(query: str, max_results: int = 15) -> list[KiprisItem]:
    """Search KIPRIS for Korean patents."""
    params = {
        "word": query,
        "numOfRows": max_results,
        "pageNo": 1,
        "ServiceKey": settings.kipris_api_key,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(KIPRIS_SEARCH_URL, params=params)
        resp.raise_for_status()

    items = _parse_response(resp.text)

    return [
        KiprisItem(
            application_number=item["application_number"],
            title=item["title"],
            applicant=item["applicant"],
            abstract=item["abstract"],
            application_date=item["application_date"],
            url=f"http://kportal.kipris.or.kr/kportal/search/search_patent.do?next=MainRecordDetailView&applno={item['application_number']}"
                if item["application_number"] else "",
        )
        for item in items
    ]
