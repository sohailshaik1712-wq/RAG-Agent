"""app/graph/nodes/hallucination_checker.py"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from app.graph.state import RAGState
from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.evidence import has_valid_citations

logger = get_logger(__name__)

SYSTEM = """You are a fact-checker. Is every claim in the answer grounded in the context?
An answer with evidence must contain valid [E#] citations and those citations
must support its factual claims."""


class GroundingDecision(BaseModel):
    grounded: bool
    reason: str = Field(default="", description="Short explanation for the decision")


def _rejection_update(state: RAGState, reason: str) -> dict:
    retries = state.get("retry_count", 0) + 1
    if retries >= get_settings().max_retries:
        return {
            "generation": (
                "I could not provide a sufficiently supported answer from the "
                "uploaded documents. Try rephrasing the question or adding more evidence."
            ),
            "hallucination_passed": True,
            "retry_count": retries,
            "validation_feedback": reason,
        }
    return {
        "hallucination_passed": False,
        "retry_count": retries,
        "validation_feedback": reason,
    }


async def hallucination_checker_node(state: RAGState) -> dict:
    settings = get_settings()
    docs = state.get("relevant_docs", [])
    if not docs:
        return {"hallucination_passed": True, "validation_feedback": ""}
    if not has_valid_citations(state["generation"], docs):
        return _rejection_update(
            state,
            "The answer omitted or used invalid evidence citations such as [E1].",
        )

    llm = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.google_api_key,
        temperature=0,
    ).with_structured_output(GroundingDecision)
    context = "\n\n".join(
        f"[{d.metadata.get('evidence_id', 'E?')}] {d.page_content}" for d in docs
    )
    try:
        r = await llm.ainvoke([
            SystemMessage(content=SYSTEM),
            HumanMessage(content=f"Context:\n{context}\n\nAnswer:\n{state['generation']}"),
        ])
        result = r if isinstance(r, GroundingDecision) else GroundingDecision.model_validate(r)
    except Exception as exc:
        result = GroundingDecision(grounded=False, reason=f"Grounding validation failed: {exc}")

    logger.info("hallucination_check", grounded=result.grounded, retries=state.get("retry_count", 0))
    if not result.grounded:
        return _rejection_update(state, result.reason)
    return {"hallucination_passed": True, "validation_feedback": ""}
