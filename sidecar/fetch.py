"""arXiv paper discovery CLI.

Usage:
    uv run python sidecar/fetch.py search "CRISPR off-target" --cat q-bio.GN --days 30
    uv run python sidecar/fetch.py paper 2401.12345
    uv run python sidecar/fetch.py categories
"""

import json
import logging
import sys

import typer
from rich.console import Console
from rich.table import Table

from sidecar.config import get_settings
from sidecar.services.arxiv_client import BIO_CATEGORIES, make_arxiv_client

logging.basicConfig(level=logging.WARNING)
app = typer.Typer(help="Discover bioinformatics papers on arXiv")
console = Console()


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    cat: list[str] = typer.Option([], "--cat", "-c", help="arXiv category filter (repeatable)"),
    days: int = typer.Option(None, "--days", "-d", help="Only papers from last N days"),
    max_results: int = typer.Option(None, "--max", "-n", help="Max results"),
    output: str = typer.Option(None, "--output", "-o", help="Save results to JSON file"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Output JSON only (for piping)"),
) -> None:
    """Search arXiv for papers matching QUERY."""
    settings = get_settings()
    client = make_arxiv_client(
        max_results=max_results or settings.arxiv.max_results,
        rate_limit_seconds=settings.arxiv.rate_limit_seconds,
    )

    papers = client.search(query=query, categories=cat or None, days=days, max_results=max_results)

    if quiet or output:
        data = [
            {
                "arxiv_id": p.arxiv_id,
                "title": p.title,
                "authors": p.authors,
                "abstract": p.abstract,
                "categories": p.categories,
                "published": str(p.published),
                "pdf_url": p.pdf_url,
            }
            for p in papers
        ]
        if output:
            with open(output, "w") as f:
                json.dump(data, f, indent=2)
            console.print(f"[green]Saved {len(papers)} papers to {output}[/green]")
        else:
            print(json.dumps(data, indent=2))
        return

    table = Table(title=f"arXiv results for '{query}' ({len(papers)} papers)")
    table.add_column("arXiv ID", style="cyan", no_wrap=True)
    table.add_column("Published", style="dim")
    table.add_column("Title")
    table.add_column("Authors", style="dim")

    for p in papers:
        table.add_row(
            p.arxiv_id,
            str(p.published),
            p.title[:70] + ("…" if len(p.title) > 70 else ""),
            ", ".join(p.authors[:2]) + ("…" if len(p.authors) > 2 else ""),
        )

    console.print(table)


@app.command()
def paper(
    arxiv_id: str = typer.Argument(..., help="arXiv paper ID (e.g. 2401.12345)"),
    output: str = typer.Option(None, "--output", "-o", help="Save to JSON file"),
) -> None:
    """Fetch a single paper by arXiv ID."""
    client = make_arxiv_client()
    p = client.fetch_paper(arxiv_id)

    data = {
        "arxiv_id": p.arxiv_id,
        "title": p.title,
        "authors": p.authors,
        "abstract": p.abstract,
        "categories": p.categories,
        "published": str(p.published),
        "pdf_url": p.pdf_url,
    }

    if output:
        with open(output, "w") as f:
            json.dump(data, f, indent=2)
    else:
        console.print_json(json.dumps(data, indent=2))


@app.command()
def categories() -> None:
    """List supported arXiv bioinformatics categories."""
    table = Table(title="Bioinformatics arXiv Categories")
    table.add_column("Category", style="cyan")
    table.add_column("Description")
    for cat, desc in BIO_CATEGORIES.items():
        table.add_row(cat, desc)
    console.print(table)


if __name__ == "__main__":
    app()
