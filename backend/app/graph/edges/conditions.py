"""app/graph/edges/conditions.py — All routing logic."""

from app.core.config import get_settings
from app.graph.state import RAGState


def route_after_grader(state: RAGState) -> str:
    settings = get_settings()
    # If we have relevant docs, generate immediately
    if state.get("relevant_docs"):
        return "generator"
    # If the collection returned no candidates at all, answer with an explicit abstention.
    if not state.get("had_retrieval_candidates"):
        return "generator"
    # Candidates existed but none survived selection/grading — try a revised query.
    if state.get("retry_count", 0) >= settings.max_retries:
        return "generator"
    return "query_rewriter"


def route_after_judge(state: RAGState) -> str:
    """Routes based on the consolidated judge node (hallucination + quality)."""
    settings = get_settings()

    # If both checks passed, or we hit max retries, we finish
    passed = state.get("hallucination_passed") and state.get("quality_passed")

    if passed or state.get("retry_count", 0) >= settings.max_retries:
        return "__end__"

    # If we failed but still have retries, loop back to the rewriter
    return "query_rewriter"


# Maintain old names to avoid breaking the graph builder during transition if needed,
# but point them to the correct logic.
def route_after_hallucination_check(state: RAGState) -> str:
    return route_after_judge(state)
