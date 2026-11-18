"""Offline contract tests for staging-only Neon RAG storage V0.3.
No API key, Neon connection or network access is necessary.
"""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import os
import unittest

import hybrid_rag
import rag_postgres
import rag_pg_migrate

TEST_URL = "postgresql://rag_test:fake@ep-test.us-east-2.aws.neon.tech/isolated_rag_test?sslmode=require"


class FakeCursor:
    def __init__(self, owner="prof", project=42):
        self.owner = owner
        self.project = project
        self.last_sql = ""
        self.statements = []
        self.rowcount = 1
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, typ, exc, tb):
        return False

    def execute(self, sql, args=()):
        self.last_sql = str(sql)
        self.statements.append(self.last_sql)
        self.calls.append((self.last_sql, args))

    def fetchone(self):
        if "ON CONFLICT" in self.last_sql:
            return {"id": 991}
        if "RETURNING id" in self.last_sql:
            return {"id": 991}
        if "SELECT 1 FROM rag_chunks" in self.last_sql:
            return None
        if "SELECT count(*) AS n" in self.last_sql:
            return {"n": 0}
        return None

    def fetchall(self):
        return []


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()
        self.closed = False
        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


class NeonRAGV03Test(unittest.TestCase):
    def test_staging_required_no_primary_reuse(self):
        with patch.dict(os.environ, {"RAG_ENVIRONMENT": "production", "RAG_DATABASE_URL": TEST_URL}):
            with self.assertRaises(RuntimeError):
                rag_postgres._required_staging_dsn()
        with patch.dict(os.environ, {"RAG_ENVIRONMENT": "staging", "DATABASE_URL": TEST_URL,
                                         "RAG_DATABASE_URL": TEST_URL}):
            with self.assertRaises(RuntimeError):
                rag_postgres._required_staging_dsn()
        with patch.dict(os.environ, {"RAG_ENVIRONMENT": "staging", "RAG_DATABASE_URL": TEST_URL}, clear=True):
            self.assertEqual(rag_postgres._required_staging_dsn(), TEST_URL)

    def test_vector_validation(self):
        with self.assertRaises(ValueError):
            rag_postgres._vector_literal([0.1, 0.2])
        with self.assertRaises(ValueError):
            rag_postgres._vector_literal([float("nan")] * 768)
        with self.assertRaises(ValueError):
            rag_postgres._vector_literal([0.0] * 768)
        literal = rag_postgres._vector_literal([1.0] + [0.0] * 767)
        self.assertTrue(literal.startswith("[1.0,0.0,"))

    def test_factory_sqlite_default_and_postgres_guard(self):
        with patch.dict(os.environ, {"RAG_STORAGE_BACKEND": "sqlite"}, clear=True):
            self.assertIsInstance(hybrid_rag.open_index(), hybrid_rag.RAGIndex)
        with patch.dict(os.environ, {"RAG_STORAGE_BACKEND": "postgres", "RAG_ENVIRONMENT": "staging",
                                         "RAG_DATABASE_URL": TEST_URL}, clear=True):
            self.assertIsInstance(hybrid_rag.open_index(), rag_postgres.PostgresRAGIndex)
        with patch.dict(os.environ, {"RAG_STORAGE_BACKEND": "wrong"}):
            with self.assertRaises(ValueError):
                hybrid_rag.open_index()

    def test_migration_is_explicit_and_has_indexes(self):
        statements = "\n".join(rag_pg_migrate.migration_statements()).lower()
        self.assertIn("create extension if not exists vector", statements)
        self.assertIn("vector_gemini vector(768)", statements)
        self.assertIn("rag_events", statements)
        self.assertIn("using hnsw", statements)
        self.assertIn("rag_documents_scope_idx", statements)
        self.assertIn("to_tsvector('simple', body)", statements)
        # No standalone production tables can be modified in migration.
        self.assertNotIn("teacher_projects", statements)
        self.assertNotIn("user_accounts", statements)

    def test_no_embedding_without_teacher_permission(self):
        connection = FakeConnection()
        def factory(_):
            return connection
        with TemporaryDirectory() as tmp:
            document = Path(tmp) / "course.txt"
            document.write_text("Qubit superposition measurement. " * 10)
            with patch.dict(os.environ, {"RAG_ENVIRONMENT": "staging", "RAG_DATABASE_URL": TEST_URL,
                                             "RAG_CLOUD_EMBEDDINGS_ENABLED": "true"}, clear=True):
                def no_embed(_):
                    raise AssertionError("No content should leave server without consent")
                index = rag_postgres.PostgresRAGIndex(embedder=no_embed, connect_factory=factory)
                result = index.add_document(owner="prof", project_id=42, path=document,
                                            allow_cloud_processing=False, allow_online_generation=False)
        self.assertEqual(result["embedding_provider"], "lexical")
        self.assertEqual(result["chunks"], 1)
        self.assertTrue(connection.closed)
        self.assertGreaterEqual(connection.commits, 1)
        self.assertTrue(any("INSERT INTO rag_events" in q for q in connection.cursor_instance.statements))
        self.assertTrue(any("ON CONFLICT" in q for q in connection.cursor_instance.statements))

    def test_cloud_embedding_requires_explicit_permission_before_database(self):
        with patch.dict(os.environ, {"RAG_ENVIRONMENT": "staging", "RAG_DATABASE_URL": TEST_URL}, clear=True):
            index = rag_postgres.PostgresRAGIndex(connect_factory=lambda _: (_ for _ in ()).throw(AssertionError("DB accessed")))
            with self.assertRaises(PermissionError):
                index.enable_cloud_embeddings(owner="prof", project_id=42, source_id="RAGFFFFFFFFFFFF")

    def test_generation_search_scopes_all_queries_and_consent(self):
        all_connections = []
        def factory(_):
            conn = FakeConnection()
            all_connections.append(conn)
            return conn
        with patch.dict(os.environ, {"RAG_ENVIRONMENT": "staging", "RAG_DATABASE_URL": TEST_URL,
                                         "RAG_CLOUD_EMBEDDINGS_ENABLED": "false"}, clear=True):
            index = rag_postgres.PostgresRAGIndex(connect_factory=factory)
            result = index.search(owner="prof", project_id=42, query="qubit", for_generation=True)
        self.assertFalse(result.hits)
        statements = [s for c in all_connections for s in c.cursor_instance.statements]
        self.assertTrue(any("d.cloud_generation_consent=TRUE" in s for s in statements))
        self.assertTrue(any("d.owner=%s AND d.project_id=%s" in s for s in statements))
        self.assertTrue(all(c.closed for c in all_connections))

    def test_approval_and_revocation_scoped_and_audited(self):
        connections = []
        def factory(_):
            c = FakeConnection()
            connections.append(c)
            return c
        with patch.dict(os.environ, {"RAG_ENVIRONMENT":"staging", "RAG_DATABASE_URL":TEST_URL}, clear=True):
            idx=rag_postgres.PostgresRAGIndex(connect_factory=factory)
            self.assertTrue(idx.approve(owner="prof",project_id=42,source_id="RAG123",approved=False))
            self.assertTrue(idx.set_generation_consent(owner="prof",project_id=42,source_id="RAG123",allowed=False))
        updates=[q for c in connections for q in c.cursor_instance.calls if "UPDATE rag_documents" in q[0]]
        self.assertEqual(len(updates),2)
        for sql,args in updates:
            self.assertIn("owner=%s AND project_id=%s AND source_id=%s",sql)
            self.assertEqual(tuple(args[-3:]),("prof",42,"RAG123"))
        self.assertTrue(all(c.closed for c in connections))


if __name__ == "__main__":
    unittest.main()
