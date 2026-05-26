"""
app/api/routes/chat.py
────────────────────────
POST /conversations/{conv_id}/chat — SSE streaming chat.

Key fixes:
- Buffer generator output until grounding and quality checks approve it
- Use a fresh DB session inside the generator to avoid closed-session errors
- Pre-load messages before entering the async generator
"""
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from langchain_core.messages import HumanMessage, AIMessage

from app.core.database import get_db, AsyncSessionLocal
from app.core.deps import get_current_user
from app.models.orm import User, Conversation, Message
from app.models.schemas import ChatRequest, ChatStreamEvent
from app.graph.builder import build_graph
from app.core.logging import get_logger

router = APIRouter(tags=["Chat"])
logger = get_logger(__name__)

GRAPH_NODES = {
    "query_rewriter", "retriever", "relevance_grader",
    "generator", "hallucination_checker", "answer_quality",
}


async def _stream(
    conv_id:          str,
    user_message:     str,
    collection_name:  str,
    history:          list,
    document_names:   list[str] | None = None,
) -> AsyncGenerator[str, None]:
    def sse(event: ChatStreamEvent) -> str:
        return f"data: {event.model_dump_json()}\n\n"

    graph = build_graph()
    from app.graph.builder import get_graph_config
    config = get_graph_config()

    lc_messages = []
    for role, content in history:
        if role == "user":
            lc_messages.append(HumanMessage(content=content))
        else:
            lc_messages.append(AIMessage(content=content))

    initial_state = {
        "session_id":           conv_id,
        "document_names":       document_names or [],
        "messages":             lc_messages + [HumanMessage(content=user_message)],
        "original_question":    user_message,
        "rewritten_question":   "",
        "had_retrieval_candidates": False,
        "retrieved_docs":       [],
        "relevant_docs":        [],
        "generation":           "",
        "retry_count":          0,
        "retrieval_feedback":   "",
        "validation_feedback":  "",
        "hallucination_passed": False,
        "quality_passed":       False,
        "collection_name":      collection_name,
    }

    final_response = ""
    candidate_response = ""
    current_node = ""

    try:
        async for event in graph.astream_events(initial_state, config=config, version="v2"):
            kind = event.get("event", "")
            name = event.get("name", "")

            if kind == "on_chain_start" and name in GRAPH_NODES:
                current_node = name
                if name == "generator":
                    candidate_response = ""
                yield sse(ChatStreamEvent(type="metadata", data={"node": name, "status": "started"}))

            elif kind == "on_chain_end" and name in GRAPH_NODES:
                output = event.get("data", {}).get("output", {})
                generated = output.get("generation", "") if isinstance(output, dict) else ""
                if generated:
                    final_response = generated.strip()
                if name == "generator":
                    final_response = generated.strip() or candidate_response
                current_node = ""
                yield sse(ChatStreamEvent(type="metadata", data={"node": name, "status": "done"}))

            # Buffer candidate answer tokens until validation completes. A graph
            # retry must not expose or persist a rejected draft answer.
            elif kind == "on_chat_model_stream" and current_node == "generator":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    candidate_response += chunk.content

        final_response = final_response or "I was unable to generate a response."
        yield sse(ChatStreamEvent(type="token", data=final_response))

        # Save messages with a fresh session — request session closes after response headers sent
        async with AsyncSessionLocal() as db:
            try:
                db.add(Message(conversation_id=conv_id, role="user",      content=user_message))
                db.add(Message(conversation_id=conv_id, role="assistant", content=final_response))
                from datetime import datetime, timezone
                result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
                conv = result.scalar_one_or_none()
                if conv:
                    conv.updated_at = datetime.now(timezone.utc)
                await db.commit()
            except Exception as e:
                logger.error("message_save_failed", conv_id=conv_id, error=str(e))
                await db.rollback()

        yield sse(ChatStreamEvent(type="done", data=""))
        logger.info("chat_complete", conv_id=conv_id, response_len=len(final_response))

    except Exception as exc:
        logger.error("chat_error", conv_id=conv_id, error=str(exc))
        yield sse(ChatStreamEvent(type="error", data=str(exc)))


@router.post("/conversations/{conv_id}/chat")
async def chat(
    conv_id: str,
    body:    ChatRequest,
    user:    User = Depends(get_current_user),
    db:      AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conv_id, Conversation.user_id == user.id)
        .options(selectinload(Conversation.messages), selectinload(Conversation.documents))
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    history = [(m.role, m.content) for m in conv.messages[-20:]]
    document_names = [d.filename for d in conv.documents]

    return StreamingResponse(
        _stream(conv.id, body.message, conv.chroma_collection_name, history, document_names),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
