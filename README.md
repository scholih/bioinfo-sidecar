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

> Full platform-specific setup (macOS, Ubuntu, WSL2) → **[SETUP.md](SETUP.md)**

---

## Stack

| Component | Technology |
|-----------|-----------|
| Local LLM | Ollama + Qwen2.5:7b |
| Embeddings | nomic-embed-text (768-dim) |
| PDF Parsing | Docling (primary) + Marker (fallback) |
| Vector DB | PostgreSQL + pgvector (HNSW index) |
| RAG Agent | LangGraph (guardrail → retrieve → grade → rewrite loop) |
| UI | Gradio (4-tab dashboard) |
| Package mgr | uv |

---

## Example Use Cases

### 1. Build a Literature Base for Your Thesis Chapter

```bash
# Find recent papers on your topic
uv run python sidecar/fetch.py search "single-cell RNA-seq batch correction" \
  --cat q-bio.GN --cat cs.LG --days 90 --output papers.json

# Index a specific paper end-to-end
uv run python sidecar/parse.py download-and-parse https://arxiv.org/pdf/2401.13460 \
  --arxiv-id 2401.13460 --output chunks.json

uv run python sidecar/store.py index chunks.json --arxiv-id 2401.13460 \
  --title "Scalable batch correction" --authors "Smith, Jones"

# Now ask questions against it
uv run python sidecar/ask.py "What normalization strategy did they use and why?"
```

---

### 2. Compare Methods for Your Methods Section

```bash
# Index several competing papers, then interrogate them together
uv run python sidecar/ask.py \
  "Compare the batch correction approaches across the indexed papers. \
   What are the tradeoffs between Harmony, scVI, and ComBat-seq?"
```

---

### 3. Explore arXiv for Thesis Background

```bash
# Genomics + ML papers from the last 60 days
uv run python sidecar/fetch.py search "transformer protein structure prediction" \
  --cat q-bio.BM --cat cs.LG --days 60

# List all supported bioinformatics categories
uv run python sidecar/fetch.py categories
```

---

### 4. Validate Your Index

```bash
# Semantic search — does the index understand your domain?
uv run python sidecar/store.py search \
  "CRISPR off-target detection machine learning" --top-k 5

# Check what's indexed
uv run python sidecar/store.py stats
```

---

### 5. Interactive Research Session in Gradio

```bash
uv run python sidecar/ui.py
```

Opens at `http://localhost:7860` with four tabs:

| Tab | What you can do |
|-----|----------------|
| **Paper Discovery** | Search arXiv, filter by category and date, one-click index |
| **Ask the Literature** | Chat with your indexed papers, get answers with citations |
| **Collection Browser** | See all indexed papers, filter by topic |
| **Status** | Verify Ollama, pgvector, model and index health |

---

### 6. Use with Claude Code (Recommended)

```bash
claude   # opens Claude Code — reads CLAUDE.md automatically
```

Example sessions with Claude Code:

```
"Search arXiv for papers about spatial transcriptomics from 2024.
 Help me pick the 5 most relevant to my thesis on cell-cell communication."

"I want to implement a sidecar script that fetches my gene list from
 Ensembl and annotates each gene with GO terms. Write the test first."

"I indexed 20 papers. Help me draft the Related Work section of my thesis
 based on what's in the collection."
```

> Full co-development guide → **[WORKINSTRUCTIONS.md](WORKINSTRUCTIONS.md)**

---

## CLI Reference

```bash
# ── Paper Discovery ──────────────────────────────────────────────────────────
uv run python sidecar/fetch.py search "QUERY" [--cat CATEGORY] [--days N] [--max N]
uv run python sidecar/fetch.py paper ARXIV_ID
uv run python sidecar/fetch.py categories

# ── PDF Parsing ──────────────────────────────────────────────────────────────
uv run python sidecar/parse.py parse FILE.pdf [--arxiv-id ID] [--output chunks.json]
uv run python sidecar/parse.py download-and-parse PDF_URL --arxiv-id ID

# ── Vector Index ─────────────────────────────────────────────────────────────
uv run python sidecar/store.py index chunks.json [--arxiv-id ID] [--title "..."]
uv run python sidecar/store.py search "QUERY" [--top-k 5] [--vector-only]
uv run python sidecar/store.py stats

# ── RAG Agent ────────────────────────────────────────────────────────────────
uv run python sidecar/ask.py "QUESTION" [--verbose]

# ── Gradio UI ────────────────────────────────────────────────────────────────
uv run python sidecar/ui.py [--port 7860] [--share]

# ── Make shortcuts ───────────────────────────────────────────────────────────
make verify                        # check full stack health
make ui                            # launch Gradio
make search Q="RNA-seq methods"    # quick arXiv search
make ask Q="What is UMAP?"         # quick RAG query
make test                          # run all tests
make format                        # ruff format + lint fix
```

---

## Extend It

The sidecar is designed to grow with your thesis. Suggested additions:

| Script | What it would do |
|--------|----------------|
| `sidecar/bio.py` | Biopython + Entrez — fetch sequences, BLAST, GO enrichment |
| `sidecar/thesis.py` | Draft Methods/Related Work sections, format citations |
| `sidecar/pathway.py` | KEGG/Reactome/STRING pathway queries from a gene list |
| `sidecar/structure.py` | PDB fetch, protein embedding via ESM-2 |
| `sidecar/lit.py` | Semantic Scholar citation graph traversal |

> Full package catalogue (100+ curated tools by research phase) → **[docs/PACKAGES.md](docs/PACKAGES.md)**

---

## Tests

```bash
uv run pytest tests/ -v
uv run pytest tests/unit/ -v         # unit only (no services required)
uv run pytest tests/integration/ -v  # requires running Postgres + Ollama
```

---

## Documentation

| File | Contents |
|------|---------|
| [SETUP.md](SETUP.md) | Step-by-step install — macOS, Ubuntu, WSL2, common errors |
| [CLAUDE.md](CLAUDE.md) | Claude Code agent configuration for this project |
| [WORKINSTRUCTIONS.md](WORKINSTRUCTIONS.md) | Daily workflow, 5 weekly milestones, prompting guide |
| [docs/PACKAGES.md](docs/PACKAGES.md) | 100+ curated bioinformatics packages by research phase |

---

## Project Structure

```
bioinfo-sidecar/
├── SETUP.md                     # Full setup guide
├── CLAUDE.md                    # Claude Code configuration
├── WORKINSTRUCTIONS.md          # Co-development guide
├── pyproject.toml               # uv-managed dependencies
├── Makefile                     # Common task shortcuts
├── scripts/
│   └── init_db.sql              # PostgreSQL + pgvector schema
├── sidecar/
│   ├── config.py                # Pydantic settings (reads .env)
│   ├── fetch.py                 # arXiv discovery CLI
│   ├── parse.py                 # Docling/Marker PDF parser CLI
│   ├── store.py                 # pgvector index + search CLI
│   ├── ask.py                   # LangGraph RAG agent CLI
│   ├── ui.py                    # Gradio 4-tab dashboard
│   ├── services/
│   │   ├── arxiv_client.py
│   │   ├── parser.py            # Docling → Marker → PyMuPDF fallback
│   │   ├── ollama_client.py     # Qwen chat + nomic embeddings
│   │   ├── pgvector_client.py   # Hybrid BM25 + vector search
│   │   └── agents/
│   │       ├── state.py         # LangGraph AgentState
│   │       ├── nodes.py         # guardrail, retrieve, grade, generate, rewrite
│   │       └── graph.py         # StateGraph assembly
│   └── models/
│       ├── paper.py
│       └── chunk.py
├── tests/
│   ├── conftest.py              # Shared fixtures + mocks
│   ├── unit/
│   │   ├── test_models.py
│   │   └── test_agents.py
│   └── integration/
└── docs/
    └── PACKAGES.md              # Curated package reference by research phase
```
