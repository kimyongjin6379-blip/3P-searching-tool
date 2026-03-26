"""Excel export service using pandas + openpyxl."""
import io

import pandas as pd

from app.schemas.models import ExportRequest


def build_excel(data: ExportRequest) -> io.BytesIO:
    """Create a multi-sheet Excel workbook and return as bytes buffer."""
    buf = io.BytesIO()

    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        # Sheet 1: 논문
        if data.articles:
            df_articles = pd.DataFrame(
                [
                    {
                        "PMID": a.pmid,
                        "제목": a.title,
                        "저자": ", ".join(a.authors),
                        "발행일": a.pub_date,
                        "초록": a.abstract,
                    }
                    for a in data.articles
                ]
            )
        else:
            df_articles = pd.DataFrame(columns=["PMID", "제목", "저자", "발행일", "초록"])
        df_articles.to_excel(writer, sheet_name="논문", index=False)

        # Sheet 2: 특허
        if data.patents:
            df_patents = pd.DataFrame(
                [
                    {
                        "출원번호": p.publication_number,
                        "특허명": p.title,
                        "출원인": p.applicant,
                        "요약": p.abstract,
                        "출원일": p.filing_date,
                        "국가코드": p.country_code,
                    }
                    for p in data.patents
                ]
            )
        else:
            df_patents = pd.DataFrame(
                columns=["출원번호", "특허명", "출원인", "요약", "출원일", "국가코드"]
            )
        df_patents.to_excel(writer, sheet_name="Google특허", index=False)

        # Sheet 3: KIPRIS 한국 특허
        if data.kipris:
            df_kipris = pd.DataFrame(
                [
                    {
                        "출원번호": k.application_number,
                        "발명의 명칭": k.title,
                        "출원인": k.applicant,
                        "요약": k.abstract,
                        "출원일": k.application_date,
                        "링크": k.url,
                    }
                    for k in data.kipris
                ]
            )
        else:
            df_kipris = pd.DataFrame(
                columns=["출원번호", "발명의 명칭", "출원인", "요약", "출원일", "링크"]
            )
        df_kipris.to_excel(writer, sheet_name="한국특허", index=False)

        # Sheet 4: 제품
        if data.products:
            df_products = pd.DataFrame(
                [
                    {
                        "제품명": p.product_name,
                        "제조사": p.manufacturer,
                        "적용 가능 균주": p.applicable_strains,
                        "펩톤/효소 규격": p.peptone_enzyme_spec,
                        "주요 특장점": p.key_features,
                        "출처 URL": p.source_url,
                    }
                    for p in data.products
                ]
            )
        else:
            df_products = pd.DataFrame(
                columns=["제품명", "제조사", "적용 가능 균주", "펩톤/효소 규격", "주요 특장점", "출처 URL"]
            )
        df_products.to_excel(writer, sheet_name="제품", index=False)

    buf.seek(0)
    return buf
