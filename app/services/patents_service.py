"""Google Patents search via BigQuery public dataset."""
import asyncio
from functools import partial

from google.cloud import bigquery

from app.schemas.models import PatentItem


def _run_query(query: str, max_results: int) -> list[dict]:
    """Execute BigQuery SQL synchronously."""
    client = bigquery.Client()

    sql = """
        SELECT
            publication_number,
            (SELECT t.text FROM UNNEST(title_localized) AS t LIMIT 1) AS title,
            (SELECT a.text FROM UNNEST(abstract_localized) AS a LIMIT 1) AS abstract,
            IFNULL(
                (SELECT h.name FROM UNNEST(assignee_harmonized) AS h LIMIT 1),
                ''
            ) AS applicant,
            CAST(filing_date AS STRING) AS filing_date,
            country_code,
            -- 관련도 점수: 제목 매치 = 3점, 초록 매치 = 1점, KR 특허 = 2점 가산
            (
                CASE WHEN EXISTS (SELECT 1 FROM UNNEST(title_localized) AS t WHERE LOWER(t.text) LIKE CONCAT('%', LOWER(@query), '%'))
                     THEN 3 ELSE 0 END
                + CASE WHEN EXISTS (SELECT 1 FROM UNNEST(abstract_localized) AS a WHERE LOWER(a.text) LIKE CONCAT('%', LOWER(@query), '%'))
                       THEN 1 ELSE 0 END
                + CASE WHEN country_code = 'KR' THEN 2 ELSE 0 END
            ) AS relevance_score
        FROM
            `patents-public-data.patents.publications`
        WHERE
            EXISTS (SELECT 1 FROM UNNEST(title_localized) AS t WHERE LOWER(t.text) LIKE CONCAT('%', LOWER(@query), '%'))
            OR EXISTS (SELECT 1 FROM UNNEST(abstract_localized) AS a WHERE LOWER(a.text) LIKE CONCAT('%', LOWER(@query), '%'))
        ORDER BY
            relevance_score DESC,
            filing_date DESC
        LIMIT @max_results
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("query", "STRING", query),
            bigquery.ScalarQueryParameter("max_results", "INT64", max_results),
        ]
    )
    result = client.query(sql, job_config=job_config).result()
    return [dict(row) for row in result]


async def search_patents(query: str, max_results: int = 15) -> list[PatentItem]:
    """Search Google Patents public dataset, prioritising KR patents."""
    loop = asyncio.get_running_loop()
    rows = await loop.run_in_executor(None, partial(_run_query, query, max_results))

    return [
        PatentItem(
            publication_number=r.get("publication_number", ""),
            title=r.get("title", ""),
            applicant=r.get("applicant", ""),
            abstract=r.get("abstract", ""),
            filing_date=r.get("filing_date", ""),
            country_code=r.get("country_code", ""),
            url=f"https://patents.google.com/patent/{r.get('publication_number', '')}"
                if r.get("publication_number") else "",
        )
        for r in rows
    ]
