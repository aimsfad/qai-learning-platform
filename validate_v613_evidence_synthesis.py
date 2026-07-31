"""Behavioral validation for V6.13 evidence synthesis foundation."""

from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
import types
from pathlib import Path

_tmp = tempfile.NamedTemporaryFile(prefix="qai_v613_", suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

fake_st = types.ModuleType("streamlit")
fake_st.secrets = {
    "ENABLE_RESEARCH_AUGMENTED_GENERATION": "true",
    "ENABLE_EVIDENCE_SYNTHESIS": "true",
    "REQUIRE_EVIDENCE_APPROVAL_FOR_GENERATION": "true",
    "EVIDENCE_MIN_COMPOSITE_SCORE": "0.50",
}
fake_st.cache_resource = lambda *args, **kwargs: (lambda fn: fn)
sys.modules["streamlit"] = fake_st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

db = importlib.import_module("db")
web_research_engine = importlib.import_module("web_research_engine")
content_generation_engine = importlib.import_module("content_generation_engine")
evidence_synthesis_engine = importlib.import_module("evidence_synthesis_engine")
educational_builder = importlib.import_module("educational_builder")


def project_payload(name: str = "Evidence course") -> dict:
    return {
        "teacher_username": "validator",
        "project_name": name,
        "domain": "Programming",
        "program_name": "Python foundations",
        "unit_title": "Variables and data types",
        "target_concept": "Python variables and basic data types",
        "target_learners": "Secondary-school beginners",
        "learner_level": "Beginner",
        "prerequisites": "Basic computer use and print statements",
        "target_languages": ["Arabic", "French", "English"],
        "primary_language": "Arabic",
        "primary_language_code": "ar",
        "expected_duration": "45 minutes",
        "technical_environment": "Python 3 and Streamlit",
        "platform_components": ["AI Coach", "Assessment"],
        "source_material": "Teacher-authored notes.",
        "teaching_preferences": "Attempt first, then progressive hints.",
        "assessment_preferences": "Formative questions and a small coding task.",
        "additional_notes": "",
        "requested_outputs": ["Interactive lesson", "Assessment bank"],
        "current_phase": 1,
        "status": "draft",
    }


def research_sources() -> list[web_research_engine.ResearchSource]:
    return [
        web_research_engine.ResearchSource(
            "S1", "Python 3 language reference", "https://docs.python.org/3/reference/?utm_source=test",
            "docs.python.org", "official technical documentation", 5,
            "Names refer to objects and assignment binds names to values in Python 3.", 0.95,
        ),
        web_research_engine.ResearchSource(
            "S5", "Duplicate Python reference", "https://docs.python.org/3/reference/#objects-values-and-types",
            "docs.python.org", "official technical documentation", 5,
            "Duplicate reference entry for canonical URL testing.", 0.70,
        ),
        web_research_engine.ResearchSource(
            "S2", "Python tutorial - an informal introduction", "https://docs.python.org/3/tutorial/introduction.html",
            "docs.python.org", "official technical documentation", 5,
            "The tutorial introduces numbers, text, lists, and assignment with executable examples.", 0.91,
        ),
        web_research_engine.ResearchSource(
            "S3", "Teaching introductory programming", "https://example.edu/teaching/programming-2025",
            "example.edu", "university or academic institution", 5,
            "Worked examples and misconception-focused formative assessment improve beginner instruction.", 0.82,
        ),
        web_research_engine.ResearchSource(
            "S4", "Open course activity", "https://ocw.mit.edu/courses/python/",
            "ocw.mit.edu", "open educational resource", 4,
            "Open educational activities include short exercises and practice tasks.", 0.76,
        ),
    ]


def synthesis_json() -> str:
    return json.dumps(
        {
            "evidence_cards": [
                {
                    "claim": "في بايثون تربط عملية الإسناد اسم المتغير بكائن أو قيمة.",
                    "source_ids": ["S1", "S2"],
                    "evidence_excerpt": "توضح وثائق بايثون المرجعية والبرنامج التعليمي معنى الإسناد وربط الأسماء بالقيم.",
                    "confidence": "high",
                    "intended_use": ["lesson_explanation", "worked_example"],
                },
                {
                    "claim": "تساعد الأمثلة المحلولة المتدرجة المبتدئ على التمييز بين النصوص والأعداد.",
                    "source_ids": ["S2", "S3"],
                    "evidence_excerpt": "يجمع البرنامج التعليمي الرسمي بين الأمثلة القابلة للتنفيذ وإرشادات التدريس الجامعية.",
                    "confidence": "high",
                    "intended_use": ["worked_example", "activity"],
                },
                {
                    "claim": "ينبغي أن يتضمن التقويم التكويني أخطاء شائعة مرتبطة بالإسناد وأنواع البيانات.",
                    "source_ids": ["S3"],
                    "evidence_excerpt": "يركز دليل التدريس على كشف التصورات الخاطئة عبر أسئلة قصيرة.",
                    "confidence": "moderate",
                    "intended_use": ["misconception", "assessment"],
                },
                {
                    "claim": "يمكن استعمال أنشطة تعليمية مفتوحة لتوفير تدريب مستقل قصير.",
                    "source_ids": ["S4"],
                    "evidence_excerpt": "يوفر المورد التعليمي المفتوح أنشطة وتمارين عملية.",
                    "confidence": "moderate",
                    "intended_use": ["activity", "teacher_note"],
                },
            ],
            "concepts": [
                {
                    "name": "القيمة",
                    "description": "بيانات يعالجها البرنامج مثل العدد أو النص.",
                    "prerequisites": [],
                    "source_ids": ["S1", "S2"],
                    "difficulty": "introductory",
                },
                {
                    "name": "المتغير",
                    "description": "اسم يرتبط بقيمة أو كائن داخل البرنامج.",
                    "prerequisites": ["القيمة"],
                    "source_ids": ["S1", "S2"],
                    "difficulty": "introductory",
                },
                {
                    "name": "نوع البيانات",
                    "description": "تصنيف يحدد طبيعة القيمة والعمليات المناسبة لها.",
                    "prerequisites": ["القيمة", "المتغير"],
                    "source_ids": ["S1", "S2"],
                    "difficulty": "introductory",
                },
                {
                    "name": "الإسناد",
                    "description": "عملية ربط اسم بقيمة باستعمال عامل الإسناد.",
                    "prerequisites": ["المتغير", "نوع البيانات"],
                    "source_ids": ["S1", "S2"],
                    "difficulty": "introductory",
                },
            ],
            "quality_notes": [],
        },
        ensure_ascii=False,
    )


def long_phase_output() -> str:
    sections = ["# المرحلة 1: تدقيق الأدلة والمفهوم"]
    for index in range(1, 12):
        sections.append(
            f"## القسم {index}\n- محتوى تعليمي موثق بالمصدر [S1] ومدعوم بمثال [S2]. "
            + ("شرح منظم مناسب للمبتدئين. " * 10)
        )
    sections.append("## فحوص التوليد\n- تمت مراجعة الأدلة والافتراضات، وتبقى الموافقة النهائية للأستاذ.")
    return "\n\n".join(sections)


def main() -> None:
    db.init_db()
    project_id = db.save_teacher_project(project_payload())
    project = db.get_teacher_project(project_id, "validator")
    assert project

    research = web_research_engine.ResearchResult(
        report="Python names, assignment, types, examples, and misconception-based assessment are supported by the listed sources.",
        sources=research_sources(),
        queries=["Python variables official documentation", "introductory programming misconceptions"],
        provider="gemini",
        model="gemini-test",
        status="completed",
        diagnostic="Research passed checks.",
        latency_ms=120,
    )
    research_run_id = db.save_teacher_research_run(
        project_id=project_id,
        phase_number=1,
        research_mode="balanced",
        query_plan_json=json.dumps(research.queries),
        report_text=research.report,
        sources_json=web_research_engine.sources_to_json(research.sources),
        provider=research.provider,
        model=research.model,
        status=research.status,
        diagnostic=research.diagnostic,
        source_count=len(research.sources),
        latency_ms=research.latency_ms,
    )
    research_run = db.latest_teacher_research(project_id, 1)
    assert research_run and int(research_run["id"]) == research_run_id

    original_generate = content_generation_engine.generate_content
    content_generation_engine.generate_content = lambda *args, **kwargs: content_generation_engine.ContentGenerationResult(
        response=synthesis_json(), provider="mock", model="evidence-json", status="completed", latency_ms=210
    )
    try:
        bundle = evidence_synthesis_engine.synthesize_and_persist(
            project,
            "validator",
            phase_number=1,
            research_run=research_run,
        )
    finally:
        content_generation_engine.generate_content = original_generate

    assert bundle["status"] in {"completed", "needs_review"}
    assert len(bundle["sources"]) == 4, "tracking/fragment duplicate should be removed"
    assert len(bundle["evidence_cards"]) == 4
    assert len(bundle["concepts"]) == 4
    assert bundle["quality"]["source_coverage"] >= 0.75
    assert bundle["quality"]["approved_source_count"] >= 3
    assert all(card["source_ids"] for card in bundle["evidence_cards"])

    # Strict gate rejects generation before teacher approval.
    raised = False
    try:
        educational_builder.generate_project_phase(project, "validator", phase_number=1, research_mode="balanced")
    except ValueError as exc:
        raised = "approved" in str(exc).lower()
    assert raised

    db.approve_teacher_evidence_run(int(bundle["id"]), project_id, "validator")
    approved = db.latest_teacher_evidence(project_id, 1, approved_only=True)
    assert approved and int(approved["approved_by_teacher"]) == 1
    packet = evidence_synthesis_engine.build_evidence_packet(approved)
    assert "teacher_reviewable_evidence_synthesis" in packet
    assert "[E1]" in packet and "[C1]" in packet and "[S1]" in packet

    prompt = educational_builder.compile_project_prompt(project, 1)
    assert "teacher_reviewable_evidence_synthesis" in prompt
    assert "Teacher approval: approved" in prompt
    assert "Evidence cards" in prompt

    content_generation_engine.generate_content = lambda *args, **kwargs: content_generation_engine.ContentGenerationResult(
        response=long_phase_output(), provider="mock", model="phase-writer", status="completed", latency_ms=300
    )
    try:
        outcome = educational_builder.generate_project_phase(
            project,
            "validator",
            phase_number=1,
            research_mode="balanced",
        )
    finally:
        content_generation_engine.generate_content = original_generate
    assert outcome.status == "completed", outcome.diagnostic
    assert outcome.evidence_approved is True
    assert outcome.evidence_card_count == 4
    assert outcome.next_phase == 2

    ui_text = (ROOT / "teacher_studio.py").read_text(encoding="utf-8")
    assert "render_evidence_synthesis" in ui_text
    assert "تركيب الأدلة" in ui_text
    assert 'sections = ["overview", "production", "evidence", "assets", "publish"]' in ui_text

    print("V6.13 evidence synthesis foundation validation passed.")


if __name__ == "__main__":
    try:
        main()
    finally:
        try:
            os.unlink(_tmp.name)
        except OSError:
            pass
