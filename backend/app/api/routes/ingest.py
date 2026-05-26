"""app/api/routes/ingest.py — Upload and embed documents scoped to a conversation."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.logging import get_logger
from app.models.orm import Conversation, Document, User
from app.models.schemas import IngestResponse
from app.services.vector_store import get_collection
from app.utils.document_chunker import SUPPORTED_EXTENSIONS, chunk_document

router = APIRouter(tags=["Ingest"])
logger = get_logger(__name__)

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024


@router.post("/conversations/{conv_id}/ingest", response_model=IngestResponse)
async def ingest_document(
    conv_id: str,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a document into a specific conversation's knowledge base.
    Each conversation has its own isolated Chroma collection so
    documents from one chat never bleed into another.
    """
    # Verify conversation belongs to user
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_id, Conversation.user_id == user.id
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Validate file type
    filename = file.filename or "unknown"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type. Allowed: {', '.join(SUPPORTED_EXTENSIONS)}",
        )

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="File is empty")
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 20MB limit")

    doc = Document(
        conversation_id=conv_id,
        filename=filename,
    )
    db.add(doc)
    await db.flush()

    # Chunk and embed into this conversation's collection
    try:
        chunks = chunk_document(file_bytes, filename)
        if not chunks:
            raise HTTPException(
                status_code=422, detail="Document produced no text chunks"
            )

        for chunk in chunks:
            chunk.metadata["document_id"] = doc.id
        collection = get_collection(conv.chroma_collection_name)
        # Use synchronous add_documents to avoid async engine mismatch issues
        collection.add_documents(chunks)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("ingest_failed", filename=filename, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to process document")

    doc.chunks_created = len(chunks)

    # Auto-title the conversation from first upload if still default
    if conv.title == "New conversation":
        conv.title = filename.rsplit(".", 1)[0][:80]

    logger.info(
        "ingest_complete", conv_id=conv_id, filename=filename, chunks=len(chunks)
    )
    return IngestResponse(
        status="success",
        filename=filename,
        chunks_created=len(chunks),
        message=f"Ingested '{filename}' into {len(chunks)} chunks.",
    )


@router.delete("/conversations/{conv_id}/documents/{doc_id}", status_code=204)
async def delete_document(
    conv_id: str,
    doc_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a document record from Postgres and remove its chunks
    from the conversation's Chroma collection.
    """
    from sqlalchemy import delete as sql_delete

    # Verify conversation belongs to user
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conv_id, Conversation.user_id == user.id
        )
    )
    conv = conv_result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get the document
    doc_result = await db.execute(
        select(Document).where(
            Document.id == doc_id, Document.conversation_id == conv_id
        )
    )
    doc = doc_result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    filename = doc.filename

    # Remove chunks from Chroma that came from this file
    try:
        collection = get_collection(conv.chroma_collection_name)
        chunk_ids = collection.get(where={"document_id": doc_id}).get("ids", [])
        if chunk_ids:
            collection.delete(ids=chunk_ids)
        else:
            # Backwards compatibility for chunks ingested before document IDs
            # were recorded in vector metadata.
            collection.delete(where={"source": filename})
        logger.info("chroma_chunks_deleted", filename=filename, conv_id=conv_id)
    except Exception as e:
        logger.warning("chroma_delete_failed", filename=filename, error=str(e))

    # Delete from Postgres
    await db.execute(sql_delete(Document).where(Document.id == doc_id))
    await db.commit()
    logger.info("document_deleted", doc_id=doc_id, filename=filename)
