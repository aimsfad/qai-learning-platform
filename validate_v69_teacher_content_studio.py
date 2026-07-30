from __future__ import annotations

import importlib.util
import py_compile
import sys
import tempfile
import types
from pathlib import Path

from sqlalchemy import create_engine


ROOT = Path(__file__).resolve().parent


def assert_contains(path: Path, snippets: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for snippet in snippets:
        assert snippet in text, f"Missing {snippet!r} in {path.name}"


def compile_files() -> None:
    for name in [
        "app.py",
        "main_app.py",
        "db.py",
        "teacher_studio.py",
        "content_generation_engine.py",
        "ui_v6.py",
    ]:
        py_compile.compile(str(ROOT / name), doraise=True)


def validate_prompt() -> None:
    prompt = ROOT / "prompts" / "educational_content_production_master.md"
    assert prompt.exists(), "Master prompt is missing"
    text = prompt.read_text(encoding="utf-8")
    assert "{{TEACHER_PROJECT_BRIEF}}" in text
    assert "{{PHASE_NUMBER}}" in text
    assert "{{PHASE_NAME}}" in text
    assert "{{OUTPUT_LANGUAGE}}" in text
    for phase in range(1, 12):
        assert f"Phase {phase}" in text
    compiled = (
        text.replace("{{TEACHER_PROJECT_BRIEF}}", "- Subject: Quantum computing")
        .replace("{{PHASE_NUMBER}}", "1")
        .replace("{{PHASE_NAME}}", "Evidence and concept audit")
        .replace("{{OUTPUT_LANGUAGE}}", "Arabic")
    )
    assert "{{" not in compiled


def validate_routing_and_ui() -> None:
    assert_contains(ROOT / "app.py", [
        "import teacher_studio",
        'router.route_key("public", "teacher")',
        'router.route_key("teacher", "Content Studio")',
        'role == "teacher"',
    ])
    assert_contains(ROOT / "ui_v6.py", [
        '"teacher": "دخول الأستاذ"',
        'router.route_key("public", "teacher")',
    ])
    assert_contains(ROOT / "main_app.py", [
        '"teacher_logged_in": False',
        'elif role == "teacher"',
    ])
    assert_contains(ROOT / "teacher_studio.py", [
        "def compile_project_prompt",
        "def render_teacher_app",
        "def extract_uploaded_sources",
        "educational_builder.generate_project_phase",
    ])


def validate_database() -> None:
    fake_st = types.ModuleType("streamlit")
    fake_st.secrets = {}
    fake_st.cache_resource = lambda *args, **kwargs: (lambda fn: fn)
    sys.modules.setdefault("streamlit", fake_st)
    sys.path.insert(0, str(ROOT))

    spec = importlib.util.spec_from_file_location("db_v69_validation", ROOT / "db.py")
    assert spec and spec.loader
    db = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(db)

    engine = create_engine("sqlite:///:memory:", future=True)
    db.get_engine = lambda: engine
    db.init_db()

    project_id = db.save_teacher_project({
        "teacher_username": "teacher",
        "project_name": "Hadamard unit",
        "domain": "Quantum computing",
        "program_name": "Introductory quantum programming",
        "unit_title": "Hadamard gate",
        "target_concept": "Balanced superposition",
        "target_learners": "Undergraduate beginners",
        "learner_level": "Beginner",
        "target_languages": ["Arabic", "English"],
        "primary_language": "Arabic",
        "primary_language_code": "ar",
        "platform_components": ["AI Coach", "Assessment"],
        "requested_outputs": ["Interactive lesson", "Video"],
        "current_phase": 1,
    })
    assert project_id > 0
    project = db.get_teacher_project(project_id, "teacher")
    assert project and project["unit_title"] == "Hadamard gate"
    run_id = db.save_teacher_generation(
        project_id, 1, "prompt", "response", "local", "test", "completed", ""
    )
    assert run_id > 0
    assert len(db.teacher_projects_df("teacher")) == 1
    assert len(db.teacher_generation_runs_df(project_id)) == 1


def main() -> None:
    compile_files()
    validate_prompt()
    validate_routing_and_ui()
    validate_database()
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "pypdf" in requirements and "python-docx" in requirements
    print("V6.9 teacher content studio validation passed.")


if __name__ == "__main__":
    main()
