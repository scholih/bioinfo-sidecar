"""LangGraph agent graph assembly."""

import logging
from functools import partial

from langgraph.graph import END, StateGraph

from sidecar.services.agents.nodes import (
    generate_node,
    grade_node,
    guardrail_node,
    retrieve_node,
    rewrite_node,
    route_after_grade,
    route_after_guardrail,
)
from sidecar.services.agents.state import AgentState
from sidecar.services.ollama_client import OllamaClient
from sidecar.services.pgvector_client import PgVectorClient

logger = logging.getLogger(__name__)


def build_graph(llm: OllamaClient, db: PgVectorClient) -> StateGraph:
    """Assemble and compile the RAG agent graph.

    Graph topology:
        guardrail → [out_of_scope → END] | [retrieve → grade → generate → END]
                                                              ↑          |
                                                         rewrite ←───────┘ (if no relevant chunks)
    """
    graph = StateGraph(AgentState)

    # Register nodes — use partial to inject dependencies
    graph.add_node("guardrail", partial(guardrail_node, llm=llm))
    graph.add_node("retrieve", partial(retrieve_node, db=db, llm=llm))
    graph.add_node("grade", partial(grade_node, llm=llm))
    graph.add_node("generate", partial(generate_node, llm=llm))
    graph.add_node("rewrite", partial(rewrite_node, llm=llm))

    # Terminal pseudo-nodes
    graph.add_node("out_of_scope", lambda s: {
        "answer": "I can only answer questions about bioinformatics and computational biology.",
        "citations": [],
    })
    graph.add_node("no_results", lambda s: {
        "answer": "I couldn't find relevant papers in the indexed literature for your question. "
                  "Try indexing more papers on this topic first.",
        "citations": [],
    })

    # Entry point
    graph.set_entry_point("guardrail")

    # Edges
    graph.add_conditional_edges("guardrail", route_after_guardrail)
    graph.add_edge("retrieve", "grade")
    graph.add_conditional_edges("grade", route_after_grade)
    graph.add_edge("rewrite", "retrieve")
    graph.add_edge("generate", END)
    graph.add_edge("out_of_scope", END)
    graph.add_edge("no_results", END)

    return graph.compile()


def run_agent(query: str, llm: OllamaClient, db: PgVectorClient) -> dict:
    """Run the RAG agent for a single query. Returns final state dict."""
    compiled = build_graph(llm, db)
    initial_state: AgentState = {
        "query": query,
        "rewritten_query": None,
        "retrieved_chunks": [],
        "graded_chunks": [],
        "answer": None,
        "citations": [],
        "rewrite_count": 0,
        "out_of_scope": False,
    }
    final_state = compiled.invoke(initial_state)
    logger.info("Agent finished: answer=%d chars, citations=%s", len(final_state.get("answer", "")), final_state.get("citations"))
    return final_state
