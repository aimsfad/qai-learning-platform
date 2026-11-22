from __future__ import annotations
import importlib.util, json, sys, types, unittest
from pathlib import Path
from dataclasses import dataclass
from unittest.mock import Mock

@dataclass(frozen=True)
class ResearchSource:
    source_id:str
    title:str
    url:str
    domain:str
    source_type:str
    authority_level:int
    snippet:str = ""
    relevance_score:float = 0.0

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self._saved={k:sys.modules.get(k) for k in ('db','hybrid_rag','web_research_engine')}
        self.saved=[]
        self.docs=[dict(source_id='RAGCABC', name='Teacher ref',approved=True,cloud_generation_consent=True)]
        self.hits=[dict(source_id='RAGCABC',citation_key='RAGCABC_P0_C2',body='Machine learning uses training examples.')]
        self.idx=types.SimpleNamespace(list_documents=Mock(side_effect=lambda **k:self.docs), search=Mock(side_effect=lambda **k:types.SimpleNamespace(hits=self.hits,retrieval_mode='lexical')))
        sys.modules['db']=types.SimpleNamespace(get_teacher_project=lambda pid,o:{'id':pid} if o=='teacher' else None,save_teacher_research_run=Mock(side_effect=lambda **kw:self.saved.append(kw) or 29))
        sys.modules['hybrid_rag']=types.SimpleNamespace(enabled=lambda:True,open_index=lambda:self.idx)
        sys.modules['web_research_engine']=types.SimpleNamespace(ResearchSource=ResearchSource,sources_from_json=lambda v:[ResearchSource(**d) for d in json.loads(v)])
        spec=importlib.util.spec_from_file_location('rag_course_sources',str(Path(__file__).resolve().parent.parent / 'rag_course_sources.py'))
        self.mod=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)
    def tearDown(self):
        for k,v in self._saved.items():
            if v is None:sys.modules.pop(k,None)
            else:sys.modules[k]=v
        sys.modules.pop('rag_course_sources',None)
    def test_creates_reviewable_local_dossier(self):
        rid=self.mod.create_local_rag_dossier({'id':5},owner='teacher',query='Machine learning')
        self.assertEqual(rid,29)
        d=self.saved[0]
        self.assertEqual(d['status'],'needs_review')
        self.assertEqual(d['provider'],'teacher_rag')
        self.assertEqual(d['source_count'],1)
        self.assertIn('NOT web research',d['report_text'])
        self.assertIn('RAGCABC_P0_C2',d['report_text'])
        self.assertEqual(json.loads(d['sources_json'])[0]['source_id'],'RAGCABC')
        self.assertTrue(self.idx.search.call_args.kwargs['for_generation'])
        self.assertEqual(self.idx.search.call_args.kwargs['project_id'],5)
    def test_denies_wrong_project_owner(self):
        with self.assertRaisesRegex(ValueError,'access denied'):
            self.mod.create_local_rag_dossier({'id':5},owner='stranger',query='ML')
        self.assertFalse(self.saved)
    def test_cloud_permission_required(self):
        self.docs[0]['cloud_generation_consent']=False
        with self.assertRaisesRegex(ValueError,'cloud generation'):
            self.mod.create_local_rag_dossier({'id':5},owner='teacher',query='ML')
        self.assertFalse(self.saved)
    def test_empty_search_prevents_dossier(self):
        self.hits.clear()
        with self.assertRaisesRegex(ValueError,'No approved'):
            self.mod.create_local_rag_dossier({'id':5},owner='teacher',query='ML')
        self.assertFalse(self.saved)
    def test_snapshot_invalidated_after_revoke(self):
        run={'provider':'teacher_rag','sources_json':json.dumps([dict(source_id='RAGCABC',title='doc',url='',domain='teacher-upload',source_type='teacher',authority_level=3)])}
        self.assertEqual(self.mod.current_snapshot_error(run,owner='teacher',project_id=5),'')
        self.docs[0]['approved']=False
        self.assertIn('revoked',self.mod.current_snapshot_error(run,owner='teacher',project_id=5))
        self.assertEqual(self.mod.current_snapshot_error({'provider':'gemini'},owner='teacher',project_id=5),'')

if __name__=='__main__': unittest.main()
