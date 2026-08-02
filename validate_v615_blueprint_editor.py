"""Behavioral validation for V6.15 blueprint editor and revision history."""

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


def cards() -> list[dict]:
    return [
        {"evidence_id": "E1", "claim": "يفهم المتعلم القيم قبل الإسناد والمتغيرات.", "source_ids": ["S1", "S2"], "evidence_excerpt": "Values and assignment are introduced before control flow.", "confidence": "high", "intended_use": ["lesson_explanation"], "review_status": "approved"},
        {"evidence_id": "E2", "claim": "يحتاج المبتدئ إلى أمثلة محلولة قبل التدريب المستقل.", "source_ids": ["S2"], "evidence_excerpt": "The tutorial uses progressive executable examples.", "confidence": "high", "intended_use": ["worked_example", "activity"], "review_status": "approved"},
    ]


def concepts() -> list[dict]:
    return [
        {"concept_id": "C1", "name": "القيمة", "description": "بيانات يعالجها البرنامج.", "prerequisites": [], "source_ids": ["S1", "S2"], "difficulty": "introductory", "review_status": "approved"},
        {"concept_id": "C2", "name": "المتغير", "description": "اسم يرتبط بقيمة.", "prerequisites": ["C1"], "source_ids": ["S1", "S2"], "difficulty": "introductory", "review_status": "approved"},
        {"concept_id": "C3", "name": "نوع البيانات", "description": "تصنيف القيمة والعمليات المناسبة.", "prerequisites": ["C2"], "source_ids": ["S1", "S2"], "difficulty": "introductory", "review_status": "approved"},
        {"concept_id": "C4", "name": "الإسناد", "description": "ربط اسم بقيمة.", "prerequisites": ["C1", "C2"], "source_ids": ["S1", "S2"], "difficulty": "introductory", "review_status": "approved"},
    ]


def main() -> None:
    db.init_db()
    project_id = db.save_teacher_project(project_payload())
    project = db.get_teacher_project(project_id, "validator")
    assert project

    evidence_id = db.save_teacher_evidence_bundle(
        project_id=project_id, phase_number=1, research_run_id=None,
        prompt_text="test", response_text="test", sources=sources(), evidence_cards=cards(), concepts=concepts(),
        quality={"readiness_score": 0.95, "approved_source_count": 2}, provider="deterministic", model="test", status="completed",
    )
    db.approve_teacher_evidence_run(evidence_id, project_id, "validator")
    evidence = db.teacher_evidence_bundle(evidence_id)
    assert evidence

    base = lesson_blueprint_engine.generate_and_persist(project, "validator", evidence_bundle=evidence, max_units=2, max_lessons=6)
    assert int(base.get("revision_number") or 1) == 1
    db.approve_teacher_blueprint_run(int(base["id"]), project_id, "validator")

    tables = lesson_blueprint_engine.editor_tables_from_blueprint(base["blueprint"])
    tables["units"][0]["title"] = "الوحدة الأولى: القيم والمتغيرات"
    tables["concepts"].append({
        "concept_id": "", "name": "التعبير البرمجي", "description": "تركيب ينتج قيمة.",
        "difficulty": "introductory", "prerequisites": "C1, C2", "source_ids": "S1, S2",
    })
    tables["lessons"].append({
        "lesson_id": "", "unit_id": tables["units"][0]["unit_id"], "sequence_order": 99,
        "title": "تطبيقات على التعبيرات", "duration_minutes": 35,
        "concept_ids": "C1, C2", "source_ids": "S1, S2", "prerequisites": "L1", "misconceptions": "خلط النص بالعدد",
    })
    tables["outcomes"].append({
        "outcome_id": "", "lesson_id": "L3", "bloom_level": "apply", "verb": "يطبّق",
        "object": "التعبيرات البرمجية في مثال قصير", "condition": "بعد مثال موجّه",
        "success_criterion": "ينفذ المثال دون خطأ", "activity_id": "", "assessment_id": "",
    })
    draft = lesson_blueprint_engine.blueprint_from_editor_tables(
        base["blueprint"], concepts=tables["concepts"], units=tables["units"], lessons=tables["lessons"], outcomes=tables["outcomes"],
    )
    revision = lesson_blueprint_engine.save_manual_revision(
        project, "validator", base_run_id=int(base["id"]), edited_blueprint=draft,
        change_summary="Added expression concept and an application lesson.",
    )
    assert int(revision.get("parent_run_id") or 0) == int(base["id"])
    assert int(revision.get("revision_number") or 0) == 2
    assert int(revision.get("approved_by_teacher") or 0) == 0
    assert revision["blueprint"]["units"][0]["title"].startswith("الوحدة الأولى")
    assert any(item["name"] == "التعبير البرمجي" for item in revision["concepts"])
    assert len(revision["lessons"]) == len(base["lessons"]) + 1
    assert revision["quality"]["alignment_rate"] == 1.0

    # The previously approved revision remains available until the edited draft is approved.
    approved_before = db.latest_teacher_blueprint(project_id, approved_only=True)
    assert approved_before and int(approved_before["id"]) == int(base["id"])

    history = db.teacher_blueprint_history_df(project_id)
    assert list(history["revision_number"].astype(int))[:2] == [2, 1]
    audit = db.teacher_blueprint_change_log_df(project_id, int(revision["id"]))
    assert not audit.empty
    assert "revision_created" in set(audit["action"])
    assert "added" in set(audit["action"])

    db.approve_teacher_blueprint_run(int(revision["id"]), project_id, "validator")
    approved_after = db.latest_teacher_blueprint(project_id, approved_only=True)
    assert approved_after and int(approved_after["id"]) == int(revision["id"])
    packet = lesson_blueprint_engine.build_blueprint_packet(approved_after)
    assert "الوحدة الأولى: القيم والمتغيرات" in packet

    restored = lesson_blueprint_engine.restore_blueprint_as_revision(
        project, "validator", source_run_id=int(base["id"]), parent_run_id=int(revision["id"]),
    )
    assert int(restored.get("revision_number") or 0) == 3
    assert int(restored.get("parent_run_id") or 0) == int(revision["id"])
    assert restored["blueprint"]["units"][0]["title"] == base["blueprint"]["units"][0]["title"]

    ui = (ROOT / "teacher_studio.py").read_text(encoding="utf-8")
    assert "blueprint_editor_form_" in ui
    assert "تحرير المخطط" in ui
    assert "الإصدارات وسجل التعديلات" in ui
    assert "restore_blueprint_as_revision" in ui
    assert 'APP_VERSION = "v6.15-blueprint-editor-versioning"' in (ROOT / "db.py").read_text(encoding="utf-8")

    print("V6.15 blueprint editor and revision history validation passed.")


if __name__ == "__main__":
    try:
        main()
    finally:
        try:
            os.unlink(_tmp.name)
        except OSError:
            pass
