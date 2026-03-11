"""LangGraph agent state — shared across all graph nodes."""

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State passed between LangGraph nodes."""

    query: str                          # original user question
    rewritten_query: str | None         # rewritten query (if retrieval failed)
    retrieved_chunks: list[dict]        # raw chunks from pgvector
    graded_chunks: list[dict]           # chunks after relevance grading
    answer: str | None                  # final generated answer
    citations: list[str]                # arxiv_ids cited in the answer
    rewrite_count: int                  # how many times we've rewritten the query
    out_of_scope: bool                  # guardrail flagged this as off-topic
