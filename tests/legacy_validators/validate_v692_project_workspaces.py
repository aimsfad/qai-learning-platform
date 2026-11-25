"""Validation for V6.9.2 teacher project workspaces and publication."""

from __future__ import annotations

import importlib.util
import py_compile
import sys
import types
from pathlib import Path

from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parent


def assert_contains(path: Path, snippets: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for snippet in snippets:
        assert snippet in text, f"Missing {snippet!r} in {path.name}"


def compile_files() -> None:
    for name in ["app.py", "main_app.py", "db.py", "teacher_studio.py", "i18n.py"]:
        py_compile.compile(str(ROOT / name), doraise=True)


def load_db():
    fake_st = types.ModuleType("streamlit")
    fake_st.secrets = {}

    def cache_resource(*args, **kwargs):
        if args and callable(args[0]) and len(args) == 1 and not kwargs:
            return args[0]
        return lambda fn: fn

    fake_st.cache_resource = cache_resource
    sys.modules["streamlit"] = fake_st
    spec = importlib.util.spec_from_file_location("db_v692_validation", ROOT / "db.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    engine = create_engine("sqlite:///:memory:", future=True)
    module.get_engine = lambda: engine
    module.init_db()
    return module


def validate_database_lifecycle() -> None:
    db = load_db()
    project_id = db.save_teacher_project({
        "teacher_username": "teacher.a",
        "project_name": "Hadamard learning project",
        "domain": "Quantum computing",
        "program_name": "Quantum foundations",
        "unit_title": "Hadamard gate",
        "target_concept": "Balanced superposition",
        "target_learners": "Undergraduate beginners",
        "learner_level": "Beginner",
        "target_languages": ["Arabic", "English"],
        "primary_language": "Arabic",
        "primary_language_code": "ar",
        "platform_components": ["AI Coach", "Assessment"],
        "requested_outputs": ["Interactive lesson", "Video"],
        "current_phase": 3,
    })
    assert db.published_teacher_projects_df().empty
    db.save_teacher_generation(project_id, 3, "prompt", "# Core lesson", "local", "test", "completed", "")
    progress = db.teacher_projects_with_progress_df("teacher.a")
    assert len(progress) == 1
    assert int(progress.iloc[0]["completed_phases"]) == 1
    outputs = db.teacher_project_phase_outputs(project_id)
    assert 3 in outputs and outputs[3]["response_text"] == "# Core lesson"

    db.set_teacher_project_status(project_id, "teacher.a", "review")
    assert db.get_teacher_project(project_id, "teacher.a")["status"] == "review"
    db.set_teacher_project_status(project_id, "teacher.a", "published")
    public = db.published_teacher_projects_df()
    assert len(public) == 1
    assert db.get_published_teacher_project(project_id)["status"] == "published"
    db.set_teacher_project_status(project_id, "teacher.a", "draft")
    assert db.published_teacher_projects_df().empty

    denied = False
    try:
        db.set_teacher_project_status(project_id, "other.teacher", "published")
    except ValueError:
        denied = True
    assert denied, "Project ownership must be enforced"


def validate_ui_contract() -> None:
    assert_contains(ROOT / "teacher_studio.py", [
        "def render_projects_grid",
        "def render_project_workspace",
        "def render_project_student_preview",
        "def render_published_course_catalog",
        "publish_gate",
        "teacher_workspace_section",
    ])
    assert_contains(ROOT / "main_app.py", [
        'elif page == "Published Courses"',
        'teacher_studio.render_published_course_catalog',
        '("Published Courses", "▤"',
    ])
    assert_contains(ROOT / "i18n.py", ['"Published Courses"'])
    assert_contains(ROOT / ".streamlit" / "v6_theme.css", [
        "v692-project-card-marker",
        "v692-course-preview-hero",
        "v692-public-course-marker",
    ])


def main() -> None:
    compile_files()
    validate_ui_contract()
    validate_database_lifecycle()
    print("V6.9.2 project workspaces and publishing validation passed.")


if __name__ == "__main__":
    main()
