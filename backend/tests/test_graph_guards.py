import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.graph.edges.conditions import route_after_grader
from app.graph.nodes.judge import judge_node
from langchain_core.documents import Document


class RetrievalRoutingTests(unittest.TestCase):
    @patch("app.graph.edges.conditions.get_settings")
    def test_retries_when_candidates_exist_but_evidence_is_rejected(self, settings):
        settings.return_value = SimpleNamespace(max_retries=3)
        state = {
            "relevant_docs": [],
            "retrieved_docs": [],
            "had_retrieval_candidates": True,
            "retry_count": 1,
        }

        self.assertEqual(route_after_grader(state), "query_rewriter")

    @patch("app.graph.edges.conditions.get_settings")
    def test_abstains_without_retry_for_empty_collection(self, settings):
        settings.return_value = SimpleNamespace(max_retries=3)
        state = {
            "relevant_docs": [],
            "retrieved_docs": [],
            "had_retrieval_candidates": False,
            "retry_count": 0,
        }

        self.assertEqual(route_after_grader(state), "generator")


class GroundingGuardTests(unittest.IsolatedAsyncioTestCase):
    @patch("app.graph.nodes.judge.get_settings")
    async def test_missing_citations_rejects_answer_before_budget_exhaustion(
        self, settings
    ):
        settings.return_value = SimpleNamespace(max_retries=3)
        state = {
            "generation": "The refund window is 30 days.",
            "relevant_docs": [
                Document(page_content="30 days", metadata={"evidence_id": "E1"})
            ],
            "retry_count": 0,
        }

        result = await judge_node(state)

        self.assertFalse(result["hallucination_passed"])
        self.assertEqual(result["retry_count"], 1)

    @patch("app.graph.nodes.judge.get_settings")
    async def test_missing_citations_abstains_when_budget_is_exhausted(self, settings):
        settings.return_value = SimpleNamespace(max_retries=3)
        # Budget of 3 means retry_count 2 -> 3 hits limit
        state = {
            "generation": "The refund window is 30 days.",
            "relevant_docs": [
                Document(page_content="30 days", metadata={"evidence_id": "E1"})
            ],
            "retry_count": 2,
        }

        result = await judge_node(state)

        self.assertTrue(result["hallucination_passed"])
        self.assertIn(
            "having trouble generating a high-quality answer", result["generation"]
        )


if __name__ == "__main__":
    unittest.main()
