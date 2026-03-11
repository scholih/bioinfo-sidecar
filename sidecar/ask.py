"""Agentic RAG CLI — ask questions over your indexed paper collection.

Usage:
    uv run python sidecar/ask.py "What methods exist for scRNA-seq batch correction?"
    uv run python sidecar/ask.py --stream "Compare UMAP vs t-SNE for single-cell data"
"""

import logging
import sys

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from sidecar.config import get_settings
from sidecar.services.agents.graph import run_agent
from sidecar.services.ollama_client import make_ollama_client
from sidecar.services.pgvector_client import make_pgvector_client

logging.basicConfig(level=logging.WARNING)
app = typer.Typer(help="Ask questions over your indexed bioinformatics papers")
console = Console()


@app.command()
def ask(
    question: str = typer.Argument(..., help="Your research question"),
    stream: bool = typer.Option(False, "--stream", "-s", help="Stream tokens (experimental)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show retrieved chunks"),
) -> None:
    """Ask QUESTION and get an answer grounded in your indexed papers."""
    settings = get_settings()

    llm = make_ollama_client(
        base_url=settings.ollama.base_url,
        chat_model=settings.ollama.chat_model,
        embed_model=settings.ollama.embed_model,
        temperature=settings.ollama.temperature,
    )
    db = make_pgvector_client(settings.postgres.dsn)

    if not llm.is_healthy():
        console.print(
            f"[red]Ollama is not running or model '{settings.ollama.chat_model}' not found.[/red]\n"
            f"Run: ollama pull {settings.ollama.chat_model}"
        )
        raise typer.Exit(1)

    console.print(f"[dim]Querying: {question[:80]}[/dim]")

    final_state = run_agent(question, llm=llm, db=db)

    answer = final_state.get("answer", "No answer generated.")
    citations = final_state.get("citations", [])

    console.print()
    console.print(Panel(Markdown(answer), title="Answer", border_style="green"))

    if citations:
        console.print(f"\n[bold]Sources:[/bold] {', '.join(citations)}")

    if verbose:
        graded = final_state.get("graded_chunks", [])
        if graded:
            console.print(f"\n[dim]Used {len(graded)} chunks from:[/dim]")
            for c in graded:
                console.print(f"  [{c['score']:.2f}] {c['arxiv_id']} — {c['section']}")

    db.close()


if __name__ == "__main__":
    app()
