"""Chunk dataclass — represents one text chunk from a parsed paper."""

from dataclasses import dataclass, field
from uuid import UUID


KNOWN_SECTIONS = {
    "Abstract",
    "Introduction",
    "Background",
    "Methods",
    "Materials and Methods",
    "Results",
    "Discussion",
    "Conclusion",
    "References",
    "Supplementary",
}


@dataclass
class Chunk:
    paper_arxiv_id: str
    chunk_index: int
    content: str
    section: str = "Unknown"
    tokens: int = 0
    embedding: list[float] = field(default_factory=list)
    db_id: UUID | None = None
    paper_db_id: UUID | None = None

    def __post_init__(self) -> None:
        if not self.tokens:
            # rough token estimate: ~4 chars per token
            self.tokens = len(self.content) // 4

    def __str__(self) -> str:
        preview = self.content[:80].replace("\n", " ")
        return f"[{self.paper_arxiv_id} §{self.section} chunk {self.chunk_index}] {preview}..."
