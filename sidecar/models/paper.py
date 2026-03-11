"""Paper dataclass — represents one arXiv paper."""

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID


@dataclass
class Paper:
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    categories: list[str]
    published: date
    pdf_url: str
    html_url: str | None = None
    parser_used: str = "docling"
    db_id: UUID | None = None

    @property
    def short_id(self) -> str:
        """e.g. '2401.12345'"""
        return self.arxiv_id.split("v")[0]

    def __str__(self) -> str:
        return f"[{self.arxiv_id}] {self.title} ({', '.join(self.authors[:2])}{'...' if len(self.authors) > 2 else ''})"
