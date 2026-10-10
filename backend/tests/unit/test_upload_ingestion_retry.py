"""Tests for truthful partial status and retryable vector indexing."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from services.upload_ingestion_service import UploadIngestionService


class UploadIngestionRetryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.session = Mock()
        self.job = SimpleNamespace(
            id="job-1", content_hash="hash", status="PROCESSING",
            error_message=None, completed_at=None, chunk_count=0, document_count=0,
        )
        self.document = SimpleNamespace(ingestion_job_id="job-1")
        self.session.scalar.return_value = self.document
        self.service = UploadIngestionService(self.session)

    def test_retry_failure_is_persisted_as_partial(self) -> None:
        self.service._ensure_qdrant_index = Mock(side_effect=ConnectionError("offline"))

        with self.assertRaisesRegex(RuntimeError, "Qdrant indexing failed"):
            self.service.retry_indexing(self.job)

        self.assertEqual("PARTIAL", self.job.status)
        self.assertIn("ConnectionError: offline", self.job.error_message)
        self.session.commit.assert_called_once()

    def test_successful_retry_completes_original_job(self) -> None:
        self.service._ensure_qdrant_index = Mock(return_value=7)

        updated = self.service.retry_indexing(self.job)

        self.assertIs(updated, self.job)
        self.assertEqual("COMPLETED", self.job.status)
        self.assertIsNone(self.job.error_message)
        self.assertEqual(7, self.job.chunk_count)
        self.assertEqual(1, self.job.document_count)
        self.session.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
