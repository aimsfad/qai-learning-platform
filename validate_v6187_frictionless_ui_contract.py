"""Validation for V6.18.7 Frictionless UI Contract."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def source(path: str) -> str:
    text = (ROOT / path).read_text(encoding="utf-8")
    if path.endswith(".py"):
        ast.parse(text, filename=path)
    return text


def validate_researcher_context() -> None:
    design = source("global_design_system.py")
    main = source("main_app.py")
    css = source(".streamlit/v6_theme.css")
    require('"researcher": {"icon": "monitoring"' in design, "researcher visual missing")
    require('global_ui.render_role_marker("researcher" if page in researcher_pages else "evaluator")' in main, "dynamic researcher/evaluator marker missing")
    require("v6186-role-researcher" in css, "researcher scoped CSS missing")


def validate_frictionless_teacher_flow() -> None:
    teacher = source("teacher_studio.py")
    for token in (
        "accessible_ids = {incomplete_id}",
        "only approved lessons and the current lesson",
        "lesson_access",
        "simple_lesson_action_bar_",
        "approve_full_lesson",
    ):
        require(token in teacher, f"teacher flow token missing: {token}")


def validate_accessibility_css() -> None:
    css = source(".streamlit/v6_theme.css")
    for token in (
        "V6.18.7 — Frictionless UI Contract & Accessibility QA",
        'min-height:44px !important',
        'outline:2px solid #2563EB !important',
        'button[role="tab"][aria-selected="true"] *',
        'simple_lesson_action_bar_',
        'simple_preview_',
    ):
        require(token in css, f"CSS contract token missing: {token}")
    # The final layer must explicitly neutralize the old filled selected-tab child color.
    final = css.split("V6.18.7 — Frictionless UI Contract & Accessibility QA", 1)[-1]
    require('color:#0F172A !important' in final, "selected tab child color is not overridden")


def validate_non_destructive_release() -> None:
    db = source("db.py")
    require(any(v in db for v in ('APP_VERSION = "v6.19.0-pedagogical-quality-adaptive-coach"', 'APP_VERSION = "v6.18.9-lesson-identity-content-hygiene"', 'APP_VERSION = "v6.18.8-teacher-workspace-screenshot-polish"', 'APP_VERSION = "v6.18.7-frictionless-ui-contract"')), "app version missing")
    # The release should remain UI-only; engines continue to be validated by previous suites.
    for path in (
        "lesson_block_generation_engine.py",
        "lesson_blueprint_engine.py",
        "pedagogical_orchestrator.py",
        "production_pipeline.py",
        "evidence_synthesis_engine.py",
    ):
        require((ROOT / path).exists(), f"preserved engine missing: {path}")


def main() -> None:
    validate_researcher_context()
    validate_frictionless_teacher_flow()
    validate_accessibility_css()
    validate_non_destructive_release()
    print("V6.18.7 frictionless UI contract validation passed.")


if __name__ == "__main__":
    main()
