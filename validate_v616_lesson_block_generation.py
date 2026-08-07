"""Behavioral validation for V6.16 block-level lesson generation."""
from __future__ import annotations
import importlib, os, sys, tempfile, types
from pathlib import Path

_tmp=tempfile.NamedTemporaryFile(prefix='qai_v616_',suffix='.db',delete=False); _tmp.close()
os.environ['DATABASE_URL']=f'sqlite:///{_tmp.name}'
fake_st=types.ModuleType('streamlit')
fake_st.secrets={
 'ENABLE_EVIDENCE_SYNTHESIS':'true','REQUIRE_EVIDENCE_APPROVAL_FOR_GENERATION':'true',
 'ENABLE_LESSON_BLUEPRINT':'true','REQUIRE_BLUEPRINT_APPROVAL_FOR_GENERATION':'true',
 'ENABLE_BLUEPRINT_EDITOR':'true','ENABLE_LESSON_BLOCK_GENERATION':'true',
 'REQUIRE_BLOCK_APPROVAL_FOR_LESSON_COMPLETION':'true'
}
fake_st.cache_resource=lambda *a,**k:(lambda fn:fn)
sys.modules['streamlit']=fake_st
ROOT=Path(__file__).resolve().parent; sys.path.insert(0,str(ROOT))
db=importlib.import_module('db')
lesson_blueprint_engine=importlib.import_module('lesson_blueprint_engine')
engine=importlib.import_module('lesson_block_generation_engine')
content_generation_engine=importlib.import_module('content_generation_engine')

def project_payload():
 return {'teacher_username':'validator','project_name':'Python foundations','domain':'Programming','program_name':'Python foundations','unit_title':'Variables','target_concept':'Python values and variables','target_learners':'Beginners','learner_level':'Beginner','prerequisites':'Basic computer use','target_languages':['Arabic'],'primary_language':'Arabic','primary_language_code':'ar','expected_duration':'120 minutes','technical_environment':'Python 3','platform_components':['AI Coach'],'source_material':'Teacher notes','teaching_preferences':'Attempt first','assessment_preferences':'Formative tasks','additional_notes':'','requested_outputs':['Lessons'],'current_phase':3,'status':'draft'}

def main():
 db.init_db(); pid=db.save_teacher_project(project_payload()); project=db.get_teacher_project(pid,'validator')
 sources=[{'source_id':'S1','title':'Python tutorial','url':'https://docs.python.org/3/tutorial/','canonical_url':'https://docs.python.org/3/tutorial','domain':'docs.python.org','source_type':'official','language':'en','publication_date':'unknown','access_date':'2026-08-02','snippet':'Values and assignment.','authority_score':1.0,'relevance_score':1.0,'freshness_score':0.8,'pedagogical_score':0.9,'accessibility_score':0.8,'license_score':0.7,'composite_score':0.9,'status':'approved','rationale':'official','fingerprint':'s1'}]
 cards=[{'evidence_id':'E1','claim':'القيم تسبق المتغيرات.','source_ids':['S1'],'evidence_excerpt':'Values and assignment','confidence':'high','intended_use':['lesson_explanation'],'review_status':'approved'}]
 concepts=[{'concept_id':'C1','name':'القيمة','description':'بيانات','prerequisites':[],'source_ids':['S1'],'difficulty':'introductory','review_status':'approved'},{'concept_id':'C2','name':'المتغير','description':'اسم يرتبط بقيمة','prerequisites':['القيمة'],'source_ids':['S1'],'difficulty':'introductory','review_status':'approved'}]
 erid=db.save_teacher_evidence_bundle(project_id=pid,phase_number=1,research_run_id=None,prompt_text='p',response_text='r',sources=sources,evidence_cards=cards,concepts=concepts,quality={'readiness_score':.9,'approved_source_count':1},provider='deterministic',model='test',status='completed')
 db.approve_teacher_evidence_run(erid,pid,'validator'); evidence=db.teacher_evidence_bundle(erid)
 blueprint=lesson_blueprint_engine.generate_and_persist(project,'validator',evidence_bundle=evidence,max_units=2,max_lessons=4)
 db.approve_teacher_blueprint_run(int(blueprint['id']),pid,'validator'); blueprint=db.teacher_blueprint_bundle(int(blueprint['id']))
 lesson_id=str(blueprint['lessons'][0]['lesson_id'])
 def fake_generate(*a,**k):
  return content_generation_engine.ContentGenerationResult(response='# شرح المفهوم\n\nهذا شرح تدريجي للقيمة والمتغير، يبدأ بسؤال قصير ثم مثال بلغة بايثون. يطلب من المتعلم التنبؤ بالنتيجة قبل عرض التفسير، ويربط الشرح بالهدف التعليمي المحدد في المخطط. [S1]\n\n## Teacher implementation note\nاستخدم التنفيذ المباشر واطلب تفسير كل سطر. ' * 3,provider='mock',model='mock-v1',status='completed',latency_ms=10)
 content_generation_engine.generate_content=fake_generate
 first=engine.generate_and_persist(project,'validator',blueprint,lesson_id,'explanation')
 assert first and first['block_type']=='explanation' and int(first['version_number'])==1
 assert first['validation']['status'] in {'completed','needs_review'}
 db.approve_teacher_lesson_block(int(first['id']),pid,'validator')
 approved=db.latest_teacher_lesson_block(pid,lesson_id,'explanation',approved_only=True)
 assert approved and int(approved['id'])==int(first['id'])
 revision=engine.save_teacher_revision(project_id=pid,base_run_id=int(first['id']),teacher_username='validator',content_text=str(first['content_text'])+'\n\nمراجعة الأستاذ.',change_summary='Refined wording.')
 assert int(revision['version_number'])==2 and revision['revision_type']=='manual_edit'
 assert int(revision['approved_by_teacher'] or 0)==0
 versions=db.teacher_lesson_block_versions_df(pid,lesson_id,'explanation'); assert len(versions)==2
 audit=db.teacher_lesson_block_audit_df(pid,lesson_id); assert {'generated','approved','manual_edit'}.issubset(set(audit['action'].tolist()))
 prompt=engine.build_block_prompt(project,blueprint,lesson_id,'worked_example',previous_blocks=[approved])
 assert 'Generate ONE lesson block only' in prompt and lesson_id in prompt and 'S1' in prompt
 invalid=engine.validate_block_content('summary','# ملخص\nادعاء [S99]',['S1']); assert invalid['status']=='error'
 ui=(ROOT/'teacher_studio.py').read_text(encoding='utf-8'); assert 'render_lesson_blocks' in ui and ('بناء محتوى الدرس على مستوى الكتل' in ui or 'بناء الدروس' in ui)
 assert any(v in (ROOT/'db.py').read_text(encoding='utf-8') for v in ('APP_VERSION = "v6.17.1-unified-guided-production-journey"', 'APP_VERSION = "v6.17.2-simplified-guided-research-flow"', 'APP_VERSION = "v6.17.3-blueprint-action-feedback-hotfix"', 'APP_VERSION = "v6.18-global-professional-design-system"', 'APP_VERSION = "v6.18.7-frictionless-ui-contract"', 'APP_VERSION = "v6.18.6-unified-premium-platform-design"', 'APP_VERSION = "v6.18.5-premium-lesson-workspace"', 'APP_VERSION = "v6.18.4-simple-teacher-journey"', 'APP_VERSION = "v6.18.3-guided-blueprint-lesson-production"', 'APP_VERSION = "v6.18.2-blueprint-editor-runtime-and-ui-polish"'))
 print('V6.16 lesson block generation validation passed.')

if __name__=='__main__':
 try: main()
 finally:
  try: os.unlink(_tmp.name)
  except OSError: pass
