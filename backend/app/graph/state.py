"""app/graph/state.py — LangGraph state TypedDict."""

from typing import Annotated

from langchain_core.documents import Document
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class RAGState(TypedDict):
    session_id: str
    collection_name: str
    document_names: list[str]
    messages: Annotated[list, add_messages]
    original_question: str
    rewritten_question: str
    had_retrieval_candidates: bool
    retrieved_docs: list[Document]
    relevant_docs: list[Document]
    generation: str
    retry_count: int
    retrieval_feedback: str
    validation_feedback: str
    hallucination_passed: bool
    quality_passed: bool
