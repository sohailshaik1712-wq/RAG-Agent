"""app/api/routes/conversations.py — Create, list, rename, delete conversations."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.logging import get_logger
from app.models.orm import Conversation, User
from app.models.schemas import (
    ConversationCreate,
    ConversationOut,
    ConversationUpdate,
    ConversationWithMessages,
)
from app.services.vector_store import delete_collection

router = APIRouter(prefix="/conversations", tags=["Conversations"])
logger = get_logger(__name__)


@router.get("", response_model=list[ConversationOut])
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all conversations for the current user, newest first."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .options(selectinload(Conversation.documents))
    )
    return result.scalars().all()


@router.post("", response_model=ConversationOut, status_code=201)
async def create_conversation(
    body: ConversationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new conversation for the current user."""
    conv = Conversation(user_id=user.id, title=body.title)
    db.add(conv)
    await db.flush()
    await db.refresh(conv)
    logger.info("conversation_created", conv_id=conv.id, user_id=user.id)
    return conv


@router.get("/{conv_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conv_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a conversation with all its messages and documents."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conv_id, Conversation.user_id == user.id)
        .options(
            selectinload(Conversation.messages),
            selectinload(Conversation.documents),
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.patch("/{conv_id}", response_model=ConversationOut)
async def rename_conversation(
    conv_id: str,
    body: ConversationUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rename a conversation."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_id, Conversation.user_id == user.id
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv.title = body.title
    await db.flush()
    await db.refresh(conv)
    return conv


@router.delete("/{conv_id}", status_code=204)
async def delete_conversation(
    conv_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a conversation and all its messages, documents, and
    the associated vector collection.
    """
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_id, Conversation.user_id == user.id
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Delete the vector collection for this conversation
    delete_collection(conv.vector_collection_name)

    await db.execute(delete(Conversation).where(Conversation.id == conv_id))
    logger.info("conversation_deleted", conv_id=conv_id, user_id=user.id)
