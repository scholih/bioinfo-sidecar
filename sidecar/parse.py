"""Scientific PDF parser CLI.

Usage:
    uv run python sidecar/parse.py paper.pdf --output chunks.json
    uv run python sidecar/parse.py paper.pdf --arxiv-id 2401.12345
    cat paper_meta.json | uv run python sidecar/parse.py --from-url
"""

import json
import logging
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import track

from sidecar.services.parser import make_parser

logging.basicConfig(level=logging.WARNING)
app = typer.Typer(help="Parse scientific PDFs into labelled text chunks")
console = Console()


@app.command()
def parse(
    pdf_path: Path = typer.Argument(..., help="Path to PDF file", exists=True),
    arxiv_id: str = typer.Option("unknown", "--arxiv-id", "-i", help="arXiv ID for metadata"),
    output: str = typer.Option(None, "--output", "-o", help="Output JSON file"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="JSON output only"),
) -> None:
    """Parse PDF_PATH into text chunks with section labels."""
    parser = make_parser()

    if not quiet:
        console.print(f"[cyan]Parsing {pdf_path.name}...[/cyan]")

    chunks = parser.parse_pdf(pdf_path, arxiv_id)

    data = [
        {
            "arxiv_id": c.paper_arxiv_id,
            "chunk_index": c.chunk_index,
            "section": c.section,
            "content": c.content,
            "tokens": c.tokens,
        }
        for c in chunks
    ]

    if output:
        with open(output, "w") as f:
            json.dump(data, f, indent=2)
        if not quiet:
            sections = {c["section"] for c in data}
            console.print(f"[green]Saved {len(chunks)} chunks to {output}[/green]")
            console.print(f"Sections detected: {', '.join(sorted(sections))}")
    else:
        print(json.dumps(data, indent=2))


@app.command()
def download_and_parse(
    pdf_url: str = typer.Argument(..., help="PDF URL to download and parse"),
    arxiv_id: str = typer.Option("unknown", "--arxiv-id", "-i"),
    output: str = typer.Option(None, "--output", "-o"),
) -> None:
    """Download PDF from URL, then parse it."""
    parser = make_parser()
    console.print(f"[cyan]Downloading {pdf_url}...[/cyan]")
    pdf_path = parser.download_pdf(pdf_url, arxiv_id)
    console.print(f"[green]Downloaded to {pdf_path}[/green]")

    chunks = parser.parse_pdf(pdf_path, arxiv_id)
    data = [
        {"arxiv_id": c.paper_arxiv_id, "chunk_index": c.chunk_index,
         "section": c.section, "content": c.content, "tokens": c.tokens}
        for c in chunks
    ]

    if output:
        with open(output, "w") as f:
            json.dump(data, f, indent=2)
        console.print(f"[green]Saved {len(chunks)} chunks → {output}[/green]")
    else:
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    app()
