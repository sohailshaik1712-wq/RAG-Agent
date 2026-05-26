"""
app/services/vector_store.py
"""

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _get_embeddings() -> GoogleGenerativeAIEmbeddings:
    settings = get_settings()
    return GoogleGenerativeAIEmbeddings(
        model=f"models/{settings.embedding_model}",
        google_api_key=settings.google_api_key,
    )


def get_collection(collection_name: str) -> PGVector:
    settings = get_settings()
    # We use a sync connection string for the vector store
    # PGVector often prefers the 'psycopg' driver
    connection = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

    return PGVector(
        embeddings=_get_embeddings(),
        collection_name=collection_name,
        connection=connection,
        use_jsonb=True,
    )


def delete_collection(collection_name: str) -> None:
    store = get_collection(collection_name)
    try:
        # This deletes the collection and all its vectors
        store.delete_collection()
        logger.info("collection_deleted", name=collection_name)
    except Exception as e:
        logger.warning("collection_delete_failed", name=collection_name, error=str(e))
