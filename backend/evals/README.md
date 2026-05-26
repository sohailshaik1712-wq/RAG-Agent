# RAG Evaluation Scaffold

Use `cases.example.json` as a schema for a small representative benchmark.
For each question, record which source documents must be retrieved and whether
the assistant should abstain because the uploaded evidence does not answer it.

Store evaluated application outputs in a JSON file with one record per case.
`predictions.example.json` provides a runnable example:

```json
[
  {
    "id": "refund-window",
    "retrieved_sources": ["policy.pdf"],
    "answer": "Returns are accepted within 30 days. [E1]",
    "abstained": false
  }
]
```

Score a result set from the `backend/` directory:

```bash
python evals/score_predictions.py evals/cases.example.json evals/predictions.example.json
```

For meaningful quality tracking, replace the example cases with 20-50 real
questions drawn from the intended document set and retain them as regressions.
