"""app/graph/nodes/answer_quality.py"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from app.graph.state import RAGState
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

SYSTEM = """Decide whether the answer addresses the user's question using the
available evidence. An explicit insufficient-evidence response is useful when
the evidence genuinely cannot support an answer."""


class QualityDecision(BaseModel):
    useful: bool
    reason: str = Field(default="", description="Short explanation for the decision")


def _rejection_update(state: RAGState, reason: str) -> dict:
    retries = state.get("retry_count", 0) + 1
    if retries >= get_settings().max_retries:
        return {
            "generation": (
                "I could not find enough supported evidence to give a useful answer. "
                "Try rephrasing the question or uploading a more relevant source."
            ),
            "quality_passed": True,
            "retry_count": retries,
            "validation_feedback": reason,
        }
    return {
        "quality_passed": False,
        "retry_count": retries,
        "validation_feedback": reason,
    }


async def answer_quality_node(state: RAGState) -> dict:
    settings = get_settings()
    if not state.get("relevant_docs") and "sufficient evidence" in state["generation"]:
        return {"quality_passed": True, "validation_feedback": ""}

    llm = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.google_api_key,
        temperature=0,
    ).with_structured_output(QualityDecision)
    try:
        r = await llm.ainvoke([
            SystemMessage(content=SYSTEM),
            HumanMessage(content=f"Question: {state['original_question']}\n\nAnswer:\n{state['generation']}"),
        ])
        result = r if isinstance(r, QualityDecision) else QualityDecision.model_validate(r)
    except Exception as exc:
        result = QualityDecision(useful=False, reason=f"Quality validation failed: {exc}")

    logger.info("quality_check", useful=result.useful, retries=state.get("retry_count", 0))
    if not result.useful:
        return _rejection_update(state, result.reason)
    return {"quality_passed": True, "validation_feedback": ""}
