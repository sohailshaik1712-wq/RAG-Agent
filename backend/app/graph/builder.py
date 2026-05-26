"""app/graph/builder.py — Compiles the LangGraph RAG agent once at startup."""

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.core.config import get_settings
from app.graph.edges.conditions import (
    route_after_grader,
    route_after_hallucination_check,
)
from app.graph.nodes.generator import generator_node
from app.graph.nodes.judge import judge_node
from app.graph.nodes.query_rewriter import query_rewriter_node
from app.graph.nodes.relevance_grader import relevance_grader_node
from app.graph.nodes.retriever import retriever_node
from app.graph.state import RAGState


@lru_cache(maxsize=1)
def build_graph():
    graph = StateGraph(RAGState)

    graph.add_node("query_rewriter", query_rewriter_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("relevance_grader", relevance_grader_node)
    graph.add_node("generator", generator_node)
    graph.add_node("judge", judge_node)

    graph.add_edge(START, "query_rewriter")
    graph.add_edge("query_rewriter", "retriever")
    graph.add_edge("retriever", "relevance_grader")
    graph.add_edge("generator", "judge")

    graph.add_conditional_edges(
        "relevance_grader",
        route_after_grader,
        {"generator": "generator", "query_rewriter": "query_rewriter"},
    )
    graph.add_conditional_edges(
        "judge",
        route_after_hallucination_check,
        {"__end__": END, "query_rewriter": "query_rewriter"},
    )

    return graph.compile()


def get_graph_config() -> dict:
    settings = get_settings()
    return {
        "recursion_limit": max(20, 6 + (settings.max_retries * 6)),
    }
