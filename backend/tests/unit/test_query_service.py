"""Tests for entity-aware frontend query retrieval."""

import unittest

from services.query_service import extract_query_entity_ids, lexical_score


class QueryServiceTests(unittest.TestCase):
    def test_extracts_compound_and_simple_entity_ids(self) -> None:
        question = "Compare dr-bug-0026 with REQ-0345 and BUG-0026."

        self.assertEqual(
            ["DR-BUG-0026", "REQ-0345", "BUG-0026"],
            extract_query_entity_ids(question),
        )

    def test_entity_id_improves_lexical_score(self) -> None:
        score = lexical_score(
            "Give complete details of DR-BUG-0026",
            "Defect report DR-BUG-0026 is under investigation.",
        )

        self.assertGreater(score, 0)


if __name__ == "__main__":
    unittest.main()
