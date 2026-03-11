"""arXiv API client — search and fetch paper metadata."""

import asyncio
import logging
from datetime import date, timedelta

import arxiv
import httpx

from sidecar.models.paper import Paper

logger = logging.getLogger(__name__)

# Bioinformatics-relevant arXiv categories
BIO_CATEGORIES = {
    "q-bio.GN": "Genomics",
    "q-bio.QM": "Quantitative Methods",
    "q-bio.BM": "Biomolecules",
    "q-bio.MN": "Molecular Networks",
    "cs.LG": "Machine Learning",
    "cs.AI": "Artificial Intelligence",
    "stat.ML": "Statistics / ML",
}


class ArxivClient:
    def __init__(self, max_results: int = 50, rate_limit_seconds: float = 3.0) -> None:
        self.max_results = max_results
        self.rate_limit_seconds = rate_limit_seconds
        self._client = arxiv.Client(page_size=100, delay_seconds=rate_limit_seconds)

    def search(
        self,
        query: str,
        categories: list[str] | None = None,
        days: int | None = None,
        max_results: int | None = None,
    ) -> list[Paper]:
        """Search arXiv and return Paper objects."""
        search_query = query

        if categories:
            cat_filter = " OR ".join(f"cat:{c}" for c in categories)
            search_query = f"({query}) AND ({cat_filter})"

        if days:
            since = date.today() - timedelta(days=days)
            search_query += f" AND submittedDate:[{since.strftime('%Y%m%d')} TO 99991231]"

        logger.info("Searching arXiv: %s", search_query)

        search = arxiv.Search(
            query=search_query,
            max_results=max_results or self.max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        papers: list[Paper] = []
        for result in self._client.results(search):
            papers.append(self._to_paper(result))

        logger.info("Found %d papers", len(papers))
        return papers

    def fetch_paper(self, arxiv_id: str) -> Paper:
        """Fetch a single paper by arXiv ID."""
        search = arxiv.Search(id_list=[arxiv_id])
        result = next(self._client.results(search))
        return self._to_paper(result)

    def _to_paper(self, result: arxiv.Result) -> Paper:
        arxiv_id = result.entry_id.split("/")[-1]
        return Paper(
            arxiv_id=arxiv_id,
            title=result.title.strip(),
            authors=[str(a) for a in result.authors],
            abstract=result.summary.strip(),
            categories=[c for c in result.categories],
            published=result.published.date(),
            pdf_url=result.pdf_url,
            html_url=f"https://arxiv.org/html/{arxiv_id}",
        )


def make_arxiv_client(max_results: int = 50, rate_limit_seconds: float = 3.0) -> ArxivClient:
    return ArxivClient(max_results=max_results, rate_limit_seconds=rate_limit_seconds)
