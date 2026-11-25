"""Offline/mocked verification of the Online-First 3alimnIA Hybrid RAG V0.2."""
from __future__ import annotations
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests import test_hybrid_rag_v01  # sets streamlit stub for the older modules
import hybrid_rag
import online_embeddings
import rag_grounding
import lesson_block_generation_engine


class OnlineRAGTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.db = self.home / 'index.sqlite3'
        self.index = hybrid_rag.RAGIndex(self.db)
        self.first = self.home/'reference.txt'
        self.first.write_text(('Qubit states are unit vectors in a Hilbert space. ' * 24).strip(), encoding='utf-8')
        self.second = self.home/'paper.md'
        self.second.write_text(('Quantique: mesure, état et superposition. ' * 26).strip(), encoding='utf-8')
        self.env = patch.dict(os.environ, {'RAG_CLOUD_EMBEDDINGS_ENABLED':'true',
                                           'RAG_USE_LOCAL_EMBEDDINGS':'false'})
        self.env.start()
        self.addCleanup(self.env.stop)

    @staticmethod
    def fake_embed(texts, *, purpose):
        return [[1.0, 0.0, 0.0] if 'qubit' in text.lower() else [0.0, 1.0, 0.0] for text in texts]

    def test_default_lexical_does_not_transmit_teacher_document(self):
        with patch.object(online_embeddings,'embed_texts',side_effect=AssertionError('cloud called')):
            created = self.index.add_document(owner='a',project_id=1,path=self.first, approved=True)
            found = self.index.search(owner='a',project_id=1,query='Hilbert qubit')
        self.assertFalse(created['cloud_processing_consent'])
        self.assertEqual('lexical',created['embedding_provider'])
        self.assertEqual('lexical',found.retrieval_mode)
        self.assertTrue(found.hits)
        self.assertRegex(found.citation_ids[0],r'^RAG[A-F0-9]{12}_P0_C[0-9]+$')
        self.assertIn('source=',found.packet)

    def test_consent_index_and_search_are_semantic_with_provider_mock(self):
        with patch.object(online_embeddings,'embed_texts',side_effect=self.fake_embed) as fake:
            created=self.index.add_document(owner='a',project_id=1,path=self.first,approved=False,
                                            allow_cloud_processing=True)
            self.assertEqual('gemini',created['embedding_provider'])
            self.assertFalse(self.index.search(owner='a',project_id=1,query='Hilbert').hits)
            self.index.approve(owner='a',project_id=1,source_id=created['source_id'])
            found=self.index.search(owner='a',project_id=1,query='qubit state')
        self.assertTrue(found.hits)
        self.assertEqual(found.retrieval_mode,'hybrid')
        self.assertTrue(any(x.kwargs.get('purpose')=='document' for x in fake.call_args_list))
        self.assertTrue(any(x.kwargs.get('purpose')=='query' for x in fake.call_args_list))
        self.assertEqual(found.hits[0]['approved_by'],'a')

    def test_no_query_leak_for_unapproved_or_wrong_tenant(self):
        with patch.object(online_embeddings,'embed_texts',side_effect=self.fake_embed):
            self.index.add_document(owner='a',project_id=1,path=self.first,allow_cloud_processing=True)
        with patch.object(online_embeddings,'embed_texts',side_effect=AssertionError('query sent')):
            self.assertFalse(self.index.search(owner='a',project_id=1,query='private concept').hits)
            self.assertFalse(self.index.search(owner='b',project_id=1,query='private concept').hits)
            self.assertFalse(self.index.search(owner='a',project_id=2,query='private concept').hits)

    def test_backfill_requires_explicit_new_consent_and_scoped_owner(self):
        made=self.index.add_document(owner='a',project_id=1,path=self.first,approved=True)
        with self.assertRaises(PermissionError):
            self.index.enable_cloud_embeddings(owner='a',project_id=1,source_id=made['source_id'])
        with self.assertRaises(ValueError):
            self.index.enable_cloud_embeddings(owner='b',project_id=1,source_id=made['source_id'],teacher_confirmed=True)
        with patch.object(online_embeddings,'embed_texts',side_effect=self.fake_embed):
            result=self.index.enable_cloud_embeddings(owner='a',project_id=1,source_id=made['source_id'],teacher_confirmed=True)
            found=self.index.search(owner='a',project_id=1,query='Hilbert qubit')
        self.assertEqual(result['embedding_provider'],'gemini')
        self.assertTrue(found.hits)
        self.assertEqual(found.retrieval_mode,'hybrid')

    def test_migration_preserves_previous_database(self):
        # Old V0.1 schema without new provenance columns.
        with sqlite3.connect(str(self.db)) as con:
            con.executescript('''CREATE TABLE rag_documents (
                id INTEGER PRIMARY KEY, owner TEXT NOT NULL, project_id INTEGER NOT NULL,
                source_id TEXT NOT NULL UNIQUE, name TEXT NOT NULL, origin TEXT NOT NULL,
                approved INTEGER NOT NULL DEFAULT 0, license_note TEXT NOT NULL DEFAULT '',
                content_sha256 TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(owner,project_id,content_sha256));
                CREATE TABLE rag_chunks (id INTEGER PRIMARY KEY, document_id INTEGER, page INTEGER,
                ordinal INTEGER, body TEXT, vector_json TEXT NOT NULL DEFAULT '', UNIQUE(document_id,ordinal));
                CREATE VIRTUAL TABLE rag_fts USING fts5(body, tokenize='unicode61 remove_diacritics 2');''')
        with patch.object(online_embeddings,'embed_texts',side_effect=AssertionError('should not call')):
            self.index.add_document(owner='a',project_id=1,path=self.first,approved=True)
        with self.index._connect() as con:
            cols={row['name'] for row in con.execute('PRAGMA table_info(rag_documents)')}
        self.assertTrue({'cloud_processing_consent','approved_by','approved_at','embedding_provider'}<=cols)

    def test_revoke_removes_cloud_hit_immediately(self):
        with patch.object(online_embeddings,'embed_texts',side_effect=self.fake_embed):
            result=self.index.add_document(owner='a',project_id=1,path=self.first,approved=True,allow_cloud_processing=True)
            self.assertTrue(self.index.search(owner='a',project_id=1,query='qubit').hits)
            self.index.approve(owner='a',project_id=1,source_id=result['source_id'],approved=False)
            self.assertFalse(self.index.search(owner='a',project_id=1,query='qubit').hits)

    def test_semantic_error_falls_back_and_is_disclosed(self):
        with patch.object(online_embeddings,'embed_texts',side_effect=self.fake_embed):
            self.index.add_document(owner='a',project_id=1,path=self.first,approved=True,allow_cloud_processing=True)
        with patch.object(online_embeddings,'embed_texts',side_effect=RuntimeError('provider quota')):
            found=self.index.search(owner='a',project_id=1,query='qubit')
        self.assertEqual(found.retrieval_mode,'lexical')
        self.assertIn('unavailable',found.retrieval_diagnostic)
        self.assertTrue(found.hits)

    def test_cloud_revocation_clears_vectors_and_prevents_new_online_queries(self):
        with patch.object(online_embeddings,'embed_texts',side_effect=self.fake_embed):
            a=self.index.add_document(owner='a',project_id=1,path=self.first,approved=True,
                                      allow_cloud_processing=True)
        self.assertFalse(self.index.disable_cloud_embeddings(owner='b',project_id=1,source_id=a['source_id']))
        self.assertTrue(self.index.disable_cloud_embeddings(owner='a',project_id=1,source_id=a['source_id']))
        with patch.object(online_embeddings,'embed_texts',side_effect=AssertionError('query transmitted')):
            found=self.index.search(owner='a',project_id=1,query='qubit')
        self.assertEqual(found.retrieval_mode,'lexical')
        with self.index._connect() as con:
            count=con.execute("SELECT count(*) FROM rag_chunks WHERE vector_json<>''").fetchone()[0]
        self.assertEqual(count,0)

    def test_duplicate_upload_does_not_change_approval_or_consent(self):
        a=self.index.add_document(owner='a',project_id=1,path=self.first,approved=False)
        with patch.object(online_embeddings,'embed_texts',side_effect=AssertionError('should not send')):
            b=self.index.add_document(owner='a',project_id=1,path=self.first,approved=True,allow_cloud_processing=True)
        self.assertTrue(b['reused'])
        self.assertEqual(b['source_id'],a['source_id'])
        self.assertFalse(b['approved'])

    def test_online_generation_requires_separate_consent_and_approval(self):
        # Embedding consent is NOT permission to give excerpts to the LLM.
        a=self.index.add_document(owner='a',project_id=1,path=self.first,approved=True,
                                  allow_cloud_processing=False,allow_online_generation=False)
        self.assertTrue(self.index.search(owner='a',project_id=1,query='qubit').hits)
        blocked=self.index.search(owner='a',project_id=1,query='qubit',for_generation=True)
        self.assertFalse(blocked.hits)
        self.assertIn('consent',blocked.retrieval_diagnostic)
        self.assertFalse(self.index.set_generation_consent(owner='b',project_id=1,source_id=a['source_id'],allowed=True))
        self.assertTrue(self.index.set_generation_consent(owner='a',project_id=1,source_id=a['source_id'],allowed=True))
        self.assertTrue(self.index.search(owner='a',project_id=1,query='qubit',for_generation=True).hits)
        self.index.set_generation_consent(owner='a',project_id=1,source_id=a['source_id'],allowed=False)
        self.assertFalse(self.index.search(owner='a',project_id=1,query='qubit',for_generation=True).hits)

    def test_source_priority_teacher_over_external(self):
        teacher=self.index.add_document(owner='a',project_id=1,path=self.first,approved=True)
        ext=self.index.add_document(owner='a',project_id=1,path=self.second,approved=True,origin='external')
        found=self.index.search(owner='a',project_id=1,query='quantique qubit mesure state',limit=8)
        self.assertEqual(found.source_ids[0],teacher['source_id'])
        self.assertIn(ext['source_id'],found.source_ids)

    def test_traceability_audit_is_not_claim_verification(self):
        a=self.index.add_document(owner='a',project_id=1,path=self.first,approved=True)
        ctx=self.index.search(owner='a',project_id=1,query='qubit Hilbert')
        citation=ctx.citation_ids[0]
        info=rag_grounding.audit_generated_text(f'The qubit can occupy a normalized state [{citation}].',ctx)
        self.assertEqual(info['known_chunk_citations'],[citation])
        self.assertTrue(info['human_verification_required'])
        self.assertIn('semantic_support_unverified',info['review_reasons'])
        unknown=rag_grounding.audit_generated_text('Unsupported [RAGFFFFFFFFFFFF_P1_C8]',ctx)
        self.assertEqual(unknown['unknown_citations'],['RAGFFFFFFFFFFFF_P1_C8'])
        valid=lesson_block_generation_engine.validate_block_content('summary',f'# Summary\nMeaning [{citation}]',ctx.citation_ids)
        self.assertNotIn('invalid_source_ids',','.join(valid['errors']))

    def test_public_reference_metadata_and_https_only(self):
        with self.assertRaises(ValueError):
            self.index.add_document(owner='a',project_id=1,path=self.first,source_url='http://example.org')
        saved=self.index.add_document(owner='a',project_id=1,path=self.first,
                                      approved=True,source_url='https://doi.org/10.1000/example',
                                      citation_label='Sample scientific reference',
                                      license_note='Teacher declared rights to use')
        meta=self.index.list_documents(owner='a',project_id=1)[0]
        self.assertEqual(meta['source_url'],'https://doi.org/10.1000/example')
        found=self.index.search(owner='a',project_id=1,query='qubit')
        self.assertIn('10.1000/example',found.packet)
        self.assertIn('Sample scientific reference',found.packet)

    def test_project_context_requires_generation_permission(self):
        doc=self.index.add_document(owner='a',project_id=1,path=self.first,approved=True)
        with patch.dict(os.environ,{'RAG_ENABLED':'true','RAG_DB_PATH':str(self.db)}):
            excluded=hybrid_rag.project_context(project_id=1,owner='a',query='qubit')
            self.assertFalse(excluded.hits)
            self.assertIn('consent',excluded.retrieval_diagnostic)
            self.index.set_generation_consent(owner='a',project_id=1,source_id=doc['source_id'],allowed=True)
            included=hybrid_rag.project_context(project_id=1,owner='a',query='qubit')
            self.assertTrue(included.hits)
            self.assertTrue(included.citation_ids)

    def test_cloud_client_validates_response_and_does_not_expose_key(self):
        class Res:
            def raise_for_status(self): pass
            def json(self):return {'embedding':{'values':[1.0]+[0.0]*767}}
        with patch.dict(os.environ,{'GEMINI_API_KEY':'TOP-SECRET-TEST'}), patch('online_embeddings.requests.post',return_value=Res()) as req:
            vec=online_embeddings.embed_texts(['Superposition'],purpose='query')
            self.assertEqual(len(vec[0]),768)
            self.assertEqual(req.call_args.args[0],'https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent')
            self.assertEqual(req.call_args.kwargs['json']['taskType'],'RETRIEVAL_QUERY')
            self.assertNotIn('TOP-SECRET-TEST',str(vec))

    def test_cloud_client_fails_closed_without_key(self):
        with patch.dict(os.environ,{'GEMINI_API_KEY':''}),patch('online_embeddings._api_key',return_value=''):
            with self.assertRaises(RuntimeError):
                online_embeddings.embed_texts(['private paragraph'],purpose='document')


if __name__=='__main__':
    unittest.main()
