"""Deterministic evidence selection and citation formatting helpers."""
import re

from langchain_core.documents import Document


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]{3,}", text.lower()))


def _text_similarity(left: Document, right: Document) -> float:
    a = _tokens(left.page_content)
    b = _tokens(right.page_content)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def select_evidence(
    results: list[tuple[Document, float]],
    *,
    top_k: int,
    score_threshold: float,
    diversity_threshold: float,
) -> list[Document]:
    """Filter weak/duplicate candidates and attach stable evidence labels."""
    selected: list[Document] = []
    for doc, score in sorted(results, key=lambda item: item[1], reverse=True):
        if score < score_threshold:
            continue
        if any(_text_similarity(doc, other) >= diversity_threshold for other in selected):
            continue
        doc.metadata["retrieval_score"] = round(score, 4)
        selected.append(doc)
        if len(selected) >= top_k:
            break

    for index, doc in enumerate(selected, start=1):
        doc.metadata["evidence_id"] = f"E{index}"
    return selected


def source_label(doc: Document) -> str:
    evidence_id = doc.metadata.get("evidence_id", "E?")
    source = doc.metadata.get("source", "?")
    page = doc.metadata.get("page_number")
    location = f"p. {page}" if page else f"chunk {doc.metadata.get('chunk_index', '?')}"
    return f"{evidence_id} | {source} | {location}"


def format_context(docs: list[Document]) -> str:
    return "\n\n---\n\n".join(
        f"[{source_label(doc)}]\n{doc.page_content}"
        for doc in docs
    )


def cited_evidence_ids(answer: str) -> set[str]:
    citations = re.findall(r"\[(E\d+(?:\s*,\s*E\d+)*)\]", answer)
    return {
        evidence_id.strip()
        for group in citations
        for evidence_id in group.split(",")
    }


def has_valid_citations(answer: str, docs: list[Document]) -> bool:
    cited = cited_evidence_ids(answer)
    available = {str(doc.metadata.get("evidence_id")) for doc in docs}
    return bool(cited) and cited.issubset(available)
