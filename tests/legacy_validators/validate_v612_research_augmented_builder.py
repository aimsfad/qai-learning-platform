"""Behavioral validation for V6.12 research-augmented educational generation."""

from __future__ import annotations

import importlib
import os
import sys
import tempfile
import types
from pathlib import Path

_tmp = tempfile.NamedTemporaryFile(prefix="qai_v612_", suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

fake_st = types.ModuleType("streamlit")
fake_st.secrets = {
    "ENABLE_RESEARCH_AUGMENTED_GENERATION": "true",
    "DEFAULT_CONTENT_RESEARCH_MODE": "balanced",
}
fake_st.cache_resource = lambda *args, **kwargs: (lambda fn: fn)
sys.modules["streamlit"] = fake_st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

db = importlib.import_module("db")
web_research_engine = importlib.import_module("web_research_engine")
content_generation_engine = importlib.import_module("content_generation_engine")
educational_builder = importlib.import_module("educational_builder")


def project_payload() -> dict:
    return {
        "teacher_username": "validator",
        "project_name": "Python course",
        "domain": "Programming",
        "program_name": "Python foundations",
        "unit_title": "Variables and data types",
        "target_concept": "Python variables and basic data types",
        "target_learners": "Secondary-school beginners",
        "learner_level": "Beginner",
        "prerequisites": "Basic computer use",
        "target_languages": ["Arabic", "French", "English"],
        "primary_language": "Arabic",
        "primary_language_code": "ar",
        "expected_duration": "45 minutes",
        "technical_environment": "Python 3 and Streamlit",
        "platform_components": ["AI Coach", "Assessment"],
        "source_material": "Teacher-authored notes.",
        "teaching_preferences": "Attempt first, then progressive hints.",
        "assessment_preferences": "Formative questions and a small task.",
        "additional_notes": "",
        "requested_outputs": ["Interactive lesson", "Assessment bank"],
        "current_phase": 1,
        "status": "draft",
    }


def long_output() -> str:
    blocks = ["# المرحلة 1: تدقيق الأدلة والمفهوم"]
    for i in range(1, 14):
        blocks.append(
            f"## قسم {i}\n- معلومة تعليمية موثقة [S1] ومعلومة تطبيقية حديثة [S2]. "
            + ("محتوى تعليمي متحقق ومنظم. " * 8)
        )
    blocks.append("## فحوص التوليد\n- فجوات الأدلة: لا توجد ضمن نطاق الاختبار.\n- عناصر موافقة الأستاذ: المراجعة النهائية.")
    return "\n\n".join(blocks)


def main() -> None:
    db.init_db()
    project_id = db.save_teacher_project(project_payload())
    project = db.get_teacher_project(project_id, "validator")
    assert project

    mock_result = web_research_engine.ResearchResult(
        report=(
            "# Verified findings\nPython variables bind names to objects [S1]. "
            "Current official documentation should be used for syntax and examples [S2]. "
            "Active learning is suitable for misconception diagnosis [S3]."
        ),
        sources=[
            web_research_engine.ResearchSource("S1", "Python language reference", "https://docs.python.org/3/reference/", "docs.python.org", "official technical documentation", 5),
            web_research_engine.ResearchSource("S2", "Python tutorial", "https://docs.python.org/3/tutorial/", "docs.python.org", "official technical documentation", 5),
            web_research_engine.ResearchSource("S3", "University teaching guide", "https://example.edu/teaching", "example.edu", "university or academic institution", 5),
        ],
        queries=["Python variables official documentation", "Python variable misconceptions teaching"],
        provider="gemini",
        model="gemini-3.6-flash",
        status="completed",
        diagnostic="Research dossier passed checks.",
        latency_ms=250,
    )

    original_research = web_research_engine.run_phase_research
    web_research_engine.run_phase_research = lambda *args, **kwargs: mock_result
    try:
        stored = educational_builder.run_project_research(
            project,
            "validator",
            phase_number=1,
            research_mode="balanced",
            max_sources=8,
        )
    finally:
        web_research_engine.run_phase_research = original_research

    assert stored["status"] == "completed"
    assert int(stored["source_count"]) == 3
    packet = web_research_engine.build_research_packet(stored)
    assert "<web_research_packet>" in packet
    assert "[S1]" in packet and "docs.python.org" in packet

    prompt = educational_builder.compile_project_prompt(project, 1)
    assert "# Verified web-research evidence" in prompt
    assert "Research-grounding contract" in prompt
    assert "[S1]" in prompt
    compact = content_generation_engine.compact_prompt_for_budget(prompt, 2200)
    assert "web-research" in compact.lower() or "web_research_packet" in compact

    original_generation = content_generation_engine.generate_content
    content_generation_engine.generate_content = lambda *args, **kwargs: content_generation_engine.ContentGenerationResult(
        response=long_output(),
        provider="mock",
        model="mock-model",
        status="completed",
        latency_ms=321,
    )
    try:
        outcome = educational_builder.generate_project_phase(
            project,
            "validator",
            phase_number=1,
            research_mode="balanced",
            max_research_sources=8,
        )
    finally:
        content_generation_engine.generate_content = original_generation

    assert outcome.status == "completed", outcome.diagnostic
    assert outcome.next_phase == 2
    assert outcome.research_source_count == 3
    assert outcome.research_provider == "gemini"
    latest = db.latest_teacher_generation(project_id)
    assert latest and latest["status"] == "completed"
    assert "Citation check passed" in latest["diagnostic"]

    # A research dossier that needs teacher review must never silently advance
    # the project, even if the synthesis model returns an otherwise valid draft.
    project_id_2 = db.save_teacher_project({**project_payload(), "project_name": "Review-gated course"})
    project_2 = db.get_teacher_project(project_id_2, "validator")
    assert project_2
    review_result = web_research_engine.ResearchResult(
        report=mock_result.report,
        sources=mock_result.sources[:2],
        queries=mock_result.queries,
        provider="gemini",
        model="gemini-3.6-flash",
        status="needs_review",
        diagnostic="Source diversity requires teacher review.",
        latency_ms=200,
    )
    web_research_engine.run_phase_research = lambda *args, **kwargs: review_result
    content_generation_engine.generate_content = lambda *args, **kwargs: content_generation_engine.ContentGenerationResult(
        response=long_output(),
        provider="mock",
        model="mock-model",
        status="completed",
        latency_ms=300,
    )
    try:
        review_outcome = educational_builder.generate_project_phase(
            project_2,
            "validator",
            phase_number=1,
            research_mode="balanced",
            max_research_sources=8,
            force_research=True,
        )
    finally:
        web_research_engine.run_phase_research = original_research
        content_generation_engine.generate_content = original_generation
    assert review_outcome.status == "needs_review"
    assert review_outcome.next_phase == 1
    project_2_after = db.get_teacher_project(project_id_2, "validator")
    assert int(project_2_after.get("current_phase") or 0) == 1

    ui_text = (ROOT / "teacher_studio.py").read_text(encoding="utf-8")
    assert "Guided web research" in ui_text
    assert "run_project_research" in ui_text
    assert 'st.success(copy["ready"], icon=' not in ui_text

    print("V6.12 research-augmented educational builder validation passed.")


if __name__ == "__main__":
    try:
        main()
    finally:
        try:
            os.unlink(_tmp.name)
        except OSError:
            pass
