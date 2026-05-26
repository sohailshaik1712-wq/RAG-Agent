"""app/graph/nodes/judge.py — Consolidated Hallucination & Quality Checker."""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.logging import get_logger
from app.graph.state import RAGState
from app.services.evidence import has_valid_citations

logger = get_logger(__name__)

SYSTEM = """You are a senior auditor for an AI assistant. Evaluate the generated answer based on:
1. GROUNDING: Is every claim supported by the provided context? Check citations [E1, E2, etc.].
2. UTILITY: Does it actually answer the user's question?

If the answer is a valid 'I don't know' because the context is missing info, mark it as grounded and useful."""


class AuditDecision(BaseModel):
    is_grounded: bool = Field(
        description="True if the answer doesn't hallucinate and uses context correctly"
    )
    is_useful: bool = Field(description="True if the answer addresses the question")
    feedback: str = Field(
        description="If not grounded or not useful, explain why specifically"
    )


async def judge_node(state: RAGState) -> dict:
    settings = get_settings()
    docs = state.get("relevant_docs", [])
    answer = state.get("generation", "")

    # 1. Skip check if the answer is a standard abstention (Speed optimization)
    if "could not find sufficient evidence" in answer.lower():
        return {
            "hallucination_passed": True,
            "quality_passed": True,
            "validation_feedback": "",
        }

    # 2. Fast-fail for missing citations (Cost optimization - no LLM call)
    if docs and not has_valid_citations(answer, docs):
        return _rejection_update(state, "Citations [E#] are missing or malformed.")

    # 3. Consolidated LLM Judge
    llm = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.google_api_key,
        temperature=0,
    ).with_structured_output(AuditDecision)

    context = "\n\n".join(
        [f"[{d.metadata.get('evidence_id', 'E?')}] {d.page_content}" for d in docs]
    )

    try:
        result = await llm.ainvoke(
            [
                SystemMessage(content=SYSTEM),
                HumanMessage(
                    content=f"Context:\n{context}\n\nQuestion: {state['original_question']}\n\nAnswer:\n{answer}"
                ),
            ]
        )
    except Exception as exc:
        logger.error("judge_node_failed", error=str(exc))
        return {"hallucination_passed": True, "quality_passed": True}

    logger.info("audit_complete", grounded=result.is_grounded, useful=result.is_useful)

    if not result.is_grounded or not result.is_useful:
        return _rejection_update(state, result.feedback)

    return {
        "hallucination_passed": True,
        "quality_passed": True,
        "validation_feedback": "",
    }


def _rejection_update(state: RAGState, reason: str) -> dict:
    retries = state.get("retry_count", 0) + 1
    passed = retries >= get_settings().max_retries

    # If we hit max retries, we force-end with a graceful failure message
    update = {
        "hallucination_passed": passed,
        "quality_passed": passed,
        "retry_count": retries,
        "validation_feedback": reason,
    }

    if passed:
        update["generation"] = (
            "I apologize, but I'm having trouble generating a high-quality answer based on the current documents. Try rephrasing your question."
        )

    return update
