# Setup Guide — BioInfo Sidecar

Step-by-step instructions to get everything running on a fresh machine.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.12+ | via `uv` (below) |
| PostgreSQL | 15 or 16 | brew / apt |
| pgvector extension | any | brew / apt |
| Ollama | latest | https://ollama.com |
| Git | any | pre-installed |
| Node.js | 18+ | only for Claude Code |

---

## Step 1 — Clone the Repo

```bash
git clone https://github.com/scholih/bioinfo-sidecar.git
cd bioinfo-sidecar
```

---

## Step 2 — Install uv (Python Package Manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Restart your shell or run:
source ~/.zshrc   # zsh
# source ~/.bashrc  # bash
```

Verify:
```bash
uv --version   # should print uv 0.5.x or later
```

---

## Step 3 — Install Python Dependencies

```bash
uv sync
```

This creates a `.venv/` and installs everything from `pyproject.toml`.

Verify the key packages:
```bash
uv run python -c "import docling; print('Docling OK')"
uv run python -c "import langchain; print('LangChain OK')"
uv run python -c "import gradio; print('Gradio OK')"
uv run python -c "import pgvector; print('pgvector OK')"
```

> **Note:** Docling downloads ML models on first use (~2GB). This happens automatically.

---

## Step 4 — Install and Start Ollama

### macOS

```bash
brew install ollama
# Ollama starts as a menu bar app — or run manually:
ollama serve
```

### Linux

```bash
curl -fsSL https://ollama.com/install.sh | sh
sudo systemctl start ollama
# or manually:
ollama serve &
```

### Pull Required Models

```bash
# Main chat model (4.7GB — Qwen 2.5 7B)
ollama pull qwen2.5:7b

# Embedding model (274MB)
ollama pull nomic-embed-text

# Optional: larger model for deeper analysis
ollama pull qwen2.5:14b

# Optional: code generation
ollama pull qwen2.5-coder:7b
```

> **Memory guide:**
> - `qwen2.5:7b` → needs 6GB RAM (8GB recommended)
> - `qwen2.5:14b` → needs 12GB RAM (Apple M2 Pro / 16GB+ Linux)
> - `nomic-embed-text` → <1GB, always fine

Verify Ollama:
```bash
ollama list                             # shows downloaded models
ollama run qwen2.5:7b "hello world"    # quick smoke test
```

---

## Step 5 — Install PostgreSQL + pgvector

### macOS

```bash
brew install postgresql@16 pgvector
brew services start postgresql@16

# Add postgres to PATH (add to your ~/.zshrc too)
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
```

### Ubuntu / Debian

```bash
# Install PostgreSQL 16
sudo apt install -y postgresql-16 postgresql-client-16

# Install pgvector for PG16
sudo apt install -y postgresql-16-pgvector

sudo systemctl start postgresql
```

### Fedora / RHEL

```bash
sudo dnf install postgresql16-server postgresql16-pgvector
sudo postgresql-16-setup initdb
sudo systemctl start postgresql-16
```

---

## Step 6 — Initialise the Database

```bash
# Run the init script (creates user, database, enables pgvector, creates tables)
psql postgres -f scripts/init_db.sql
```

If you get a permission error:
```bash
# macOS — run as the postgres superuser
sudo -u postgres psql -f scripts/init_db.sql

# Linux
sudo -u postgres psql -f scripts/init_db.sql
```

Verify:
```bash
psql -U sidecar -d bioinfo_sidecar -c "\dt"
# Should show: papers, chunks

psql -U sidecar -d bioinfo_sidecar -c "SELECT '[1,2,3]'::vector;"
# Should return: [1,2,3]
```

---

## Step 7 — Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and update the Postgres password if you changed it:
```bash
nano .env   # or: code .env
```

Minimal required settings (rest have good defaults):
```bash
POSTGRES_PASSWORD=changeme   # match what you set in step 6
OLLAMA_CHAT_MODEL=qwen2.5:7b # or qwen2.5:14b if you have the RAM
```

---

## Step 8 — Install Claude Code (Optional but Recommended)

```bash
npm install -g @anthropic/claude-code
claude --version
claude auth login   # authenticate with your Anthropic account
```

Open Claude Code in the project:
```bash
cd ~/path/to/bioinfo-sidecar
claude
```

Claude Code reads `CLAUDE.md` automatically and configures itself for this project.

---

## Step 9 — Verify Everything Works

```bash
make verify
```

Or manually:
```bash
# 1. Ollama responding?
curl http://localhost:11434/api/tags | python -m json.tool

# 2. DB connected?
psql -U sidecar -d bioinfo_sidecar -c "SELECT count(*) FROM papers;"

# 3. Search arXiv
uv run python sidecar/fetch.py search "CRISPR genomics" --max 3

# 4. Run tests
uv run pytest tests/unit/ -v

# 5. Launch UI
uv run python sidecar/ui.py
# → open http://localhost:7860
```

---

## Step 10 — Your First Paper

```bash
# Search for papers
uv run python sidecar/fetch.py search "single-cell RNA-seq batch correction" --cat q-bio.GN --days 60

# Index one paper (pick an arXiv ID from the results above)
uv run python sidecar/store.py index-paper 2401.13460

# Ask a question about it
uv run python sidecar/ask.py "What batch correction method was proposed?"
```

---

## Common Issues

### `ollama: command not found`
- macOS: run `brew install ollama` and reopen terminal
- Linux: the install script adds to PATH — run `source ~/.bashrc`

### `psql: error: connection refused`
```bash
# macOS
brew services restart postgresql@16
# Linux
sudo systemctl restart postgresql
```

### `extension "vector" does not exist`
pgvector not installed for your PostgreSQL version:
```bash
# macOS
brew install pgvector
# Ubuntu: install postgresql-16-pgvector (not postgresql-pgvector)
sudo apt install postgresql-16-pgvector
```

### Docling first run is very slow (10+ minutes)
This is normal — Docling downloads its ML models (~2GB) on first use. Subsequent runs are fast. You can use Marker as a faster alternative while waiting:
```bash
uv run python sidecar/parse.py paper.pdf --parser marker
```

### `uv: command not found` after install
```bash
export PATH="$HOME/.cargo/bin:$PATH"
# Add this line to your ~/.zshrc or ~/.bashrc
```

### Out of memory with qwen2.5:7b
Switch to a smaller model:
```bash
# Edit .env:
OLLAMA_CHAT_MODEL=qwen2.5:3b

# Pull the smaller model:
ollama pull qwen2.5:3b
```

---

## Platform-Specific Notes

### Apple Silicon (M1/M2/M3/M4)
- Ollama uses Metal GPU automatically — fast inference
- Docling uses MPS (Metal Performance Shaders) for PDF ML models
- 16GB RAM unified memory is ideal; 8GB works for 7b models

### Intel Mac / Linux with NVIDIA GPU
- Set `CUDA_VISIBLE_DEVICES=0` for GPU acceleration
- Ollama detects CUDA automatically
- `qwen2.5:14b` runs well on 12GB+ VRAM

### Linux CPU-only
- Works fine, just slower inference
- Expect 2-5 tok/s on qwen2.5:7b with 8 cores
- Use `qwen2.5:3b` for faster responses

### Windows (WSL2)
- Run everything inside WSL2 (Ubuntu 22.04 recommended)
- Ollama has a native Windows installer — install it outside WSL, then point `OLLAMA_BASE_URL` to `http://host.docker.internal:11434`

---

## Next Steps

1. Read `WORKINSTRUCTIONS.md` — how to work with Claude Code day-to-day
2. Read `CLAUDE.md` — what Claude Code knows about this project
3. Open `notebooks/01_arxiv_exploration.ipynb` — explore the arXiv API interactively
4. Start the Gradio UI: `uv run python sidecar/ui.py`
