"""Scientific PDF parser — Docling primary, Marker fallback."""

import logging
import tempfile
import time
from pathlib import Path

import httpx

from sidecar.models.chunk import Chunk

logger = logging.getLogger(__name__)

CHUNK_SIZE_TOKENS = 512
CHUNK_OVERLAP_TOKENS = 64
CHARS_PER_TOKEN = 4


class Parser:
    """Parse scientific PDFs into labelled text chunks.

    Strategy:
    - Try Docling first (layout-aware, handles tables/figures well)
    - Fall back to Marker (fast, Markdown output)
    - Fall back to plain PyMuPDF text extraction

    Benchmarks on bioinformatics papers:
    - Docling: best section detection, 10-60s/paper
    - Marker:  good text quality, 2-5s/paper
    - PyMuPDF: fastest, no layout, last resort
    """

    def parse_pdf(self, pdf_path: Path, arxiv_id: str) -> list[Chunk]:
        """Parse a PDF file into chunks. Returns list of Chunk objects."""
        logger.info("Parsing %s with Docling...", pdf_path.name)
        try:
            return self._parse_with_docling(pdf_path, arxiv_id)
        except Exception as e:
            logger.warning("Docling failed (%s), falling back to Marker", e)

        try:
            return self._parse_with_marker(pdf_path, arxiv_id)
        except Exception as e:
            logger.warning("Marker failed (%s), falling back to PyMuPDF", e)

        return self._parse_with_pymupdf(pdf_path, arxiv_id)

    def _parse_with_docling(self, pdf_path: Path, arxiv_id: str) -> list[Chunk]:
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        result = converter.convert(str(pdf_path))
        doc = result.document

        raw_chunks: list[tuple[str, str]] = []  # (section, text)
        current_section = "Unknown"

        for item, _ in doc.iterate_items():
            item_type = type(item).__name__
            if item_type in ("SectionHeaderItem", "HeadingItem"):
                current_section = item.text.strip()
            elif item_type in ("TextItem", "ParagraphItem"):
                raw_chunks.append((current_section, item.text.strip()))

        return self._build_chunks(raw_chunks, arxiv_id, parser="docling")

    def _parse_with_marker(self, pdf_path: Path, arxiv_id: str) -> list[Chunk]:
        from marker.convert import convert_single_pdf
        from marker.models import load_all_models

        models = load_all_models()
        full_text, _, _ = convert_single_pdf(str(pdf_path), models)

        # Split Markdown by ## headings
        raw_chunks: list[tuple[str, str]] = []
        current_section = "Introduction"
        for line in full_text.split("\n"):
            if line.startswith("## "):
                current_section = line.lstrip("# ").strip()
            elif line.strip():
                raw_chunks.append((current_section, line.strip()))

        return self._build_chunks(raw_chunks, arxiv_id, parser="marker")

    def _parse_with_pymupdf(self, pdf_path: Path, arxiv_id: str) -> list[Chunk]:
        import fitz  # PyMuPDF

        doc = fitz.open(str(pdf_path))
        raw_chunks: list[tuple[str, str]] = []
        for page in doc:
            text = page.get_text().strip()
            if text:
                raw_chunks.append(("Unknown", text))
        doc.close()
        return self._build_chunks(raw_chunks, arxiv_id, parser="pymupdf")

    def _build_chunks(
        self, raw: list[tuple[str, str]], arxiv_id: str, parser: str
    ) -> list[Chunk]:
        """Merge raw (section, text) pairs into fixed-size chunks with overlap."""
        chunks: list[Chunk] = []
        chunk_size = CHUNK_SIZE_TOKENS * CHARS_PER_TOKEN
        overlap = CHUNK_OVERLAP_TOKENS * CHARS_PER_TOKEN

        buffer = ""
        buffer_section = "Unknown"
        chunk_index = 0

        for section, text in raw:
            if not text:
                continue
            if len(buffer) == 0:
                buffer_section = section
            buffer += " " + text

            while len(buffer) >= chunk_size:
                chunk_text = buffer[:chunk_size].strip()
                chunks.append(
                    Chunk(
                        paper_arxiv_id=arxiv_id,
                        chunk_index=chunk_index,
                        section=buffer_section,
                        content=chunk_text,
                        tokens=len(chunk_text) // CHARS_PER_TOKEN,
                    )
                )
                chunk_index += 1
                buffer = buffer[chunk_size - overlap:]
                buffer_section = section

        if buffer.strip():
            chunks.append(
                Chunk(
                    paper_arxiv_id=arxiv_id,
                    chunk_index=chunk_index,
                    section=buffer_section,
                    content=buffer.strip(),
                    tokens=len(buffer) // CHARS_PER_TOKEN,
                )
            )

        logger.info("Parsed %d chunks via %s for %s", len(chunks), parser, arxiv_id)
        return chunks

    def download_pdf(self, pdf_url: str, arxiv_id: str) -> Path:
        """Download a PDF to a temp file and return the path."""
        tmp = Path(tempfile.mkdtemp()) / f"{arxiv_id}.pdf"
        with httpx.stream("GET", pdf_url, follow_redirects=True, timeout=60.0) as r:
            r.raise_for_status()
            with open(tmp, "wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)
        logger.info("Downloaded %s → %s", pdf_url, tmp)
        return tmp


def make_parser() -> Parser:
    return Parser()
