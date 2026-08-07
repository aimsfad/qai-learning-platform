from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def parse(name: str) -> ast.AST:
    return ast.parse(read(name), filename=name)


def main() -> None:
    required = [
        "global_design_system.py",
        "main_app.py",
        "teacher_studio.py",
        "ui_v6.py",
        ".streamlit/v6_theme.css",
        "V6_18_GLOBAL_PROFESSIONAL_DESIGN_SYSTEM_AR.md",
    ]
    for name in required:
        assert (ROOT / name).exists(), f"Missing {name}"

    for name in ["global_design_system.py", "main_app.py", "teacher_studio.py", "ui_v6.py", "db.py"]:
        parse(name)

    design = read("global_design_system.py")
    for token in [
        "def render_page_header",
        "def render_section_header",
        "def render_kpi_card",
        "def apply_plotly_theme",
        "def render_inline_notice",
    ]:
        assert token in design, token

    main_app = read("main_app.py")
    assert "import global_design_system as global_ui" in main_app
    assert "v618_student_auth_card" in main_app
    assert "v618_evaluator_auth_card" in main_app
    assert "global_ui.render_kpi_card" in main_app
    assert "global_ui.apply_plotly_theme" in main_app

    teacher = read("teacher_studio.py")
    assert "import global_design_system as global_ui" in teacher
    assert "v618-teacher-shell-marker" in teacher
    assert "v618-project-card-marker" in teacher

    public = read("ui_v6.py")
    assert "v618-public-shell-marker" in public

    css = read(".streamlit/v6_theme.css")
    for token in [
        "3alimnIA V6.18 — Global Professional Design System",
        ".v618-page-header",
        ".v618-kpi-card",
        ".v618-action-card",
        ".v618-auth-marker",
        "button[role=\"tab\"][aria-selected=\"true\"]",
        ".st-key-v61_public_header",
    ]:
        assert token in css, token

    combined = main_app + teacher + public
    assert 'vertical_alignment="stretch"' not in combined
    assert any(v in read("db.py") for v in (
        'APP_VERSION = "v6.18-global-professional-design-system"',
        'APP_VERSION = "v6.18.2-blueprint-editor-runtime-and-ui-polish"',
        'APP_VERSION = "v6.18.5-premium-lesson-workspace"', 'APP_VERSION = "v6.18.4-simple-teacher-journey"', 'APP_VERSION = "v6.18.3-guided-blueprint-lesson-production"',
    ))
    print("V6.18 global professional design-system validation passed.")


if __name__ == "__main__":
    main()
