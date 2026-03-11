"""pgvector index and search CLI.

Usage:
    uv run python sidecar/store.py index chunks.json --arxiv-id 2401.12345
    uv run python sidecar/store.py search "RNA-seq batch correction methods" --top-k 5
    uv run python sidecar/store.py stats
"""

import json
import logging
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from sidecar.config import get_settings
from sidecar.models.chunk import Chunk
from sidecar.models.paper import Paper
from sidecar.services.ollama_client import make_ollama_client
from sidecar.services.pgvector_client import make_pgvector_client

logging.basicConfig(level=logging.WARNING)
app = typer.Typer(help="Index and search paper chunks in pgvector")
console = Console()


@app.command()
def index(
    chunks_file: Path = typer.Argument(..., help="JSON file of chunks from parse.py", exists=True),
    arxiv_id: str = typer.Option(None, "--arxiv-id", "-i", help="arXiv ID (inferred from chunks if omitted)"),
    title: str = typer.Option("Unknown", "--title", "-t"),
    authors: str = typer.Option("", "--authors", "-a", help="Comma-separated authors"),
    batch_size: int = typer.Option(32, "--batch", "-b", help="Embedding batch size"),
) -> None:
    """Embed and index chunks from CHUNKS_FILE into pgvector."""
    settings = get_settings()
    llm = make_ollama_client(
        base_url=settings.ollama.base_url,
        chat_model=settings.ollama.chat_model,
        embed_model=settings.ollama.embed_model,
    )
    db = make_pgvector_client(settings.postgres.dsn)

    with open(chunks_file) as f:
        raw = json.load(f)

    if not raw:
        console.print("[red]No chunks found in file[/red]")
        raise typer.Exit(1)

    arxiv_id = arxiv_id or raw[0].get("arxiv_id", "unknown")

    # Upsert paper metadata
    from datetime import date
    paper = Paper(
        arxiv_id=arxiv_id,
        title=title,
        authors=[a.strip() for a in authors.split(",") if a.strip()],
        abstract="",
        categories=[],
        published=date.today(),
        pdf_url="",
    )
    paper_db_id = db.upsert_paper(paper)
    console.print(f"[cyan]Paper upserted: {arxiv_id} (db_id={paper_db_id})[/cyan]")

    # Build chunk objects
    chunks = [
        Chunk(
            paper_arxiv_id=r["arxiv_id"],
            chunk_index=r["chunk_index"],
            section=r.get("section", "Unknown"),
            content=r["content"],
            tokens=r.get("tokens", 0),
        )
        for r in raw
    ]

    # Embed in batches
    console.print(f"[cyan]Embedding {len(chunks)} chunks (batch={batch_size})...[/cyan]")
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c.content for c in batch]
        embeddings = llm.embed(texts)
        for chunk, emb in zip(batch, embeddings):
            chunk.embedding = emb
        console.print(f"  [{i + len(batch)}/{len(chunks)}] embedded")

    inserted = db.insert_chunks(chunks, paper_db_id)
    console.print(f"[green]Indexed {inserted} chunks for {arxiv_id}[/green]")
    db.close()


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    top_k: int = typer.Option(5, "--top-k", "-k"),
    hybrid: bool = typer.Option(True, "--hybrid/--vector-only", help="Use hybrid BM25+vector search"),
) -> None:
    """Search the indexed chunks for QUERY."""
    settings = get_settings()
    llm = make_ollama_client(
        base_url=settings.ollama.base_url,
        embed_model=settings.ollama.embed_model,
        chat_model=settings.ollama.chat_model,
    )
    db = make_pgvector_client(settings.postgres.dsn)

    query_embedding = llm.embed([query])[0]

    if hybrid:
        results = db.hybrid_search(query=query, query_embedding=query_embedding, top_k=top_k)
    else:
        results = db.vector_search(query_embedding=query_embedding, top_k=top_k)

    table = Table(title=f"Search: '{query}' (top {top_k})", show_lines=True)
    table.add_column("Score", style="cyan", width=6)
    table.add_column("arXiv ID", width=14)
    table.add_column("Section", width=16)
    table.add_column("Excerpt")

    for r in results:
        table.add_row(
            f"{r['score']:.3f}",
            r["arxiv_id"],
            r["section"],
            r["content"][:120].replace("\n", " ") + "…",
        )

    console.print(table)
    db.close()


@app.command()
def stats() -> None:
    """Show index statistics."""
    settings = get_settings()
    db = make_pgvector_client(settings.postgres.dsn)
    s = db.stats()
    console.print(f"[bold]Papers indexed:[/bold] {s['papers']}")
    console.print(f"[bold]Total chunks:[/bold]  {s['chunks']}")
    console.print(f"[bold]With embeddings:[/bold] {s['chunks_with_embeddings']}")
    db.close()


if __name__ == "__main__":
    app()
