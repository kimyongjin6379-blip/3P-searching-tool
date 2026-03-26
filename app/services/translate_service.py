"""Auto-translate search query between Korean ↔ English using GPT-4o-mini."""
import json
import logging
import re

from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

TRANSLATE_PROMPT = """\
You are a bilingual Korean-English translator for scientific/biotech terminology.

Given a search query, detect its language and provide both Korean and English versions.

Rules:
- If the input is Korean, translate to English (natural scientific search terms, NOT literal translation)
- If the input is English, translate to Korean (natural scientific search terms)
- If mixed, produce clean versions in both languages
- Keep technical terms accurate (e.g. 펩톤 = peptone, 균주 = microbial strain)
- Output ONLY valid JSON, no markdown

Output format:
{"ko": "한국어 검색어", "en": "English search query", "detected": "ko" or "en"}
"""


async def translate_query(query: str) -> dict:
    """Translate query and return both Korean and English versions.

    Returns: {"ko": "...", "en": "...", "detected": "ko"|"en"}
    """
    # Quick language detection: if mostly ASCII → English, else Korean
    non_ascii = len(re.findall(r'[^\x00-\x7F]', query))
    is_korean = non_ascii > len(query) * 0.3

    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": TRANSLATE_PROMPT},
                {"role": "user", "content": query},
            ],
            temperature=0,
            max_tokens=200,
        )
        raw = response.choices[0].message.content or "{}"
        result = json.loads(raw)

        return {
            "ko": result.get("ko", query if is_korean else ""),
            "en": result.get("en", query if not is_korean else ""),
            "detected": result.get("detected", "ko" if is_korean else "en"),
        }
    except Exception as e:
        logger.warning(f"번역 실패, 원본 사용: {e}")
        # Fallback: use original query for both
        return {
            "ko": query,
            "en": query,
            "detected": "ko" if is_korean else "en",
        }
