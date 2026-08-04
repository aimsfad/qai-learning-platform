"""Behavioral validation for V6.15 blueprint editor and immutable versioning."""

from __future__ import annotations

import importlib
import os
import sys
import tempfile
import types
from pathlib import Path

_tmp = tempfile.NamedTemporaryFile(prefix="qai_v615_", suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

fake_st = types.ModuleType("streamlit")
fake_st.secrets = {
    "ENABLE_EVIDENCE_SYNTHESIS": "true",
    "REQUIRE_EVIDENCE_APPROVAL_FOR_GENERATION": "true",
    "ENABLE_LESSON_BLUEPRINT": "true",
    "REQUIRE_BLUEPRINT_APPROVAL_FOR_GENERATION": "true",
    "ENABLE_BLUEPRINT_EDITOR": "true",
    "BLUEPRINT_EDITOR_REQUIRE_CHANGE_SUMMARY": "true",
    "BLUEPRINT_MAX_UNITS": "5",
    "BLUEPRINT_MAX_LESSONS": "12",
    "BLUEPRINT_MIN_READINESS": "0.70",
}
fake_st.cache_resource = lambda *args, **kwargs: (lambda fn: fn)
sys.modules["streamlit"] = fake_st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

db = importlib.import_module("db")
lesson_blueprint_engine = importlib.import_module("lesson_blueprint_engine")


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


def sources() -> list[dict]:
    return [
        {"source_id": "S1", "title": "Python reference", "url": "https://docs.python.org/3/reference/", "canonical_url": "https://docs.python.org/3/reference", "domain": "docs.python.org", "source_type": "official", "language": "en", "publication_date": "unknown", "access_date": "2026-08-01", "snippet": "Assignment binds names to values.", "authority_score": 1.0, "relevance_score": 0.95, "freshness_score": 0.8, "pedagogical_score": 0.7, "accessibility_score": 0.7, "license_score": 0.7, "composite_score": 0.86, "status": "approved", "rationale": "official", "fingerprint": "s1"},
        {"source_id": "S2", "title": "Python tutorial", "url": "https://docs.python.org/3/tutorial/", "canonical_url": "https://docs.python.org/3/tutorial", "domain": "docs.python.org", "source_type": "tutorial", "language": "en", "publication_date": "unknown", "access_date": "2026-08-01", "snippet": "Examples cover values, variables, conditions and loops.", "authority_score": 1.0, "relevance_score": 0.96, "freshness_score": 0.8, "pedagogical_score": 0.95, "accessibility_score": 0.9, "license_score": 0.7, "composite_score": 0.91, "status": "approved", "rationale": "official tutorial", "fingerprint": "s2"},
    ]


def evidence_cards() -> list[dict]:
    return [
        {"evidence_id": "E1", "claim": "يفهم المتعلم القيم قبل الإسناد والمتغيرات.", "source_ids": ["S1", "S2"], "evidence_excerpt": "Values and assignment are introduced before control flow.", "confidence": "high", "intended_use": ["lesson_explanation"], "review_status": "approved"},
        {"evidence_id": "E2", "claim": "يحتاج المبتدئ إلى أمثلة محلولة قبل التدريب المستقل.", "source_ids": ["S2"], "evidence_excerpt": "The tutorial uses progressive executable examples.", "confidence": "high", "intended_use": ["worked_example", "activity"], "review_status": "approved"},
    ]


def concepts() -> list[dict]:
    return [
        {"concept_id": "C1", "name": "القيمة", "description": "بيانات يعالجها البرنامج.", "prerequisites": [], "source_ids": ["S1", "S2"], "difficulty": "introductory", "review_status": "approved"},
        {"concept_id": "C2", "name": "المتغير", "description": "اسم يرتبط بقيمة.", "prerequisites": ["القيمة"], "source_ids": ["S1", "S2"], "difficulty": "introductory", "review_status": "approved"},
        {"concept_id": "C3", "name": "نوع البيانات", "description": "تصنيف القيمة والعمليات المناسبة.", "prerequisites": ["المتغير"], "source_ids": ["S1", "S2"], "difficulty": "introductory", "review_status": "approved"},
        {"concept_id": "C4", "name": "الإسناد", "description": "ربط اسم بقيمة.", "prerequisites": ["القيمة", "المتغير"], "source_ids": ["S1", "S2"], "difficulty": "introductory", "review_status": "approved"},
    ]


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
        sources=sources(),
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

    baseline = lesson_blueprint_engine.generate_and_persist(project, "validator", evidence_bundle=evidence, max_units=3, max_lessons=8)
    assert int(baseline.get("version_number") or 0) == 1
    assert baseline.get("revision_type") == "generated"
    db.approve_teacher_blueprint_run(int(baseline["id"]), project_id, "validator")
    assert int((db.teacher_blueprint_bundle(int(baseline["id"])) or {}).get("approved_by_teacher") or 0) == 1

    draft = lesson_blueprint_engine.prepare_editor_draft(baseline)
    first_unit = str(draft["units"][0]["unit_id"])
    first_lesson = str(draft["lessons"][0]["lesson_id"])
    draft = lesson_blueprint_engine.update_unit(draft, first_unit, title="الوحدة التمهيدية", description="مراجعة بشرية للعنوان والوصف.")
    draft = lesson_blueprint_engine.add_unit(draft, "وحدة تطبيقية", "تجميع المفاهيم في مشروع مصغر.")
    new_unit = str(draft["units"][-1]["unit_id"])
    draft = lesson_blueprint_engine.add_lesson(draft, unit_id=new_unit, title="مشروع تطبيقي", duration_minutes=60, concept_ids="C1, C2", source_ids="S1, S2")
    new_lesson = str(draft["lessons"][-1]["lesson_id"])
    draft = lesson_blueprint_engine.add_outcome(
        draft,
        lesson_id=new_lesson,
        bloom_level="create",
        verb="ينشئ",
        object_text="برنامجًا صغيرًا يوظف القيم والمتغيرات",
        condition="بعد تحليل مثال محلول",
        success_criterion="تشغيل البرنامج دون أخطاء وتفسير المتغيرات المستخدمة.",
    )
    draft = lesson_blueprint_engine.move_unit(draft, new_unit, -1)
    draft = lesson_blueprint_engine.update_lesson(
        draft,
        first_lesson,
        unit_id=first_unit,
        title="القيم والمتغيرات",
        duration_minutes=50,
        concept_ids="C1, C2",
        source_ids="S1, S2",
        prerequisites="استخدام الحاسوب",
        misconceptions="الخلط بين الإسناد والمساواة",
    )
    comparison = lesson_blueprint_engine.compare_blueprints(baseline["blueprint"], draft)
    assert comparison["changed"] is True
    assert new_unit in comparison["units"]["added"]
    assert new_lesson in comparison["lessons"]["added"]

    quality = lesson_blueprint_engine.recompute_blueprint_quality(draft)
    assert quality["integrity_score"] == 1.0
    revision = lesson_blueprint_engine.save_manual_revision(
        project_id,
        int(baseline["id"]),
        "validator",
        draft,
        "Added an applied unit and refined lesson alignment.",
    )
    assert int(revision.get("version_number") or 0) == 2
    assert int(revision.get("parent_run_id") or 0) == int(baseline["id"])
    assert revision.get("revision_type") == "manual_edit"
    assert int(revision.get("approved_by_teacher") or 0) == 0
    assert int((db.teacher_blueprint_bundle(int(baseline["id"])) or {}).get("approved_by_teacher") or 0) == 0
    assert db.latest_teacher_blueprint(project_id, approved_only=True) is None

    db.approve_teacher_blueprint_run(int(revision["id"]), project_id, "validator")
    approved = db.latest_teacher_blueprint(project_id, approved_only=True)
    assert approved and int(approved["id"]) == int(revision["id"])

    restored_id = db.restore_teacher_blueprint_version(
        project_id=project_id,
        source_run_id=int(baseline["id"]),
        teacher_username="validator",
        change_summary="Restore the original generated structure for comparison.",
    )
    restored = db.teacher_blueprint_bundle(restored_id)
    assert restored
    assert int(restored.get("version_number") or 0) == 3
    assert restored.get("revision_type") == "restore"
    assert int(restored.get("restored_from_run_id") or 0) == int(baseline["id"])
    assert int(restored.get("approved_by_teacher") or 0) == 0
    assert db.latest_teacher_blueprint(project_id, approved_only=True) is None

    versions = db.teacher_blueprint_versions_df(project_id)
    assert len(versions) == 3
    assert set(versions["revision_type"].tolist()) == {"generated", "manual_edit", "restore"}
    audit = db.teacher_blueprint_audit_df(project_id)
    actions = set(audit["action"].tolist())
    assert {"generate", "approve", "manual_edit", "restore"}.issubset(actions)

    # Deletion helpers preserve referential integrity in a session draft.
    test_draft = lesson_blueprint_engine.delete_lesson(draft, new_lesson)
    assert new_lesson not in {str(item.get("lesson_id")) for item in test_draft.get("lessons") or []}
    assert not any(str(item.get("lesson_id")) == new_lesson for item in test_draft.get("outcomes") or [])
    test_draft = lesson_blueprint_engine.delete_unit(test_draft, new_unit, cascade=True)
    assert new_unit not in {str(item.get("unit_id")) for item in test_draft.get("units") or []}

    ui = (ROOT / "teacher_studio.py").read_text(encoding="utf-8")
    assert "render_blueprint_editor" in ui
    assert "render_blueprint_versions" in ui
    assert "محرر المخطط" in ui
    assert "الإصدارات والسجل" in ui
    assert any(v in (ROOT / "db.py").read_text(encoding="utf-8") for v in ('APP_VERSION = "v6.17.1-unified-guided-production-journey"', 'APP_VERSION = "v6.17.2-simplified-guided-research-flow"', 'APP_VERSION = "v6.17.3-blueprint-action-feedback-hotfix"', 'APP_VERSION = "v6.18-global-professional-design-system"', 'APP_VERSION = "v6.18.2-blueprint-editor-runtime-and-ui-polish"'))

    print("V6.15 blueprint editor and versioning validation passed.")


if __name__ == "__main__":
    try:
        main()
    finally:
        try:
            os.unlink(_tmp.name)
        except OSError:
            pass
