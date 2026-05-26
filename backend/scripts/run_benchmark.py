import asyncio
import json
import os
import sys
from pathlib import Path

# Add the backend directory to sys.path to allow imports from 'app'
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.graph.builder import build_graph
from app.services.vector_store import delete_collection, get_collection
from app.utils.document_chunker import chunk_document


async def run_benchmark():
    settings = get_settings()
    collection_name = "eval-collection"

    # 1. Setup Collection
    import time

    collection_name = f"eval-collection-{int(time.time())}"
    collection = get_collection(collection_name)

    # 2. Index Document
    handbook_path = Path(__file__).parent.parent / "test_data" / "handbook.md"
    content = handbook_path.read_bytes()
    chunks = chunk_document(content, "handbook.md")
    # Use the synchronous add_documents if asynchronous is problematic,
    # but let's try to just wait a bit or ensure collection is ready.
    collection.add_documents(chunks)
    print(f"Indexed {len(chunks)} chunks from handbook.md")
    # 3. Load Cases
    cases_path = Path(__file__).parent.parent / "evals" / "actual_cases.json"
    with open(cases_path, "r") as f:
        cases = json.load(f)

    # 4. Build Graph
    graph = build_graph()

    predictions = []

    # 5. Run Questions
    for case in cases:
        print(f"Running case: {case['id']} - {case['question']}")

        initial_state = {
            "messages": [],
            "original_question": case["question"],
            "collection_name": collection_name,
            "document_names": ["handbook.md"],
            "max_retries": settings.max_retries,
            "retry_count": 0,
        }

        # We run the graph and take the final state
        result = await graph.ainvoke(initial_state)

        retrieved_docs = result.get("relevant_docs", []) or result.get(
            "retrieved_docs", []
        )
        retrieved_sources = list(
            set([doc.metadata.get("source") for doc in retrieved_docs])
        )

        # Check if it "abstained"
        answer = result.get("generation", "")
        abstained = (
            "could not find sufficient evidence" in answer.lower()
            or "no documents" in answer.lower()
        )

        predictions.append(
            {
                "id": case["id"],
                "retrieved_sources": retrieved_sources,
                "answer": answer,
                "abstained": abstained,
            }
        )

    # 6. Save Predictions
    pred_path = Path(__file__).parent.parent / "evals" / "actual_predictions.json"
    with open(pred_path, "w") as f:
        json.dump(predictions, f, indent=2)

    print(f"Saved {len(predictions)} predictions to {pred_path}")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
