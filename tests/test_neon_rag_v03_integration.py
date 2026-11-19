"""Optional real PostgreSQL integration test. Never runs without two opt-ins.

Prerequisites: Neon TEST branch, migration already applied, separate credentials.
    RAG_TEST_DATABASE_URL=postgresql://...separate-staging...
    RAG_TEST_ALLOW_WRITES=yes
    python -m unittest tests.test_neon_rag_v03_integration -v

No Gemini / cloud embedding request is made by these tests.
"""
import os
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from rag_postgres import PostgresRAGIndex


@unittest.skipUnless(os.getenv("RAG_TEST_DATABASE_URL") and
                     os.getenv("RAG_TEST_ALLOW_WRITES") == "yes",
                     "No explicitly authorized isolated Neon staging test DB")
class RealNeonStagingTest(unittest.TestCase):
    def test_staging_ingest_approval_scope_consent_and_delete(self):
        owner = "rag_v03_qa_" + uuid.uuid4().hex[:12]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test_only.md"
            path.write_text("Unique qubit superposition evidence " + uuid.uuid4().hex + ". " * 12,
                            encoding="utf-8")
            env = {"RAG_ENVIRONMENT": "staging",
                   "RAG_DATABASE_URL": os.environ["RAG_TEST_DATABASE_URL"],
                   "RAG_CLOUD_EMBEDDINGS_ENABLED": "false",
                   "RAG_USE_LOCAL_EMBEDDINGS": "false"}
            with patch.dict(os.environ, env):
                idx = PostgresRAGIndex()
                record = idx.add_document(owner=owner, project_id=987654321, path=path)
                sid = record["source_id"]
                try:
                    self.assertFalse(idx.search(owner=owner, project_id=987654321, query="qubit").hits)
                    self.assertTrue(idx.approve(owner=owner, project_id=987654321, source_id=sid))
                    self.assertTrue(idx.search(owner=owner, project_id=987654321, query="qubit").hits)
                    self.assertFalse(idx.search(owner="another-teacher", project_id=987654321, query="qubit").hits)
                    self.assertFalse(idx.search(owner=owner, project_id=1, query="qubit").hits)
                    self.assertFalse(idx.search(owner=owner, project_id=987654321, query="qubit",
                                                for_generation=True).hits)
                    self.assertTrue(idx.set_generation_consent(owner=owner, project_id=987654321,
                                                                source_id=sid, allowed=True))
                    self.assertTrue(idx.search(owner=owner, project_id=987654321, query="qubit",
                                               for_generation=True).hits)
                    self.assertTrue(idx.approve(owner=owner, project_id=987654321, source_id=sid, approved=False))
                    self.assertFalse(idx.search(owner=owner, project_id=987654321, query="qubit").hits)
                finally:
                    idx.delete(owner=owner, project_id=987654321, source_id=sid)


if __name__ == "__main__":
    unittest.main()
