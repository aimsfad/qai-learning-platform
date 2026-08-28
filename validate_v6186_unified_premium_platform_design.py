"""Validation for V6.18.6 unified premium platform design integration.

The release is intentionally frontend-first: it must preserve the existing
student, teacher, evaluator, research, generation, and database logic while
adding a shared visual shell and role-scoped layout polish.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def parse_python(path: str) -> str:
    source = (ROOT / path).read_text(encoding="utf-8")
    ast.parse(source, filename=path)
    return source


def validate_design_system() -> None:
    source = parse_python("global_design_system.py")
    for token in (
        "ROLE_VISUALS",
        "def render_role_marker",
        "def status_badge_html",
        'role: str = ""',
        "v618-role-header-",
        '"family": "Tajawal, Arial, sans-serif"',
    ):
        require(token in source, f"missing global design-system token: {token}")


def validate_role_integration() -> None:
    main = parse_python("main_app.py")
    teacher = parse_python("teacher_studio.py")
    app = parse_python("app.py")

    require('render_role_marker("student")' in main, "student role marker missing")
    require('render_role_marker("evaluator")' in main, "evaluator role marker missing")
    require('render_role_marker("teacher")' in teacher, "teacher role marker missing")
    require("v6186-role-public" in app, "public role marker missing")
    require("v6186-simple-journey-marker" in teacher, "five-step teacher journey marker missing")
    require("v6186-evaluator-review-shell" in main, "evaluator side-by-side review shell missing")
    require("v6186_eval_response_" in main and "v6186_eval_rubric_" in main, "evaluator response/rubric containers missing")


def validate_css() -> None:
    css = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")
    for token in (
        "V6.18.6 — Unified Premium Platform Design Integration",
        "--v618-midnight:#0F172A",
        "--v618-blue:#1D4ED8",
        "--v618-bg:#F8FAFC",
        "--v618-green:#10B981",
        "font-family:\"Tajawal\"",
        "v6186-status-badge",
        "v6186-simple-journey-marker",
        "v6186-role-student",
        "v6186-role-evaluator",
        "prefers-reduced-motion",
        "focus-visible",
    ):
        require(token in css, f"missing CSS token: {token}")


def validate_non_destructive_contract() -> None:
    db = parse_python("db.py")
    require(
        any(v in db for v in (
            'APP_VERSION = "v6.20.0-published-course-runtime"', 'APP_VERSION = "v6.19.1-learner-evidence-misconception-tracing"', 'APP_VERSION = "v6.19.0-pedagogical-quality-adaptive-coach"', 'APP_VERSION = "v6.18.9-lesson-identity-content-hygiene"', 'APP_VERSION = "v6.18.8-teacher-workspace-screenshot-polish"', 'APP_VERSION = "v6.18.7-frictionless-ui-contract"',
            'APP_VERSION = "v6.18.6-unified-premium-platform-design"',
        )),
        "application version was not updated",
    )
    # This release must not add a schema migration or replace generation engines.
    changed_files = {
        "app.py",
        "main_app.py",
        "teacher_studio.py",
        "global_design_system.py",
        "db.py",
        ".streamlit/v6_theme.css",
    }
    require("lesson_block_generation_engine.py" not in changed_files, "lesson generation engine must remain untouched")
    require("lesson_blueprint_engine.py" not in changed_files, "blueprint engine must remain untouched")
    require("production_pipeline.py" not in changed_files, "production pipeline must remain untouched")


def main() -> None:
    validate_design_system()
    validate_role_integration()
    validate_css()
    validate_non_destructive_contract()
    print("V6.18.6 unified premium platform design validation passed.")


if __name__ == "__main__":
    main()
