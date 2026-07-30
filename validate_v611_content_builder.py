"""Isolated behavioral validation for V6.11 educational content builder."""

from __future__ import annotations

import importlib
import os
import sys
import tempfile
import types
from pathlib import Path

_tmp = tempfile.NamedTemporaryFile(prefix="qai_v611_", suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

fake_st = types.ModuleType("streamlit")
fake_st.secrets = {}
fake_st.cache_resource = lambda *args, **kwargs: (lambda fn: fn)
sys.modules["streamlit"] = fake_st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

content_generation_engine = importlib.import_module("content_generation_engine")
db = importlib.import_module("db")
educational_builder = importlib.import_module("educational_builder")


def project_payload() -> dict:
    return {
        "teacher_username": "validator",
        "project_name": "Python course",
        "domain": "Programming",
        "program_name": "Python foundations",
        "unit_title": "Variables and data types",
        "target_concept": "Understand Python variables and basic types",
        "target_learners": "Secondary-school beginners",
        "learner_level": "Beginner",
        "prerequisites": "Basic computer use",
        "target_languages": ["Arabic", "French", "English"],
        "primary_language": "Arabic",
        "primary_language_code": "ar",
        "expected_duration": "45 minutes",
        "technical_environment": "Streamlit and Python",
        "platform_components": ["AI Coach", "Assessment"],
        "source_material": "Teacher-authored source notes.",
        "teaching_preferences": "Attempt first, then progressive hints.",
        "assessment_preferences": "Formative questions and a small task.",
        "additional_notes": "",
        "requested_outputs": ["Interactive lesson", "Assessment bank"],
        "current_phase": 1,
        "status": "draft",
    }


def long_output(label: str) -> str:
    blocks = [f"# {label}"]
    for i in range(1, 18):
        blocks.append(f"## Section {i}\n- Educational item {i}. " + ("Validated learning content. " * 8))
    blocks.append("## Generation checks\n- Evidence gaps: none in supplied notes.\n- Teacher approval required.")
    return "\n\n".join(blocks)


def main() -> None:
    db.init_db()
    project_id = db.save_teacher_project(project_payload())
    project = db.get_teacher_project(project_id, "validator")
    assert project

    prompt1 = educational_builder.compile_project_prompt(project, 1)
    assert "# Phase 1" in prompt1
    assert "# Phase 2" not in prompt1
    assert "<teacher_project_brief>" in prompt1

    db.save_teacher_generation(project_id, 1, prompt1, long_output("Evidence audit"), "test", "mock", "completed")
    db.save_teacher_generation(project_id, 1, prompt1, "Generation failed", "test", "mock", "error")
    preferred = db.teacher_project_phase_outputs(project_id)
    assert preferred[1]["status"] == "completed", "A failed retry must not erase completed progress"
    latest = db.teacher_project_phase_outputs(project_id, prefer_completed=False)
    assert latest[1]["status"] == "error"

    db.set_teacher_project_phase(project_id, "validator", 2)
    project = db.get_teacher_project(project_id, "validator")
    assert project and int(project["current_phase"]) == 2
    prompt2 = educational_builder.compile_project_prompt(project, 2)
    assert "# Phase 2" in prompt2
    assert "# Phase 3" not in prompt2
    assert "Accepted context from previously completed phases" in prompt2
    assert "Evidence audit" in prompt2

    original = content_generation_engine.generate_content
    content_generation_engine.generate_content = lambda *args, **kwargs: content_generation_engine.ContentGenerationResult(
        response=long_output("Learning design blueprint"),
        provider="mock",
        model="mock-model",
        status="completed",
        latency_ms=321,
    )
    try:
        outcome = educational_builder.generate_project_phase(project, "validator", phase_number=2)
    finally:
        content_generation_engine.generate_content = original

    assert outcome.status == "completed"
    assert outcome.next_phase == 3
    refreshed = db.get_teacher_project(project_id, "validator")
    assert refreshed and int(refreshed["current_phase"]) == 3
    run = db.latest_teacher_generation(project_id)
    assert run and run["status"] == "completed"
    assert int(run["latency_ms"]) == 321
    assert run["validation_status"] == "passed"

    revision_id = db.save_teacher_manual_revision(
        project_id,
        "validator",
        2,
        long_output("Teacher-reviewed learning design"),
        source_run_id=int(run["id"]),
    )
    revision = db.latest_teacher_generation(project_id)
    assert revision and int(revision["id"]) == revision_id
    assert revision["provider"] == "teacher"
    assert revision["validation_status"] == "teacher_approved"

    print("V6.11 educational content builder validation passed.")


if __name__ == "__main__":
    try:
        main()
    finally:
        Path(_tmp.name).unlink(missing_ok=True)
