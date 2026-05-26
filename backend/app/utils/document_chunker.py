"""app/utils/document_chunker.py — Load and split uploaded documents."""
import os, tempfile
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import get_settings

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


def chunk_document(file_bytes: bytes, filename: str) -> list[Document]:
    settings = get_settings()
    suffix = Path(filename).suffix.lower()
    ext = suffix

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        if ext == ".pdf":
            from langchain_community.document_loaders import PyPDFLoader
            docs = PyPDFLoader(tmp_path).load()
        elif ext in {".txt", ".md"}:
            from langchain_community.document_loaders import TextLoader
            docs = TextLoader(tmp_path, encoding="utf-8").load()
        else:
            raise ValueError(f"Unsupported: {ext}")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        chunks = splitter.split_documents(docs)
        for i, c in enumerate(chunks):
            page = c.metadata.get("page")
            c.metadata.update({
                "source": filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "page_number": page + 1 if isinstance(page, int) else None,
            })
        return chunks
    finally:
        os.unlink(tmp_path)
