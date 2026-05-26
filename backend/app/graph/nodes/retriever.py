"""app/graph/nodes/retriever.py — Retrieves docs from the conversation's collection."""

from app.core.config import get_settings
from app.core.logging import get_logger
from app.graph.state import RAGState
from app.services.evidence import select_evidence
from app.services.vector_store import get_collection

logger = get_logger(__name__)


async def retriever_node(state: RAGState) -> dict:
    settings = get_settings()
    collection = get_collection(state["collection_name"])
    query = state["rewritten_question"]

    # PGVector search is usually synchronous in LangChain Postgres
    results = collection.similarity_search_with_relevance_scores(
        query, k=max(settings.retrieval_top_k, settings.retrieval_candidate_k)
    )
    docs = select_evidence(
        results,
        top_k=settings.retrieval_top_k,
        score_threshold=settings.retrieval_score_threshold,
        diversity_threshold=settings.retrieval_diversity_threshold,
    )
    feedback = (
        ""
        if docs
        else (
            f"No candidate evidence met the relevance threshold "
            f"({settings.retrieval_score_threshold:.2f}); reformulate the search."
        )
    )

    logger.info(
        "docs_retrieved",
        candidates=len(results),
        selected=len(docs),
        collection=state["collection_name"],
    )
    return {
        "had_retrieval_candidates": bool(results),
        "retrieved_docs": docs,
        "retrieval_feedback": feedback,
    }
