import unittest

from langchain_core.documents import Document

from app.services.evidence import (
    cited_evidence_ids,
    format_context,
    has_valid_citations,
    select_evidence,
)


class EvidenceSelectionTests(unittest.TestCase):
    def test_filters_low_scores_and_near_duplicates(self):
        duplicate_a = Document(
            page_content="Refund requests are accepted within 30 days with proof of purchase.",
            metadata={"source": "policy.pdf", "page_number": 2},
        )
        duplicate_b = Document(
            page_content="Refund requests are accepted within 30 days with proof of purchase.",
            metadata={"source": "policy-copy.pdf", "page_number": 2},
        )
        weak = Document(page_content="Company history.", metadata={"source": "about.txt"})

        selected = select_evidence(
            [(weak, 0.2), (duplicate_b, 0.91), (duplicate_a, 0.95)],
            top_k=3,
            score_threshold=0.35,
            diversity_threshold=0.85,
        )

        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].metadata["evidence_id"], "E1")
        self.assertEqual(selected[0].metadata["retrieval_score"], 0.95)

    def test_context_exposes_citeable_source_and_page(self):
        doc = Document(
            page_content="Refunds are available for 30 days.",
            metadata={"evidence_id": "E1", "source": "policy.pdf", "page_number": 2},
        )

        context = format_context([doc])

        self.assertIn("[E1 | policy.pdf | p. 2]", context)


class CitationValidationTests(unittest.TestCase):
    def setUp(self):
        self.docs = [
            Document(page_content="A", metadata={"evidence_id": "E1"}),
            Document(page_content="B", metadata={"evidence_id": "E2"}),
        ]

    def test_accepts_known_evidence_ids(self):
        self.assertTrue(has_valid_citations("Refunds take 30 days. [E1, E2]", self.docs))
        self.assertEqual(cited_evidence_ids("Supported. [E2]"), {"E2"})

    def test_rejects_missing_or_unknown_evidence_ids(self):
        self.assertFalse(has_valid_citations("Refunds take 30 days.", self.docs))
        self.assertFalse(has_valid_citations("Refunds take 30 days. [E3]", self.docs))


if __name__ == "__main__":
    unittest.main()
