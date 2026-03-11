.PHONY: install verify test lint format ui ask search clean

# Install all dependencies
install:
	uv sync

# Verify the full stack is operational
verify:
	@echo "=== Checking Ollama ==="
	curl -sf http://localhost:11434/api/tags | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Ollama OK — {len(d[\"models\"])} models loaded')"
	@echo "=== Checking pgvector ==="
	psql -U sidecar -d bioinfo_sidecar -c "SELECT count(*) as papers FROM papers; SELECT count(*) as chunks FROM chunks;" 2>&1 | grep -E "papers|chunks|row"
	@echo "=== Running unit tests ==="
	uv run pytest tests/unit/ -q
	@echo "=== All checks passed ==="

# Run tests
test:
	uv run pytest tests/ -v

test-unit:
	uv run pytest tests/unit/ -v

test-integration:
	uv run pytest tests/integration/ -v

# Code quality
lint:
	uv run ruff check sidecar/ tests/
	uv run mypy sidecar/

format:
	uv run ruff format sidecar/ tests/
	uv run ruff check --fix sidecar/ tests/

# Launch Gradio UI
ui:
	uv run python sidecar/ui.py

# Quick search (usage: make search Q="CRISPR off-target")
search:
	uv run python sidecar/fetch.py search "$(Q)" --days 30

# Ask a question (usage: make ask Q="What is CRISPR?")
ask:
	uv run python sidecar/ask.py "$(Q)"

# Init database (first time)
db-init:
	psql postgres -f scripts/init_db.sql

# Show index stats
stats:
	uv run python sidecar/store.py stats

# Clean generated artifacts
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
