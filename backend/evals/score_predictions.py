"""Score saved RAG outputs against a question/evidence benchmark."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def _load(path: str) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def score(cases: list[dict], predictions: list[dict]) -> dict[str, float]:
    by_id = {prediction["id"]: prediction for prediction in predictions}
    retrieval_hits = 0
    citation_hits = 0
    abstention_hits = 0

    for case in cases:
        prediction = by_id.get(case["id"], {})
        expected_sources = set(case.get("expected_sources", []))
        retrieved_sources = set(prediction.get("retrieved_sources", []))
        answer = prediction.get("answer", "")

        retrieval_hits += int(not expected_sources or expected_sources.issubset(retrieved_sources))
        citation_hits += int(bool(re.search(r"\[E\d+(?:\s*,\s*E\d+)*\]", answer)) or case["should_abstain"])
        abstention_hits += int(bool(prediction.get("abstained", False)) == bool(case["should_abstain"]))

    total = max(len(cases), 1)
    return {
        "retrieval_source_recall": round(retrieval_hits / total, 3),
        "citation_or_abstention_rate": round(citation_hits / total, 3),
        "abstention_accuracy": round(abstention_hits / total, 3),
    }


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: python evals/score_predictions.py CASES.json PREDICTIONS.json")
        return 2
    metrics = score(_load(sys.argv[1]), _load(sys.argv[2]))
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
