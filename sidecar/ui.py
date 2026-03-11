"""Gradio research dashboard — 4-tab UI for paper discovery, RAG chat, collection browser, status.

Usage:
    uv run python sidecar/ui.py
    uv run python sidecar/ui.py --port 7861 --share
"""

import json
import logging
from datetime import date, timedelta

import gradio as gr
import typer

from sidecar.config import get_settings
from sidecar.services.agents.graph import run_agent
from sidecar.services.arxiv_client import BIO_CATEGORIES, make_arxiv_client
from sidecar.services.ollama_client import make_ollama_client
from sidecar.services.parser import make_parser
from sidecar.services.pgvector_client import make_pgvector_client

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ── Shared services (initialised once) ───────────────────────────────────────
settings = get_settings()
llm = make_ollama_client(
    base_url=settings.ollama.base_url,
    chat_model=settings.ollama.chat_model,
    embed_model=settings.ollama.embed_model,
)
db = make_pgvector_client(settings.postgres.dsn)
arxiv_client = make_arxiv_client(max_results=settings.arxiv.max_results)
parser = make_parser()


# ── Tab 1: Paper Discovery ────────────────────────────────────────────────────

def search_papers(query: str, categories: list[str], days: int) -> tuple:
    """Search arXiv and return table data + status."""
    if not query.strip():
        return [], "Enter a search query."
    try:
        papers = arxiv_client.search(query=query, categories=categories or None, days=days or None)
        rows = [
            [p.arxiv_id, str(p.published), p.title[:80], ", ".join(p.authors[:2]), ", ".join(p.categories[:2])]
            for p in papers
        ]
        return rows, f"Found {len(papers)} papers."
    except Exception as e:
        return [], f"Error: {e}"


def index_paper(arxiv_id: str) -> str:
    """Download, parse, embed, and index a single paper."""
    if not arxiv_id.strip():
        return "Enter an arXiv ID."
    try:
        paper = arxiv_client.fetch_paper(arxiv_id.strip())
        pdf_path = parser.download_pdf(paper.pdf_url, paper.arxiv_id)
        chunks = parser.parse_pdf(pdf_path, paper.arxiv_id)

        # Embed
        for i in range(0, len(chunks), 32):
            batch = chunks[i:i+32]
            embeddings = llm.embed([c.content for c in batch])
            for chunk, emb in zip(batch, embeddings):
                chunk.embedding = emb

        # Store
        paper_db_id = db.upsert_paper(paper)
        inserted = db.insert_chunks(chunks, paper_db_id)
        return f"Indexed {inserted} chunks from '{paper.title[:60]}' ({paper.arxiv_id})"
    except Exception as e:
        return f"Error indexing {arxiv_id}: {e}"


# ── Tab 2: RAG Chat ───────────────────────────────────────────────────────────

def chat_respond(message: str, history: list) -> tuple[str, list]:
    """Run RAG agent and return (answer, updated history)."""
    if not message.strip():
        return "", history
    try:
        state = run_agent(message, llm=llm, db=db)
        answer = state.get("answer", "No answer generated.")
        citations = state.get("citations", [])
        if citations:
            answer += f"\n\n**Sources:** {', '.join(citations)}"
        history.append((message, answer))
    except Exception as e:
        history.append((message, f"Error: {e}"))
    return "", history


# ── Tab 3: Collection Browser ─────────────────────────────────────────────────

def load_collection() -> tuple:
    try:
        s = db.stats()
        rows = db.conn.execute(
            "SELECT arxiv_id, title, published, categories FROM papers ORDER BY fetched_at DESC LIMIT 100"
        ).fetchall()
        table_data = [[r[0], r[1][:60], str(r[2]), ", ".join(r[3][:2] if r[3] else [])] for r in rows]
        summary = f"Papers: {s['papers']} | Chunks: {s['chunks']} | Embeddings: {s['chunks_with_embeddings']}"
        return table_data, summary
    except Exception as e:
        return [], f"Error: {e}"


# ── Tab 4: Pipeline Status ────────────────────────────────────────────────────

def get_status() -> str:
    lines = []
    # Ollama
    if llm.is_healthy():
        lines.append(f"**Ollama:** Running — model `{settings.ollama.chat_model}`")
    else:
        lines.append(f"**Ollama:** NOT RUNNING — run `ollama pull {settings.ollama.chat_model}`")

    # DB
    try:
        s = db.stats()
        lines.append(f"**pgvector:** Connected — {s['papers']} papers, {s['chunks']} chunks")
    except Exception as e:
        lines.append(f"**pgvector:** Error — {e}")

    lines.append(f"**Embed model:** {settings.ollama.embed_model}")
    lines.append(f"**Chat model:** {settings.ollama.chat_model}")
    return "\n\n".join(lines)


# ── Build UI ──────────────────────────────────────────────────────────────────

def build_ui() -> gr.Blocks:
    with gr.Blocks(title="BioInfo Sidecar", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# BioInfo Sidecar\nLocal AI research assistant for bioinformatics — powered by Qwen + pgvector")

        with gr.Tab("Paper Discovery"):
            with gr.Row():
                search_query = gr.Textbox(label="Search Query", placeholder="e.g. CRISPR off-target detection")
                search_cats = gr.CheckboxGroup(
                    choices=list(BIO_CATEGORIES.keys()),
                    label="Category Filter",
                    value=["q-bio.GN", "cs.LG"],
                )
            search_days = gr.Slider(1, 365, value=30, label="Days back")
            search_btn = gr.Button("Search arXiv", variant="primary")
            search_status = gr.Textbox(label="Status", interactive=False)
            results_table = gr.Dataframe(
                headers=["arXiv ID", "Published", "Title", "Authors", "Categories"],
                interactive=False,
            )

            gr.Markdown("### Index a Paper")
            with gr.Row():
                index_id = gr.Textbox(label="arXiv ID", placeholder="2401.12345")
                index_btn = gr.Button("Download & Index", variant="secondary")
            index_status = gr.Textbox(label="Index Status", interactive=False)

            search_btn.click(search_papers, [search_query, search_cats, search_days], [results_table, search_status])
            index_btn.click(index_paper, [index_id], [index_status])

        with gr.Tab("Ask the Literature"):
            chatbot = gr.Chatbot(height=500, label="Research Chat")
            chat_input = gr.Textbox(label="Your question", placeholder="What is the state of the art for scRNA-seq batch correction?")
            with gr.Row():
                submit_btn = gr.Button("Ask", variant="primary")
                clear_btn = gr.Button("Clear")

            submit_btn.click(chat_respond, [chat_input, chatbot], [chat_input, chatbot])
            chat_input.submit(chat_respond, [chat_input, chatbot], [chat_input, chatbot])
            clear_btn.click(lambda: ([], ""), outputs=[chatbot, chat_input])

        with gr.Tab("Collection Browser"):
            refresh_btn = gr.Button("Refresh")
            collection_summary = gr.Textbox(label="Summary", interactive=False)
            collection_table = gr.Dataframe(
                headers=["arXiv ID", "Title", "Published", "Categories"],
                interactive=False,
            )
            refresh_btn.click(load_collection, outputs=[collection_table, collection_summary])
            demo.load(load_collection, outputs=[collection_table, collection_summary])

        with gr.Tab("Status"):
            status_btn = gr.Button("Refresh Status")
            status_md = gr.Markdown()
            status_btn.click(get_status, outputs=[status_md])
            demo.load(get_status, outputs=[status_md])

    return demo


def main(
    port: int = typer.Option(7860, "--port", "-p"),
    share: bool = typer.Option(False, "--share"),
) -> None:
    ui = build_ui()
    ui.launch(server_port=port, share=share)


if __name__ == "__main__":
    typer.run(main)
