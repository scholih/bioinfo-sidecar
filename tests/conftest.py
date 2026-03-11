"""Shared pytest fixtures."""

import pytest
from unittest.mock import MagicMock

from sidecar.models.paper import Paper
from sidecar.models.chunk import Chunk
from datetime import date


@pytest.fixture
def sample_paper() -> Paper:
    return Paper(
        arxiv_id="2401.00001",
        title="Test Paper on CRISPR Gene Editing",
        authors=["Alice Smith", "Bob Jones"],
        abstract="We present a novel method for CRISPR off-target detection using machine learning.",
        categories=["q-bio.GN", "cs.LG"],
        published=date(2024, 1, 1),
        pdf_url="https://arxiv.org/pdf/2401.00001",
    )


@pytest.fixture
def sample_chunk(sample_paper: Paper) -> Chunk:
    return Chunk(
        paper_arxiv_id=sample_paper.arxiv_id,
        chunk_index=0,
        section="Methods",
        content="We used a transformer-based model to predict CRISPR off-target sites from genomic sequences.",
        tokens=20,
        embedding=[0.1] * 768,
    )


@pytest.fixture
def mock_llm() -> MagicMock:
    llm = MagicMock()
    llm.chat.return_value = "This is a test answer about bioinformatics."
    llm.embed.return_value = [[0.1] * 768]
    llm.is_healthy.return_value = True
    return llm


@pytest.fixture
def mock_db() -> MagicMock:
    db = MagicMock()
    db.hybrid_search.return_value = [
        {
            "chunk_id": "test-id",
            "section": "Methods",
            "content": "CRISPR off-target detection using ML.",
            "tokens": 10,
            "score": 0.85,
            "arxiv_id": "2401.00001",
            "title": "Test Paper",
            "authors": ["Alice Smith"],
            "published": "2024-01-01",
        }
    ]
    return db
