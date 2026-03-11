# CLAUDE.md — BioInformatics Sidecar Research Project

> This file configures Claude Code for a master's student in bioinformatics building
> a Python research sidecar: arXiv paper discovery, scientific PDF parsing, local LLM
> inference, vector search, and agentic RAG workflows.

---

## Who You Are Working With

You are assisting a **bioinformatics master's student** who:

- Has Python experience but is new to LLM tooling and vector databases
- Is building a **personal research assistant sidecar** — CLI tools that augment Claude Code
- Wants to work locally (privacy-first, no cloud API calls for core inference)
- Learns by doing: explain your reasoning, show alternatives, ask before assuming

**Your role:** Collaborative senior engineer + research mentor. Think out loud. Teach patterns, not just code.

---

## Project Goal

Build `~/sidecar/` — a collection of Python CLI scripts that a bioinformatics researcher uses
alongside Claude Code to:

1. **Discover** relevant arXiv papers (bioinformatics, genomics, ML for biology)
2. **Parse** scientific PDFs with high fidelity (figures, tables, equations, references)
3. **Embed & store** paper chunks in a local vector database (pgvector on PostgreSQL)
4. **Query** papers semantically via local Ollama/Qwen LLMs
5. **Orchestrate** multi-step research workflows with LangGraph agents
6. **Present** findings via a Gradio UI for interactive exploration

---

## Technology Stack to Research and Implement

### 1. Local LLM — Ollama + Qwen

**What to research on arXiv:**
- Search: `"Qwen" model architecture language model 2024`
- Search: `"local LLM inference" efficiency quantization`
- Key papers: Qwen2, Qwen2.5, Qwen2.5-Coder technical reports

**Implementation target:**
```bash
# Pull models
ollama pull qwen2.5:7b          # general reasoning
ollama pull qwen2.5:14b         # deeper analysis (if GPU memory allows)
ollama pull nomic-embed-text    # embeddings (768-dim)
ollama pull qwen2.5-coder:7b   # code generation tasks
```

**Sidecar scripts to build:**
- `sidecar/llm.py` — query Qwen via Ollama REST API
- `sidecar/embed.py` — generate embeddings via Ollama

**Key config decisions to validate:**
- Context window (128k for Qwen2.5)
- Temperature for scientific reasoning (0.1–0.3)
- System prompt for bioinformatics domain

---

### 2. Scientific PDF Parsing — Docling vs Alternatives

**What to research on arXiv:**
- Search: `"scientific document understanding" PDF parsing layout 2024`
- Search: `"document AI" table extraction figure recognition`
- Relevant: LayoutLM, NOUGAT, Marker, Docling (IBM Research) papers

**Tools to evaluate:**

| Tool | Strengths | Weaknesses | arXiv relevance |
|------|-----------|------------|-----------------|
| **Docling** (IBM) | Layout-aware, tables, figures, formulas | Slow on CPU | Best for structured bio papers |
| **Marker** | Fast, Markdown output, open source | Less accurate on tables | Good for text-heavy papers |
| **NOUGAT** (Meta) | Math/equation aware | Slow, hallucinations | Best for methods sections |
| **PyMuPDF** | Very fast, lightweight | No layout understanding | Good for plain text extraction |
| **pdfplumber** | Table extraction | Poor on complex layouts | Supplement tables |

**Recommendation for bioinformatics:** Docling primary, Marker fallback.

**Sidecar script to build:**
```python
# sidecar/parse.py
# Usage: python parse.py paper.pdf --output chunks.json --parser docling
```

**Research tasks:**
- [ ] Read Docling paper: https://arxiv.org/abs/2408.09869
- [ ] Compare parsing quality on 5 bioinformatics papers (genomics, proteomics, ML methods)
- [ ] Benchmark: parse time vs quality score (manual evaluation)

---

### 3. Vector Database — pgvector on PostgreSQL

**What to research on arXiv:**
- Search: `"approximate nearest neighbor" vector database benchmark 2024`
- Search: `"hybrid search" BM25 dense retrieval RAG`
- Key: ANN benchmarks (ann-benchmarks.com)

**Why pgvector over alternatives (Chroma, Qdrant, Weaviate):**
- Runs in same Postgres instance as paper metadata
- SQL + vector in one query (JOIN paper metadata with similarity search)
- ACID transactions — no consistency issues
- Familiar tooling for researchers who know SQL

**Schema to implement:**
```sql
-- papers table
CREATE TABLE papers (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    arxiv_id    TEXT UNIQUE NOT NULL,
    title       TEXT NOT NULL,
    authors     TEXT[],
    abstract    TEXT,
    categories  TEXT[],
    published   DATE,
    fetched_at  TIMESTAMPTZ DEFAULT NOW()
);

-- chunks table with vector column
CREATE TABLE chunks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id    UUID REFERENCES papers(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    section     TEXT,           -- "Abstract", "Methods", "Results", etc.
    content     TEXT NOT NULL,
    tokens      INTEGER,
    embedding   VECTOR(768),    -- nomic-embed-text dim
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW index for fast ANN search
CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

**Sidecar script to build:**
```python
# sidecar/store.py
# Usage: python store.py index chunks.json
#        python store.py search "CRISPR off-target detection methods" --top-k 10
```

---

### 4. arXiv Research Discovery

**What to research on arXiv:**
- Search: `"systematic literature review" automation NLP 2024`
- Search: `"paper recommendation" citation network embedding`

**arXiv categories for bioinformatics:**
```
q-bio.GN    Genomics
q-bio.QM    Quantitative Methods
q-bio.BM    Biomolecules
cs.LG       Machine Learning (for ML biology papers)
cs.AI       Artificial Intelligence
stat.ML     Statistics / Machine Learning
```

**Sidecar script to build:**
```python
# sidecar/fetch.py
# Usage: python fetch.py search "protein structure prediction" --cat q-bio --days 30
#        python fetch.py paper 2401.12345           # fetch specific paper
#        python fetch.py batch queries.txt          # batch search
```

**Pipeline to implement:**
1. Search arXiv API by query + category + date range
2. Filter by relevance (title/abstract keyword match)
3. Fetch PDF or HTML version
4. Parse → chunk → embed → store in pgvector

---

### 5. LangChain / LangGraph — Agentic RAG

**What to research on arXiv:**
- Search: `"retrieval augmented generation" scientific literature 2024`
- Search: `"agentic RAG" multi-step reasoning document retrieval`
- Search: `"graph of thought" chain of thought scientific reasoning`

**Architecture to build:**

```
User Query
    │
    ▼
[Guardrail Node] ──── off-topic? ──→ "I only answer bioinformatics questions"
    │
    ▼
[Retrieve Node] ──── pgvector hybrid search (BM25 + cosine)
    │
    ▼
[Grade Node] ──── Qwen grades each chunk relevance (0-1)
    │                              │
    ├── relevant docs found        └── no relevant docs
    │                                         │
    ▼                                         ▼
[Generate Node]                       [Rewrite Query Node]
    │                                         │
    ▼                                         └──→ back to Retrieve
[Answer + Citations]
```

**Key LangGraph concepts to learn:**
- `StateGraph` — define nodes and edges
- `TypedDict` state — typed state shared between nodes
- Conditional edges — branch based on grading results
- `ToolNode` — wrap vector search as a tool
- Streaming — stream tokens back to user

**Sidecar script to build:**
```python
# sidecar/ask.py
# Usage: python ask.py "What methods exist for single-cell RNA-seq batch correction?"
#        python ask.py --stream "Compare UMAP vs t-SNE for dimensionality reduction"
```

---

### 6. Gradio UI — Interactive Research Dashboard

**What to research on arXiv:**
- Search: `"interactive machine learning" user interface research tools`
- Gradio documentation: https://www.gradio.app/docs

**UI components to build:**

```
Tab 1: Paper Discovery
├── Search box (query + category filter + date range)
├── Results table (title, authors, abstract preview, relevance score)
└── "Index this paper" button → triggers parse → embed → store pipeline

Tab 2: Ask the Literature
├── Chat interface (streaming responses)
├── Source panel (cited chunks with paper links)
└── Query history

Tab 3: Collection Browser
├── Indexed papers list with metadata
├── Category breakdown chart
└── Timeline of indexed papers

Tab 4: Pipeline Status
├── Current ingestion jobs
└── Storage stats (papers indexed, total chunks, DB size)
```

**Sidecar script to build:**
```python
# sidecar/ui.py
# Usage: python ui.py --port 7860 --share false
```

---

## Directory Structure to Build

```
~/sidecar/
├── README.md                    # Setup and usage guide
├── CLAUDE.md                    # This file
├── pyproject.toml               # uv-managed dependencies
├── .env.example                 # Required environment variables
│
├── sidecar/
│   ├── __init__.py
│   ├── config.py                # Pydantic settings (reads .env)
│   ├── fetch.py                 # arXiv discovery CLI
│   ├── parse.py                 # PDF/HTML parsing CLI
│   ├── embed.py                 # Embedding generation
│   ├── store.py                 # pgvector index/search CLI
│   ├── ask.py                   # Agentic RAG CLI
│   ├── ui.py                    # Gradio interface
│   │
│   ├── services/
│   │   ├── arxiv_client.py      # arXiv API wrapper
│   │   ├── parser.py            # Docling/Marker abstraction
│   │   ├── ollama_client.py     # Ollama REST client
│   │   ├── pgvector_client.py   # asyncpg + pgvector queries
│   │   └── agents/
│   │       ├── state.py         # LangGraph AgentState
│   │       ├── nodes.py         # Graph node functions
│   │       └── graph.py         # Graph assembly
│   │
│   └── models/
│       ├── paper.py             # Paper dataclass
│       └── chunk.py             # Chunk dataclass
│
├── tests/
│   ├── unit/
│   └── integration/
│
└── notebooks/
    ├── 01_arxiv_exploration.ipynb
    ├── 02_parsing_comparison.ipynb
    ├── 03_embedding_quality.ipynb
    └── 04_rag_evaluation.ipynb
```

---

## Research Tasks (Build These as beads Issues)

Before writing code, research each topic and document findings:

```bash
bd create "Research: Qwen2.5 model selection for bioinformatics RAG"
bd create "Research: Docling vs Marker PDF parsing quality benchmark"
bd create "Research: pgvector HNSW index tuning for scientific text"
bd create "Research: LangGraph agentic RAG patterns 2024"
bd create "Research: arXiv paper relevance scoring approaches"
bd create "Implement: sidecar/fetch.py arXiv discovery"
bd create "Implement: sidecar/parse.py Docling parser"
bd create "Implement: sidecar/store.py pgvector indexer"
bd create "Implement: sidecar/ask.py LangGraph RAG agent"
bd create "Implement: sidecar/ui.py Gradio dashboard"
```

---

## Coding Standards

- **All Python via `uv run`** — never `python script.py`, always `uv run python script.py`
- **Async/await** for all I/O (HTTP, DB, file reads)
- **Type hints** on all functions
- **Dataclasses** for config and data models
- **Under 50 lines per function** — extract helpers aggressively
- **Test first** — write failing test before implementation (TDD)
- Line length: 100 chars

---

## Environment Variables

```bash
# .env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text
OLLAMA_CHAT_MODEL=qwen2.5:7b

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=bioinfo_sidecar
POSTGRES_USER=sidecar
POSTGRES_PASSWORD=changeme

ARXIV_MAX_RESULTS=50
ARXIV_RATE_LIMIT_SECONDS=3

GRADIO_PORT=7860
GRADIO_SHARE=false

LOG_LEVEL=INFO
```

---

## How Claude Code Should Behave

1. **Research before implementing** — when a new technology appears, ask: "should we read the arXiv paper first?"
2. **Show the benchmark** — for parser/model choices, run a quick comparison on real bioinformatics papers
3. **Explain the tradeoff** — always present 2-3 options with pros/cons before implementing
4. **Think bioinformatics-first** — domain matters: gene/protein names, GO terms, PubMed IDs, sequence data
5. **Verify locally** — all inference runs on Ollama; never send paper content to cloud APIs without asking
6. **Use TDD** — write the test, watch it fail, write the code
7. **One topic at a time** — don't overwhelm; complete and validate before moving on
