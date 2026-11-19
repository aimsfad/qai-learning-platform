import os
import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

# Streamlit is not needed for standalone RAG, but is imported by the existing router.
if 'streamlit' not in sys.modules:
    try:
        import streamlit
    except ImportError:
        streamlit = types.ModuleType('streamlit')
        streamlit.secrets = {}
        streamlit.cache_resource = lambda *args, **kwargs: (lambda func: func)
        streamlit.cache_data = lambda *args, **kwargs: (lambda func: func)
        sys.modules['streamlit'] = streamlit

import hybrid_rag
import local_ai
import model_router
import content_generation_engine


class RAGTest(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.folder = Path(self.work.name)
        self.index = hybrid_rag.RAGIndex(self.folder/'rag.sqlite3')
        self.doc = self.folder/'course.md'
        self.doc.write_text('Le qubit est une superposition quantique. La mesure probabiliste de l etat est cruciale. '*15, encoding='utf-8')

    def tearDown(self):
        self.work.cleanup()

    def test_approval_owner_project_scope_and_revoke(self):
        created = self.index.add_document(owner='teacher_A',project_id=5,path=self.doc,approved=False)
        self.assertRegex(created['source_id'], r'^RAG[A-F0-9]{12}$')
        self.assertFalse(self.index.search(owner='teacher_A',project_id=5,query='qubit superposition').hits)
        self.assertTrue(self.index.approve(owner='teacher_A',project_id=5,source_id=created['source_id']))
        found = self.index.search(owner='teacher_A',project_id=5,query='qubit superposition')
        self.assertTrue(found.hits)
        self.assertIn(created['source_id'],found.packet)
        self.assertEqual('lexical',found.retrieval_mode)
        self.assertFalse(self.index.search(owner='teacher_B',project_id=5,query='qubit superposition').hits)
        self.assertFalse(self.index.search(owner='teacher_A',project_id=99,query='qubit superposition').hits)
        self.assertFalse(self.index.approve(owner='teacher_B',project_id=5,source_id=created['source_id']))
        self.assertTrue(self.index.approve(owner='teacher_A',project_id=5,source_id=created['source_id'],approved=False))
        self.assertFalse(self.index.search(owner='teacher_A',project_id=5,query='qubit superposition').hits)

    def test_teacher_approved_has_priority_over_approved_external(self):
        a = self.index.add_document(owner='p',project_id=7,path=self.doc,approved=True,origin='teacher')
        ext = self.folder/'external.txt'
        ext.write_text('Le qubit, superposition et mesure quantique. '*50,encoding='utf-8')
        b = self.index.add_document(owner='p',project_id=7,path=ext,approved=True,origin='external')
        output = self.index.search(owner='p',project_id=7,query='qubit superposition',limit=6)
        self.assertIn(a['source_id'],output.source_ids)
        self.assertIn(b['source_id'],output.source_ids)
        self.assertEqual(a['source_id'],output.hits[0]['source_id'])

    def test_remove_erases_fts_and_prevents_new_search(self):
        a=self.index.add_document(owner='p',project_id=7,path=self.doc,approved=True)
        self.assertTrue(self.index.delete(owner='p',project_id=7,source_id=a['source_id']))
        self.assertFalse(self.index.search(owner='p',project_id=7,query='qubit').hits)

    def test_hybrid_vector_ranking_mock(self):
        class Stub:
            def __call__(self,texts):
                return [[1.0,0.0] if ('qubit' in t.lower() or 'quantique' in t.lower()) else [0.0,1.0] for t in texts]
        self.index.embedder=Stub()
        with patch.dict(os.environ, {'RAG_USE_LOCAL_EMBEDDINGS':'true'}):
            self.index.add_document(owner='p',project_id=7,path=self.doc,approved=True)
            result=self.index.search(owner='p',project_id=7,query='qubit')
        self.assertEqual(result.retrieval_mode,'hybrid')
        self.assertTrue(result.hits)

    def test_unknown_citation_and_unsupported_input(self):
        self.assertEqual(['RAGFFFFFFFFFFFF'],hybrid_rag.unknown_rag_citations('Example [RAGFFFFFFFFFFFF]',[]))
        fake=self.folder/'binary.exe';fake.write_bytes(b'abc')
        with self.assertRaises(ValueError):
            self.index.add_document(owner='p',project_id=7,path=fake)

    def test_local_only_provider_never_falls_back_to_cloud(self):
        with patch.dict(os.environ, {'CONTENT_LLM_PROVIDER':'ollama','OLLAMA_ENABLED':'true',
                                     'GROQ_API_KEY':'not-real','LOCAL_AI_ALLOW_CLOUD_FALLBACK':'false'}):
            providers=model_router.generation_candidates('content')
        self.assertEqual(len(providers),1)
        self.assertEqual(providers[0].provider,'ollama')
        self.assertTrue(providers[0].available)

    def test_no_external_url_without_explicit_opt_in(self):
        with patch.dict(os.environ, {'OLLAMA_BASE_URL':'http://public.example:11434','OLLAMA_ALLOW_REMOTE':'false'}):
            with self.assertRaises(ValueError):
                local_ai.configured_url()

    def test_ollama_chat_shape_mock(self):
        class Fake:
            def raise_for_status(self):pass
            def json(self):return {'message':{'content':'تم توليد الدرس'}}
        with patch('local_ai.requests.post',return_value=Fake()) as mocked:
            self.assertEqual('تم توليد الدرس',local_ai.chat(model='qwen3:4b',prompt='شرح',system='درس'))
            self.assertTrue(mocked.call_args.kwargs['json']['stream'] is False)
            self.assertTrue(mocked.call_args.args[0].startswith('http://'))

    def test_lesson_compaction_keeps_rules_and_sources(self):
        from content_generation_engine import compact_lesson_prompt
        prompt = '# 3alimnIA lesson-block production request\n'+'Overview '*600 +\
            '\n# Verified teacher-approved RAG evidence\n[RAGAAAAAAAAAAAA] '+('Quantum superposition '*300)+\
            '\n# Requested block\n- Type: explanation\n# Mandatory rules\nNever invent sources.'
        compact = compact_lesson_prompt(prompt, 1000)
        self.assertIn('RAGAAAAAAAAAAAA', compact)
        self.assertIn('Mandatory rules', compact)
        self.assertLessEqual(content_generation_engine.estimate_tokens(compact),1000)

if __name__=='__main__':
    unittest.main()

class IntegrationContractTest(unittest.TestCase):
    def test_course_phase_prompt_accepts_rag_packet(self):
        import educational_builder as eb
        project={
            'project_name':'Quantum course','program_name':'Quantum computing',
            'unit_title':'Qubits','target_concept':'Superposition',
            'primary_language_code':'en','primary_language':'English',
        }
        output=eb.compile_project_prompt(project,1,prior_context='',research_packet='',evidence_packet='',
                                        rag_packet='[RAGAAAAAAAAAAAA] approved source excerpt')
        self.assertIn('Verified teacher-approved RAG evidence',output)
        self.assertIn('[RAGAAAAAAAAAAAA]',output)
        shortened=content_generation_engine.compact_prompt_for_budget(output,1800)
        self.assertIn('[RAGAAAAAAAAAAAA]',shortened)
        self.assertLessEqual(content_generation_engine.estimate_tokens(shortened),1800)

    def test_lesson_generation_prompt_source_allowlist(self):
        import lesson_block_generation_engine as lg
        project={'id':1,'project_name':'Quantum course','program_name':'Computing',
                 'primary_language':'English'}
        bundle={'id':7,'blueprint':{
            'lessons':[{'lesson_id':'L1','title':'Quantum Superposition','concept_ids':['C1'],
                        'source_ids':['S1'], 'prerequisites':[], 'misconceptions':[]}],
            'concepts':[{'concept_id':'C1','name':'Superposition','difficulty':'beginner','source_ids':['S1']}],
            'outcomes':[],
        }}
        prompt=lg.build_block_prompt(project,bundle,'L1','explanation',
                                    rag_packet='[RAGAAAAAAAAAAAA] Qubit superposition',
                                    rag_source_ids=['RAGAAAAAAAAAAAA'])
        self.assertIn('RAGAAAAAAAAAAAA',prompt)
        self.assertIn('S1',prompt)
        v=lg.validate_block_content('explanation','# شرح\nQubit measurement [RAGAAAAAAAAAAAA]',
                                    ['S1','RAGAAAAAAAAAAAA'])
        self.assertNotIn('invalid_source_ids',','.join(v['errors']))

    def test_end_to_end_routed_generation_mock(self):
        with patch.dict(os.environ, {'CONTENT_LLM_PROVIDER':'ollama','OLLAMA_ENABLED':'true',
                                     'LOCAL_AI_ALLOW_CLOUD_FALLBACK':'false'}):
            with patch('local_ai.chat',return_value='## درس تجريبي\nGenerated locally') as fake:
                response=content_generation_engine.generate_content('مقدمة في الحوسبة الكمومية', 'Arabic',max_tokens=500)
        self.assertEqual(response.provider,'ollama')
        self.assertEqual(response.status,'completed')
        self.assertFalse(response.used_fallback)
        self.assertEqual(fake.call_count,1)

class ApprovalHotfixTest(unittest.TestCase):
    def test_full_lesson_approval_resolves_approved_blueprint(self):
        import lesson_block_generation_engine as lg
        from contextlib import ExitStack
        blk = {'status':'completed','approved_by_teacher':0, 'content_text':'test'}
        with ExitStack() as e:
            e.enter_context(patch.object(lg,'_active_blueprint_run_id',return_value=9))
            e.enter_context(patch.object(lg.db,'latest_teacher_lesson_block',return_value=blk))
            e.enter_context(patch.object(lg,'lesson_quality_snapshot',return_value={'pedagogical_gate':{'can_approve':True}}))
            e.enter_context(patch.object(lg.db,'teacher_blueprint_bundle',return_value={
                'id':9,'project_id':1,'approved_by_teacher':1,'evidence_run_id':2,
                'blueprint':{'lessons':[{'lesson_id':'L1','title':'Qubit','sequence_order':1}]},
            }))
            e.enter_context(patch.object(lg.db,'teacher_evidence_bundle',return_value={}))
            e.enter_context(patch.object(lg.db,'query_one',return_value={'id':1,'primary_language_code':'en'}))
            e.enter_context(patch.object(lg.lesson_identity,'inspect_lesson_identity',return_value={'valid':True}))
            e.enter_context(patch.object(lg.db,'approve_teacher_full_lesson_blocks',return_value=None))
            e.enter_context(patch.object(lg,'lesson_completion',return_value={'complete':True}))
            result=lg.approve_full_lesson(1,'L1','teacher1')
        self.assertTrue(result['complete'])
