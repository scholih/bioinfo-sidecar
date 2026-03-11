"""Unit tests for LangGraph agent nodes."""

import pytest

from sidecar.services.agents.nodes import (
    MAX_REWRITES,
    grade_node,
    guardrail_node,
    route_after_grade,
    route_after_guardrail,
)
from sidecar.services.agents.state import AgentState


def make_state(**overrides) -> AgentState:
    base: AgentState = {
        "query": "What is CRISPR?",
        "rewritten_query": None,
        "retrieved_chunks": [],
        "graded_chunks": [],
        "answer": None,
        "citations": [],
        "rewrite_count": 0,
        "out_of_scope": False,
    }
    base.update(overrides)
    return base


class TestGuardrailNode:
    def test_bioinformatics_query_passes(self, mock_llm) -> None:
        mock_llm.chat.return_value = "YES"
        result = guardrail_node(make_state(), llm=mock_llm)
        assert result["out_of_scope"] is False

    def test_off_topic_query_blocked(self, mock_llm) -> None:
        mock_llm.chat.return_value = "NO"
        result = guardrail_node(make_state(query="What is the weather today?"), llm=mock_llm)
        assert result["out_of_scope"] is True

    def test_rewrite_count_reset(self, mock_llm) -> None:
        mock_llm.chat.return_value = "YES"
        result = guardrail_node(make_state(), llm=mock_llm)
        assert result["rewrite_count"] == 0


class TestRouting:
    def test_route_to_retrieve_when_in_scope(self) -> None:
        state = make_state(out_of_scope=False)
        assert route_after_guardrail(state) == "retrieve"

    def test_route_to_out_of_scope(self) -> None:
        state = make_state(out_of_scope=True)
        assert route_after_guardrail(state) == "out_of_scope"

    def test_route_to_generate_when_chunks_found(self) -> None:
        state = make_state(graded_chunks=[{"content": "test"}])
        assert route_after_grade(state) == "generate"

    def test_route_to_rewrite_when_no_chunks(self) -> None:
        state = make_state(graded_chunks=[], rewrite_count=0)
        assert route_after_grade(state) == "rewrite"

    def test_route_to_no_results_after_max_rewrites(self) -> None:
        state = make_state(graded_chunks=[], rewrite_count=MAX_REWRITES)
        assert route_after_grade(state) == "no_results"


class TestGradeNode:
    def test_relevant_chunks_kept(self, mock_llm) -> None:
        mock_llm.chat.return_value = "0.9"
        state = make_state(
            retrieved_chunks=[{"content": "CRISPR off-target detection", "arxiv_id": "2401.00001"}]
        )
        result = grade_node(state, llm=mock_llm)
        assert len(result["graded_chunks"]) == 1
        assert result["graded_chunks"][0]["relevance_score"] == pytest.approx(0.9)

    def test_irrelevant_chunks_filtered(self, mock_llm) -> None:
        mock_llm.chat.return_value = "0.2"
        state = make_state(
            retrieved_chunks=[{"content": "Unrelated content", "arxiv_id": "2401.00002"}]
        )
        result = grade_node(state, llm=mock_llm)
        assert len(result["graded_chunks"]) == 0

    def test_invalid_score_treated_as_zero(self, mock_llm) -> None:
        mock_llm.chat.return_value = "not a number"
        state = make_state(
            retrieved_chunks=[{"content": "Some content", "arxiv_id": "2401.00003"}]
        )
        result = grade_node(state, llm=mock_llm)
        assert len(result["graded_chunks"]) == 0
