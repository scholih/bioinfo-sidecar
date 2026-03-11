"""Unit tests for Paper and Chunk models."""

from datetime import date

import pytest

from sidecar.models.chunk import Chunk
from sidecar.models.paper import Paper


class TestPaper:
    def test_short_id_strips_version(self) -> None:
        paper = Paper(
            arxiv_id="2401.00001v2",
            title="Test", authors=[], abstract="", categories=[],
            published=date.today(), pdf_url="",
        )
        assert paper.short_id == "2401.00001"

    def test_str_shows_title_and_authors(self, sample_paper: Paper) -> None:
        s = str(sample_paper)
        assert "2401.00001" in s
        assert "CRISPR" in s

    def test_str_truncates_long_author_list(self) -> None:
        paper = Paper(
            arxiv_id="2401.00002",
            title="Multi-author paper", authors=["A", "B", "C", "D"], abstract="",
            categories=[], published=date.today(), pdf_url="",
        )
        assert "…" in str(paper)


class TestChunk:
    def test_tokens_estimated_when_zero(self) -> None:
        chunk = Chunk(
            paper_arxiv_id="2401.00001",
            chunk_index=0,
            content="A" * 400,  # 400 chars → ~100 tokens
            tokens=0,
        )
        assert chunk.tokens == 100

    def test_str_shows_section_and_preview(self, sample_chunk: Chunk) -> None:
        s = str(sample_chunk)
        assert "Methods" in s
        assert "2401.00001" in s

    def test_explicit_tokens_not_overridden(self) -> None:
        chunk = Chunk(
            paper_arxiv_id="2401.00001",
            chunk_index=0,
            content="Short text",
            tokens=999,
        )
        assert chunk.tokens == 999
