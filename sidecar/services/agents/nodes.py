"""LangGraph node functions — each node takes AgentState, returns partial state update."""

import logging

from sidecar.services.agents.state import AgentState
from sidecar.services.ollama_client import OllamaClient
from sidecar.services.pgvector_client import PgVectorClient

logger = logging.getLogger(__name__)

MAX_REWRITES = 2

BIOINFORMATICS_SYSTEM = """You are an expert bioinformatics research assistant.
You answer questions about genomics, proteomics, transcriptomics, computational biology,
single-cell analysis, machine learning for biology, and related fields.
You base your answers strictly on the provided scientific literature excerpts.
Always cite papers by their arXiv ID when making specific claims."""

GUARDRAIL_SYSTEM = """You determine whether a question is related to bioinformatics,
computational biology, genomics, proteomics, or related life sciences fields.
Reply with exactly 'YES' if it is relevant, or 'NO' if it is not."""

GRADER_SYSTEM = """You assess whether a text chunk from a scientific paper is relevant
to answering the user's question. Reply with a score from 0.0 to 1.0.
Only reply with the number — no explanation."""


# ── Node functions ────────────────────────────────────────────────────────────

def guardrail_node(state: AgentState, llm: OllamaClient) -> dict:
    """Classify whether the query is within bioinformatics scope."""
    response = llm.chat(
        prompt=f"Is this question about bioinformatics or computational biology? '{state['query']}'",
        system=GUARDRAIL_SYSTEM,
    ).strip().upper()

    out_of_scope = response.startswith("NO")
    logger.debug("Guardrail: %s → out_of_scope=%s", state["query"][:60], out_of_scope)
    return {"out_of_scope": out_of_scope, "rewrite_count": 0}


def retrieve_node(state: AgentState, db: PgVectorClient, llm: OllamaClient) -> dict:
    """Retrieve relevant chunks using hybrid search."""
    query = state.get("rewritten_query") or state["query"]
    embedding = llm.embed([query])[0]
    chunks = db.hybrid_search(query=query, query_embedding=embedding, top_k=10)
    logger.info("Retrieved %d chunks for query: %s", len(chunks), query[:60])
    return {"retrieved_chunks": chunks}


def grade_node(state: AgentState, llm: OllamaClient) -> dict:
    """Grade each retrieved chunk for relevance. Keep score >= 0.5."""
    query = state.get("rewritten_query") or state["query"]
    graded: list[dict] = []

    for chunk in state["retrieved_chunks"]:
        prompt = f"Question: {query}\n\nChunk:\n{chunk['content'][:500]}\n\nRelevance score (0.0-1.0):"
        try:
            score_str = llm.chat(prompt=prompt, system=GRADER_SYSTEM).strip()
            score = float(score_str)
        except (ValueError, Exception):
            score = 0.0

        if score >= 0.5:
            graded.append({**chunk, "relevance_score": score})

    logger.info("Graded: %d/%d chunks passed relevance threshold", len(graded), len(state["retrieved_chunks"]))
    return {"graded_chunks": graded}


def generate_node(state: AgentState, llm: OllamaClient) -> dict:
    """Generate answer from graded chunks."""
    chunks = state["graded_chunks"]
    context = "\n\n---\n\n".join(
        f"[{c['arxiv_id']} — {c['section']}]\n{c['content']}"
        for c in chunks[:6]  # top 6 chunks
    )
    citations = list({c["arxiv_id"] for c in chunks})

    prompt = f"""Question: {state['query']}

Scientific literature:
{context}

Provide a clear, accurate answer based only on the above excerpts. Cite papers by arXiv ID."""

    answer = llm.chat(prompt=prompt, system=BIOINFORMATICS_SYSTEM)
    logger.info("Generated answer (%d chars), citing: %s", len(answer), citations)
    return {"answer": answer, "citations": citations}


def rewrite_node(state: AgentState, llm: OllamaClient) -> dict:
    """Rewrite the query to improve retrieval."""
    prompt = f"""The query '{state['query']}' returned no relevant scientific results.
Rewrite it to be more specific and use technical bioinformatics terminology.
Return only the rewritten query, nothing else."""

    rewritten = llm.chat(prompt=prompt).strip()
    logger.info("Rewrote query: '%s' → '%s'", state["query"][:60], rewritten[:60])
    return {
        "rewritten_query": rewritten,
        "rewrite_count": state.get("rewrite_count", 0) + 1,
        "retrieved_chunks": [],
        "graded_chunks": [],
    }


# ── Routing functions ─────────────────────────────────────────────────────────

def route_after_guardrail(state: AgentState) -> str:
    return "out_of_scope" if state["out_of_scope"] else "retrieve"


def route_after_grade(state: AgentState) -> str:
    if state["graded_chunks"]:
        return "generate"
    if state.get("rewrite_count", 0) >= MAX_REWRITES:
        return "no_results"
    return "rewrite"
