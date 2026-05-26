"""app/graph/nodes/query_rewriter.py — Rewrites query for better retrieval."""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.graph.state import RAGState
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

SYSTEM = """You are an expert at reformulating questions for semantic search.
Rewrite the user's question to be self-contained, specific, and optimised for
searching a knowledge base. If previous retrieval or validation feedback is
provided, change the search formulation to address that failure rather than
repeating the same query. Return ONLY the rewritten question."""


async def query_rewriter_node(state: RAGState) -> dict:
    settings = get_settings()
    llm = ChatGoogleGenerativeAI(model=settings.llm_model, google_api_key=settings.google_api_key, temperature=0)

    history = state.get("messages", [])[-6:]
    history_text = "\n".join(f"{m.type.upper()}: {m.content}" for m in history)
    feedback = "\n".join(
        f for f in [
            state.get("retrieval_feedback", ""),
            state.get("validation_feedback", ""),
        ]
        if f
    ) or "None"

    response = await llm.ainvoke([
        SystemMessage(content=SYSTEM),
        HumanMessage(content=(
            f"History:\n{history_text}\n\nQuestion: {state['original_question']}"
            f"\n\nPrevious failure feedback:\n{feedback}\n\nRewritten:"
        )),
    ])
    rewritten = response.content.strip()
    logger.info("query_rewritten", original=state["original_question"], rewritten=rewritten)
    return {"rewritten_question": rewritten}
