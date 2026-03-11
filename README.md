# BioInfo Sidecar

A local-first AI research assistant for bioinformatics master's students.

Discover arXiv papers → parse scientific PDFs → embed & store in pgvector → query with Qwen via Ollama → explore in Gradio.

**Everything runs locally. No cloud API required for inference.**

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/scholih/bioinfo-sidecar.git
cd bioinfo-sidecar

# 2. Install Python deps
uv sync

# 3. Copy and edit environment
cp .env.example .env
# Edit .env with your Postgres password

# 4. Pull Ollama models
ollama pull qwen2.5:7b
ollama pull nomic-embed-text

# 5. Init database
psql postgres -f scripts/init_db.sql

# 6. Run the UI
uv run python sidecar/ui.py
# → open http://localhost:7860
```

---

## Stack

| Component | Technology |
|-----------|-----------|
| Local LLM | Ollama + Qwen2.5:7b |
| Embeddings | nomic-embed-text (768-dim) |
| PDF Parsing | Docling (primary) + Marker (fallback) |
| Vector DB | PostgreSQL + pgvector (HNSW) |
| RAG Agent | LangGraph (grade → retrieve → rewrite loop) |
| UI | Gradio |
| Package mgr | uv |

---

## CLI Tools

```bash
# Search arXiv
uv run python sidecar/fetch.py search "CRISPR off-target" --cat q-bio --days 30

# Parse a PDF
uv run python sidecar/parse.py paper.pdf --output chunks.json

# Index chunks into pgvector
uv run python sidecar/store.py index chunks.json

# Ask a question
uv run python sidecar/ask.py "What is the state of the art for RNA-seq normalization?"

# Launch UI
uv run python sidecar/ui.py
```

---

## Working with Claude Code

Read `WORKINSTRUCTIONS.md` for the full guide on how to use Claude Code as your pair-programming research mentor.

```bash
claude   # opens Claude Code in this directory
```

The `CLAUDE.md` in this repo configures Claude Code's behavior automatically.

---

## Tests

```bash
uv run pytest tests/ -v
uv run pytest tests/unit/ -v        # unit only
uv run pytest tests/integration/ -v # integration (requires running Postgres + Ollama)
```

---

## Project Structure

```
sidecar/
├── config.py          # Pydantic settings
├── fetch.py           # arXiv discovery CLI
├── parse.py           # PDF/HTML parsing CLI
├── embed.py           # Embedding generation
├── store.py           # pgvector index + search CLI
├── ask.py             # Agentic RAG CLI
├── ui.py              # Gradio dashboard
├── services/
│   ├── arxiv_client.py
│   ├── parser.py
│   ├── ollama_client.py
│   ├── pgvector_client.py
│   └── agents/
│       ├── state.py
│       ├── nodes.py
│       └── graph.py
└── models/
    ├── paper.py
    └── chunk.py
```
