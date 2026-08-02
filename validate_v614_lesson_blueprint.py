"""Behavioral validation for V6.14 evidence-to-lesson blueprint."""

from __future__ import annotations

import importlib
import os
import sys
import tempfile
import types
from pathlib import Path

_tmp = tempfile.NamedTemporaryFile(prefix="qai_v614_", suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

fake_st = types.ModuleType("streamlit")
fake_st.secrets = {
    "ENABLE_RESEARCH_AUGMENTED_GENERATION": "false",
    "ENABLE_EVIDENCE_SYNTHESIS": "true",
    "REQUIRE_EVIDENCE_APPROVAL_FOR_GENERATION": "true",
    "ENABLE_LESSON_BLUEPRINT": "true",
    "REQUIRE_BLUEPRINT_APPROVAL_FOR_GENERATION": "true",
    "BLUEPRINT_MAX_UNITS": "4",
    "BLUEPRINT_MAX_LESSONS": "10",
    "BLUEPRINT_MIN_READINESS": "0.70",
}
fake_st.cache_resource = lambda *args, **kwargs: (lambda fn: fn)
sys.modules["streamlit"] = fake_st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

db = importlib.import_module("db")
content_generation_engine = importlib.import_module("content_generation_engine")
lesson_blueprint_engine = importlib.import_module("lesson_blueprint_engine")
educational_builder = importlib.import_module("educational_builder")


def project_payload() -> dict:
    return {
        "teacher_username": "validator",
        "project_name": "Python foundations",
        "domain": "Programming",
        "program_name": "Python foundations",
        "unit_title": "Python variables and control flow",
        "target_concept": "A sequenced beginner course in Python programming",
        "target_learners": "Secondary-school beginners",
        "learner_level": "Beginner",
        "prerequisites": "Basic computer use",
        "target_languages": ["Arabic", "English"],
        "primary_language": "Arabic",
        "primary_language_code": "ar",
        "expected_duration": "300 minutes",
        "technical_environment": "Python 3",
        "platform_components": ["AI Coach", "Assessment"],
        "source_material": "Teacher notes",
        "teaching_preferences": "Attempt first and progressive hints",
        "assessment_preferences": "Formative coding tasks",
        "additional_notes": "",
        "requested_outputs": ["Lessons", "Assessments"],
        "current_phase": 3,
        "status": "draft",
    }


def evidence_sources() -> list[dict]:
    return [
        {"source_id": "S1", "title": "Python reference", "url": "https://docs.python.org/3/reference/", "canonical_url": "https://docs.python.org/3/reference", "domain": "docs.python.org", "source_type": "official", "language": "en", "publication_date": "unknown", "access_date": "2026-08-01", "snippet": "Assignment binds names to values.", "authority_score": 1.0, "relevance_score": 0.95, "freshness_score": 0.8, "pedagogical_score": 0.7, "accessibility_score": 0.7, "license_score": 0.7, "composite_score": 0.86, "status": "approved", "rationale": "official", "fingerprint": "s1"},
        {"source_id": "S2", "title": "Python tutorial", "url": "https://docs.python.org/3/tutorial/", "canonical_url": "https://docs.python.org/3/tutorial", "domain": "docs.python.org", "source_type": "tutorial", "language": "en", "publication_date": "unknown", "access_date": "2026-08-01", "snippet": "Examples cover values, variables, conditions and loops.", "authority_score": 1.0, "relevance_score": 0.96, "freshness_score": 0.8, "pedagogical_score": 0.95, "accessibility_score": 0.9, "license_score": 0.7, "composite_score": 0.91, "status": "approved", "rationale": "official tutorial", "fingerprint": "s2"},
    ]


def evidence_cards() -> list[dict]:
    return [
        {"evidence_id": "E1", "claim": "يفهم المتعلم القيم قبل الإسناد والمتغيرات.", "source_ids": ["S1", "S2"], "evidence_excerpt": "Values and assignment are introduced before control flow.", "confidence": "high", "intended_use": ["lesson_explanation"], "review_status": "approved"},
        {"evidence_id": "E2", "claim": "يحتاج المبتدئ إلى أمثلة محلولة قبل التدريب المستقل.", "source_ids": ["S2"], "evidence_excerpt": "The tutorial uses progressive executable examples.", "confidence": "high", "intended_use": ["worked_example", "activity"], "review_status": "approved"},
        {"evidence_id": "E3", "claim": "يخلط بعض المتعلمين بين الإسناد والمساواة الرياضية.", "source_ids": ["S1"], "evidence_excerpt": "Assignment syntax requires explicit misconception handling.", "confidence": "moderate", "intended_use": ["misconception", "assessment"], "review_status": "approved"},
    ]


def concepts() -> list[dict]:
    return [
        {"concept_id": "C1", "name": "القيمة", "description": "بيانات يعالجها البرنامج.", "prerequisites": [], "source_ids": ["S1", "S2"], "difficulty": "introductory", "review_status": "approved"},
        {"concept_id": "C2", "name": "المتغير", "description": "اسم يرتبط بقيمة.", "prerequisites": ["القيمة"], "source_ids": ["S1", "S2"], "difficulty": "introductory", "review_status": "approved"},
        {"concept_id": "C3", "name": "نوع البيانات", "description": "تصنيف القيمة والعمليات المناسبة.", "prerequisites": ["المتغير"], "source_ids": ["S1", "S2"], "difficulty": "introductory", "review_status": "approved"},
        {"concept_id": "C4", "name": "الإسناد", "description": "ربط اسم بقيمة.", "prerequisites": ["القيمة", "المتغير"], "source_ids": ["S1", "S2"], "difficulty": "introductory", "review_status": "approved"},
        {"concept_id": "C5", "name": "الجملة الشرطية", "description": "اتخاذ قرار حسب شرط.", "prerequisites": ["نوع البيانات", "الإسناد"], "source_ids": ["S2"], "difficulty": "intermediate", "review_status": "approved"},
        {"concept_id": "C6", "name": "الحلقة", "description": "تكرار تعليمات وفق نطاق أو شرط.", "prerequisites": ["الجملة الشرطية"], "source_ids": ["S2"], "difficulty": "intermediate", "review_status": "approved"},
    ]


def long_output() -> str:
    blocks = ["# المرحلة 3: المحتوى التعليمي الأساسي"]
    for i in range(1, 10):
        blocks.append(f"## القسم {i}\n- محتوى منظم يحافظ على معرفات الدروس والأهداف. " + ("شرح تطبيقي مناسب للمبتدئين. " * 14))
    blocks.append("## فحوص التوليد\n- المخطط معتمد، والمحاذاة محفوظة، وتبقى المراجعة النهائية للأستاذ.")
    return "\n\n".join(blocks)


def main() -> None:
    db.init_db()
    project_id = db.save_teacher_project(project_payload())
    project = db.get_teacher_project(project_id, "validator")
    assert project

    evidence_run_id = db.save_teacher_evidence_bundle(
        project_id=project_id,
        phase_number=1,
        research_run_id=None,
        prompt_text="test",
        response_text="test",
        sources=evidence_sources(),
        evidence_cards=evidence_cards(),
        concepts=concepts(),
        quality={"readiness_score": 0.95, "approved_source_count": 2},
        provider="deterministic",
        model="test",
        status="completed",
    )
    db.approve_teacher_evidence_run(evidence_run_id, project_id, "validator")
    evidence = db.teacher_evidence_bundle(evidence_run_id)
    assert evidence and int(evidence["approved_by_teacher"]) == 1

    # Strict blueprint gate blocks long-form generation before approval.
    raised = False
    try:
        educational_builder.generate_project_phase(project, "validator", phase_number=3, research_mode="off")
    except ValueError as exc:
        raised = "blueprint" in str(exc).lower()
    assert raised

    blueprint = lesson_blueprint_engine.generate_and_persist(
        project,
        "validator",
        evidence_bundle=evidence,
        max_units=3,
        max_lessons=8,
    )
    assert blueprint["quality"]["readiness_score"] >= 0.70
    assert len(blueprint["units"]) >= 1
    assert len(blueprint["lessons"]) == 3
    assert len(blueprint["outcomes"]) == 6
    assert blueprint["quality"]["alignment_rate"] == 1.0
    assert blueprint["quality"]["source_traceability"] == 1.0
    assert blueprint["concept_edges"]
    assert all(item.get("activity_id") and item.get("assessment_id") for item in blueprint["outcomes"])

    # Unapproved blueprint remains blocked.
    raised = False
    try:
        educational_builder.generate_project_phase(project, "validator", phase_number=3, research_mode="off")
    except ValueError as exc:
        raised = "blueprint" in str(exc).lower()
    assert raised

    db.approve_teacher_blueprint_run(int(blueprint["id"]), project_id, "validator")
    approved = db.latest_teacher_blueprint(project_id, approved_only=True)
    assert approved and int(approved["approved_by_teacher"]) == 1
    packet = lesson_blueprint_engine.build_blueprint_packet(approved)
    assert "[U#]" not in packet
    assert "U1" in packet and "L1" in packet and "LO1.1" in packet

    original_generate = content_generation_engine.generate_content
    content_generation_engine.generate_content = lambda *args, **kwargs: content_generation_engine.ContentGenerationResult(
        response=long_output(), provider="mock", model="phase3", status="completed", latency_ms=20
    )
    try:
        outcome = educational_builder.generate_project_phase(project, "validator", phase_number=3, research_mode="off")
    finally:
        content_generation_engine.generate_content = original_generate
    assert outcome.status == "completed", outcome.diagnostic
    assert outcome.blueprint_approved is True
    assert outcome.blueprint_lesson_count == 3
    assert "<teacher_approved_lesson_blueprint>" in outcome.prompt
    assert "LO1.1" in outcome.prompt

    ui = (ROOT / "teacher_studio.py").read_text(encoding="utf-8")
    assert "render_lesson_blueprint" in ui
    assert "مخطط المقرر" in ui
    assert 'guided_teacher_workflow.WORKFLOW_STEPS' in ui

    print("V6.14 evidence-to-lesson blueprint validation passed.")


if __name__ == "__main__":
    try:
        main()
    finally:
        try:
            os.unlink(_tmp.name)
        except OSError:
            pass
