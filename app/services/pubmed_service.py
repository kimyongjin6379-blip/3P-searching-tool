"""PubMed search via Biopython Entrez."""
import asyncio
from functools import partial

from Bio import Entrez, Medline

from app.core.config import settings
from app.schemas.models import PubMedArticle


async def search_pubmed(query: str, max_results: int = 15) -> list[PubMedArticle]:
    """Search PubMed and return parsed articles sorted by relevance."""
    Entrez.email = settings.entrez_email
    loop = asyncio.get_running_loop()

    # 1) Search for PMIDs (relevance order)
    handle = await loop.run_in_executor(
        None,
        partial(
            Entrez.esearch,
            db="pubmed",
            term=query,
            retmax=max_results,
            sort="relevance",
        ),
    )
    search_results = Entrez.read(handle)
    handle.close()

    id_list: list[str] = search_results.get("IdList", [])
    if not id_list:
        return []

    # 2) Fetch article details
    handle = await loop.run_in_executor(
        None,
        partial(
            Entrez.efetch,
            db="pubmed",
            id=",".join(id_list),
            rettype="medline",
            retmode="text",
        ),
    )
    records = list(Medline.parse(handle))
    handle.close()

    articles: list[PubMedArticle] = []
    for rec in records:
        pmid = rec.get("PMID", "")
        articles.append(
            PubMedArticle(
                pmid=pmid,
                title=rec.get("TI", ""),
                authors=rec.get("AU", []),
                pub_date=rec.get("DP", ""),
                abstract=rec.get("AB", ""),
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
            )
        )
    return articles
