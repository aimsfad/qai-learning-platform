"""Validation for V6.9.3 teacher save and prompt hotfix."""
from __future__ import annotations

import importlib.util
import json
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
    for name in ["app.py", "main_app.py", "db.py", "teacher_studio.py", "content_generation_engine.py"]:
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
    spec = importlib.util.spec_from_file_location("db_v693_validation", ROOT / "db.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    engine = create_engine("sqlite:///:memory:", future=True)
    module.get_engine = lambda: engine
    module.init_db()
    return module


def validate_save_and_canonical_prompt() -> None:
    db = load_db()
    project_id = db.save_teacher_project({
        "teacher_username": "teacher.hotfix",
        "project_name": "Reliable save",
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
        "current_phase": 1,
    })
    saved = db.get_teacher_project(project_id, "teacher.hotfix")
    assert saved and saved["project_name"] == "Reliable save"
    assert json.loads(saved["target_languages_json"]) == ["Arabic", "English"]

    template = (ROOT / "prompts" / "educational_content_production_master.md").read_text(encoding="utf-8")
    brief = f"- Project name: {saved['project_name']}\n- Unit title: {saved['unit_title']}"
    prompt = (
        template.replace("{{TEACHER_PROJECT_BRIEF}}", brief)
        .replace("{{PHASE_NUMBER}}", "1")
        .replace("{{PHASE_NAME}}", "Evidence and concept audit")
        .replace("{{OUTPUT_LANGUAGE}}", "Arabic")
    )
    assert "Reliable save" in prompt
    assert "Hadamard gate" in prompt
    assert "{{" not in prompt


def validate_ui_contract() -> None:
    assert_contains(ROOT / "teacher_studio.py", [
        "def save_project_and_prepare_prompt",
        "saved = db.get_teacher_project",
        'st.session_state.teacher_workspace_section_pending = "production"',
        "st.session_state.teacher_expand_prompt = True",
        "teacher_flash_success",
        'u["rebuild_prompt"]',
        "clear_on_submit=False",
        "teacher_content_project_form_{form_scope}",
        "save_error",
    ])
    db_text = (ROOT / "db.py").read_text(encoding="utf-8")
    assert any(v in db_text for v in ('APP_VERSION = "v6.9.3-save-prompt-hotfix"', 'APP_VERSION = "v6.9.4-premium-logo-prompt-state"', 'APP_VERSION = "v6.10-gemini-file-analyzer-router"'))


def main() -> None:
    compile_files()
    validate_ui_contract()
    validate_save_and_canonical_prompt()
    print("V6.9.3 save and prompt hotfix validation passed.")


if __name__ == "__main__":
    main()
