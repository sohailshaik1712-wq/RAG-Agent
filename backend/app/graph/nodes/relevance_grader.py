"""app/graph/nodes/relevance_grader.py — Optimized Bulk Relevance Grader."""

from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.logging import get_logger
from app.graph.state import RAGState

logger = get_logger(__name__)

SYSTEM = """You are a relevance grader. You will be given a question and a list of document chunks.
For each chunk, decide if it contains information that can help answer the question.
Output a list of booleans corresponding to the chunks."""


class RelevanceResults(BaseModel):
    relevance_mask: List[bool] = Field(
        description="A list of true/false values for each chunk provided"
    )
    reasons: List[str] = Field(
        description="Brief reasons for rejection for each irrelevant chunk"
    )


async def relevance_grader_node(state: RAGState) -> dict:
    settings = get_settings()
    docs = state.get("retrieved_docs", [])

    if not docs:
        return {"relevant_docs": [], "retry_count": state.get("retry_count", 0) + 1}

    llm = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.google_api_key,
        temperature=0,
    ).with_structured_output(RelevanceResults)

    # Format all chunks into a single numbered list to save tokens and calls
    chunks_text = "\n\n".join(
        [f"CHUNK {i}:\n{d.page_content}" for i, d in enumerate(docs)]
    )

    try:
        result = await llm.ainvoke(
            [
                SystemMessage(content=SYSTEM),
                HumanMessage(
                    content=f"Question: {state['rewritten_question']}\n\n{chunks_text}"
                ),
            ]
        )

        relevant = []
        rejected_reasons = []

        # Match the mask back to the original documents
        for i, is_relevant in enumerate(result.relevance_mask):
            if i < len(docs):
                if is_relevant:
                    relevant.append(docs[i])
                else:
                    if i < len(result.reasons):
                        rejected_reasons.append(result.reasons[i])

    except Exception as exc:
        logger.error("bulk_grader_failed", error=str(exc))
        # Fallback: keep all docs if grader fails to avoid blocking the user
        relevant = docs
        rejected_reasons = ["Grader error fallback"]

    current_retries = state.get("retry_count", 0)
    new_retries = current_retries + (0 if relevant else 1)

    logger.info(
        "relevance_graded_optimized",
        total=len(docs),
        relevant=len(relevant),
        retry_count=new_retries,
    )

    return {
        "relevant_docs": relevant,
        "retry_count": new_retries,
        "retrieval_feedback": "" if relevant else " ".join(rejected_reasons[:2]),
    }
