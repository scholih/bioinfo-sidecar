# Work Instructions — BioInformatics Sidecar with Claude Code

> For: Master's student in bioinformatics
> Goal: Build a local AI research assistant sidecar using arXiv, Ollama/Qwen, pgvector, Docling, LangGraph, and Gradio
> Supervisor tool: Claude Code (claude.ai/code)

---

## Part 1 — One-Time Machine Setup

### 1.1 Install Prerequisites

```bash
# macOS (Apple Silicon — M1/M2/M3)
brew install postgresql@16 ollama git

# Ubuntu/Debian
sudo apt install postgresql-16 postgresql-16-contrib git curl

# Python toolchain (all platforms)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 1.2 Install Claude Code

```bash
npm install -g @anthropic/claude-code
claude --version       # verify install
claude                 # opens interactive session — follow auth steps
```

### 1.3 Install and Configure Ollama

```bash
# Start Ollama (macOS: runs as menu bar app after brew install)
ollama serve           # if not running as service

# Pull required models — do this once, they persist locally
ollama pull qwen2.5:7b             # 4.7GB — main chat model
ollama pull nomic-embed-text       # 274MB — embeddings
ollama pull qwen2.5-coder:7b       # 4.7GB — code tasks (optional)

# Verify
ollama list
ollama run qwen2.5:7b "What is a hidden Markov model in genomics?"
```

> **Memory requirements:**
> - qwen2.5:7b → 6GB RAM minimum (8GB recommended)
> - qwen2.5:14b → 12GB RAM (Apple M2 Pro or better)
> - nomic-embed-text → <1GB, always fine

### 1.4 Set Up PostgreSQL + pgvector

```bash
# macOS
brew install pgvector

# Ubuntu
sudo apt install postgresql-16-pgvector

# Create database
psql postgres <<'SQL'
CREATE USER sidecar WITH PASSWORD 'changeme';
CREATE DATABASE bioinfo_sidecar OWNER sidecar;
\c bioinfo_sidecar
CREATE EXTENSION vector;
GRANT ALL ON SCHEMA public TO sidecar;
SQL

# Verify pgvector works
psql -U sidecar -d bioinfo_sidecar -c "SELECT '[1,2,3]'::vector;"
```

### 1.5 Bootstrap Your Sidecar Project

```bash
# Create project directory
mkdir -p ~/sidecar
cd ~/sidecar

# Initialize Python project with uv
uv init --name bioinfo-sidecar --python 3.12

# Add core dependencies
uv add \
  docling \
  marker-pdf \
  langchain \
  langgraph \
  langchain-community \
  langchain-ollama \
  gradio \
  psycopg[binary,pool] \
  pgvector \
  httpx \
  arxiv \
  pydantic-settings \
  rich \
  typer

# Add dev dependencies
uv add --dev pytest pytest-asyncio ruff mypy ipykernel

# Verify install
uv run python -c "import docling; print('Docling OK')"
uv run python -c "import langchain; print('LangChain OK')"
uv run python -c "import gradio; print('Gradio OK')"
```

### 1.6 Configure Environment

```bash
# Copy template and edit
cp .env.example .env
nano .env    # fill in your values (Postgres password etc.)

# Recommended .env for local dev:
cat > .env << 'EOF'
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
EOF
```

### 1.7 Initialize Beads Issue Tracker

```bash
# Install beads (Claude Code task tracker)
npm install -g @anthropic/claude-code  # already installed
bd init       # run from ~/sidecar — creates .beads/ directory

# Create your initial research backlog
bd create "Research: Read Docling arXiv paper 2408.09869 and benchmark on 5 papers"
bd create "Research: Qwen2.5 model selection — compare 7b vs 14b on bio questions"
bd create "Research: pgvector HNSW vs IVFFlat index for 768-dim embeddings"
bd create "Research: LangGraph RAG patterns — grade-retrieve-rewrite loop"
bd create "Implement: sidecar/config.py Pydantic settings"
bd create "Implement: sidecar/fetch.py arXiv CLI"
bd create "Implement: sidecar/parse.py Docling/Marker parser"
bd create "Implement: sidecar/store.py pgvector index + search"
bd create "Implement: sidecar/ask.py LangGraph RAG agent"
bd create "Implement: sidecar/ui.py Gradio dashboard"
```

---

## Part 2 — Daily Session Workflow

### 2.1 Start Every Session

```bash
cd ~/sidecar

# 1. Sync remote task state (if working with supervisor)
bd dolt pull

# 2. Check what's ready to work on
bd ready

# 3. Resume anything in-progress
bd list --status=in_progress

# 4. Open Claude Code
claude
```

### 2.2 Working WITH Claude Code (Not Just Alongside It)

Claude Code is your **pair programmer and research mentor**. Use it for:

**Research sessions:**
```
"Claude, I want to research Docling for parsing bioinformatics PDFs.
Help me find the key arXiv papers, summarize the architecture, and
design a comparison benchmark."
```

**Implementation sessions:**
```
"I'm working on issue BIO-003: sidecar/parse.py. Let's use TDD —
write the test first, then implement Docling parsing with section detection."
```

**Debugging sessions:**
```
"I'm getting dimension mismatch errors when storing embeddings in pgvector.
Here's the error: [paste error]. Help me trace the root cause."
```

**Architecture sessions:**
```
"Before I implement the LangGraph agent, help me design the state
and nodes. Show me 2-3 different graph topologies and their tradeoffs
for a RAG system over scientific papers."
```

### 2.3 The Research-First Rule

**Never implement before researching.** For each technology:

1. Ask Claude Code: "Find the key arXiv papers on [topic] from 2023-2025"
2. Read the paper abstract + methods section
3. Ask: "What are the key design decisions we should replicate?"
4. Only then: "Now let's implement it"

```bash
# Good workflow example:
# Morning: Read Docling paper, run comparison benchmark
# Afternoon: Implement sidecar/parse.py based on findings
# Evening: Write tests, validate, commit

bd update BIO-001 --status=in_progress
# ... research session with Claude Code ...
bd remember "Docling outperforms Marker on table-heavy papers (biology methods sections). Use Docling as primary, Marker as fallback for text-only papers. Benchmark: Docling 12s/paper, Marker 2s/paper on M2."
bd close BIO-001 --reason="Benchmarked Docling vs Marker on 5 bioinformatics papers. Docling wins on quality. Results in notebooks/02_parsing_comparison.ipynb"
```

### 2.4 Commit Workflow

```bash
# After each meaningful implementation
git add sidecar/parse.py tests/unit/test_parse.py
git commit -m "feat: implement Docling parser with section detection

- Detects Abstract, Methods, Results, Discussion sections
- Falls back to Marker for text-only papers
- Adds tests for 3 real bioinformatics papers

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Part 3 — Learning Milestones

Work through these in order. Each milestone has a research phase and an implementation phase.

### Milestone 1: Foundation (Week 1)

**Research:**
- [ ] Understand what RAG is — read: https://arxiv.org/abs/2312.10997
- [ ] Understand vector embeddings — run: `python notebooks/03_embedding_quality.ipynb`
- [ ] Understand pgvector HNSW index — read: https://arxiv.org/abs/1603.09320

**Implement:**
- [ ] `sidecar/config.py` — Pydantic settings loading from `.env`
- [ ] `sidecar/fetch.py` — arXiv search and download
- [ ] Database schema — run migration script

**Validate:**
```bash
uv run python sidecar/fetch.py search "CRISPR off-target detection" --cat q-bio --days 30
# Should return 10+ papers with titles and abstracts
```

---

### Milestone 2: Parsing Pipeline (Week 2)

**Research:**
- [ ] Read Docling paper: https://arxiv.org/abs/2408.09869
- [ ] Compare: parse 5 real papers with Docling AND Marker
- [ ] Evaluate section detection quality (does it correctly identify Methods vs Results?)

**Implement:**
- [ ] `sidecar/parse.py` — parse PDF → structured chunks with section labels
- [ ] Chunking strategy — 512 token chunks with 64 token overlap
- [ ] Section metadata extraction — title, authors, abstract, DOI

**Validate:**
```bash
uv run python sidecar/parse.py paper.pdf --output chunks.json
cat chunks.json | python -c "import json,sys; d=json.load(sys.stdin); print(f'{len(d)} chunks, sections: {set(c[\"section\"] for c in d)}')"
# Expected: 40-80 chunks, sections: {'Abstract', 'Introduction', 'Methods', 'Results', 'Discussion'}
```

---

### Milestone 3: Vector Store (Week 3)

**Research:**
- [ ] Read pgvector documentation on HNSW parameters (m, ef_construction, ef_search)
- [ ] Experiment: what embedding model gives best semantic similarity for bioinformatics terms?
  - Test: "RNA sequencing" vs "transcriptomics" — should be high cosine similarity
  - Test: "PCR amplification" vs "CRISPR editing" — should be lower

**Implement:**
- [ ] `sidecar/embed.py` — batch embedding generation via Ollama
- [ ] `sidecar/store.py` — index chunks + search
- [ ] Full pipeline: `fetch → parse → embed → store`

**Validate:**
```bash
# Index a paper
uv run python sidecar/fetch.py paper 2401.12345 | \
  uv run python sidecar/parse.py --stdin | \
  uv run python sidecar/store.py index --stdin

# Search
uv run python sidecar/store.py search "what normalization method was used?" --top-k 5
# Should return relevant Methods section chunks
```

---

### Milestone 4: Agentic RAG (Week 4)

**Research:**
- [ ] Read LangGraph documentation: https://langchain-ai.github.io/langgraph/
- [ ] Read: https://arxiv.org/abs/2401.15884 (CRAG — Corrective RAG)
- [ ] Understand: retrieval grading, query rewriting, self-correction loops

**Implement:**
- [ ] `sidecar/services/agents/state.py` — AgentState TypedDict
- [ ] `sidecar/services/agents/nodes.py` — retrieve, grade, generate, rewrite nodes
- [ ] `sidecar/services/agents/graph.py` — assemble StateGraph
- [ ] `sidecar/ask.py` — CLI wrapper with streaming output

**Validate:**
```bash
uv run python sidecar/ask.py "What methods exist for correcting batch effects in single-cell RNA-seq data?"
# Should: retrieve 5-10 relevant chunks, grade them, generate answer with paper citations
# If no relevant chunks: rewrite query and retry
```

---

### Milestone 5: Gradio UI (Week 5)

**Research:**
- [ ] Gradio Blocks API — tab layout, chat interface, streaming
- [ ] gr.Dataframe for search results
- [ ] gr.ChatInterface with custom submit handler

**Implement:**
- [ ] `sidecar/ui.py` — 4-tab Gradio app
- [ ] Tab 1: Paper search + one-click indexing
- [ ] Tab 2: RAG chat with source citations
- [ ] Tab 3: Collection browser
- [ ] Tab 4: Pipeline status

**Launch:**
```bash
uv run python sidecar/ui.py
# Open: http://localhost:7860
```

---

## Part 4 — Asking Claude Code Effectively

### Good Prompts

**For research:**
```
"Search arXiv for papers about hybrid BM25 + dense retrieval for scientific text.
Find papers from 2023-2025. Summarize the key findings and help me decide
which approach to use in our pgvector implementation."
```

**For implementation with TDD:**
```
"I want to implement the Ollama embedding client in sidecar/services/ollama_client.py.
Start with the test. The function should: accept a list of strings, call Ollama's
/api/embeddings endpoint, return List[List[float]]. Write the failing test first."
```

**For debugging:**
```
"I'm getting this error when indexing embeddings:
[paste full traceback]
The embedding has shape (1, 768) but the pgvector column expects (768,).
Trace the root cause and suggest a fix."
```

**For architecture decisions:**
```
"I need to design the LangGraph agent for RAG. Show me two approaches:
(1) simple linear: retrieve → grade → generate
(2) corrective: retrieve → grade → (generate | rewrite → retrieve again)
Explain the tradeoffs and recommend which to implement for a research assistant
that needs high-quality answers, not speed."
```

### Anti-patterns to Avoid

| Don't | Do instead |
|-------|-----------|
| "Write me the whole sidecar" | One function, with tests, at a time |
| "Fix this error" (no context) | Paste full traceback + relevant code |
| "Is Docling good?" | "Compare Docling vs Marker on this specific paper" |
| Implement before researching | Research → benchmark → design → implement |
| Skip the failing test | Always write the red test first |

---

## Part 5 — When You Get Stuck

### Common Issues

**Ollama model too slow:**
```bash
# Check if using GPU
ollama ps                    # shows running models
# If CPU-only: check Apple Metal or CUDA is available
ollama run qwen2.5:7b --verbose  # shows inference speed (tokens/s)
# Minimum: 10 tok/s for usable experience
```

**pgvector dimension mismatch:**
```bash
# Check your column dimension vs your embedding model output
psql -U sidecar -d bioinfo_sidecar -c "\d chunks"
# Embedding column should match: nomic-embed-text = 768, BGE-M3 = 1024
ollama run nomic-embed-text --format json  # test embedding dims
```

**Docling parsing slow:**
```bash
# Docling uses deep learning — first run downloads models
# Expected: 10-60s per paper on CPU, 2-10s on GPU
# Speed up: use Marker for initial prototyping, switch to Docling for final pipeline
```

**LangGraph state errors:**
```bash
# Always check: are you mutating state in place?
# LangGraph requires returning new state dict from each node
# Use: return {**state, "new_key": new_value}  # correct
# Not: state["new_key"] = new_value; return state  # wrong
```

### Escalation Path

1. Check `bd memories <keyword>` — was this solved before?
2. Ask Claude Code with full error context
3. Check the relevant arXiv paper (there's usually a methods section on your exact problem)
4. Open a GitHub issue on the relevant library
5. Ask your supervisor with: error message + what you tried + what you found in the arXiv paper

---

## Part 6 — End of Session Checklist

```bash
# 1. Save any important discoveries
bd remember "Key finding: X is better than Y for Z because..."

# 2. Close completed issues
bd close BIO-005 --reason="Implemented fetch.py with search and single-paper download"

# 3. Commit your work
git add -p   # review changes interactively
git commit -m "feat: implement arXiv fetch CLI with category filtering"

# 4. Note what's next
bd update BIO-006 --status=ready --note="Start with the test for parse.py section detection"

# 5. Push task state
bd dolt push
```

---

## Quick Reference

```bash
# Fetch papers
uv run python sidecar/fetch.py search "protein folding" --cat q-bio --days 7

# Parse a paper
uv run python sidecar/parse.py paper.pdf --output chunks.json

# Index to pgvector
uv run python sidecar/store.py index chunks.json

# Ask a question
uv run python sidecar/ask.py "What is the state of the art for RNA-seq normalization?"

# Launch UI
uv run python sidecar/ui.py

# Run tests
uv run pytest tests/ -v

# Check Ollama models
ollama list

# Check DB
psql -U sidecar -d bioinfo_sidecar -c "SELECT count(*) FROM chunks;"
```

---

*Built with Claude Code — arXiv-native, privacy-first, local-first.*
