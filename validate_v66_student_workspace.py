from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main_app.py"
CSS = ROOT / ".streamlit" / "v6_theme.css"
DB = ROOT / "db.py"
ASSET = ROOT / "assets" / "branding" / "v66_student_workspace_cover.png"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    main_text = MAIN.read_text(encoding="utf-8")
    css_text = CSS.read_text(encoding="utf-8")
    db_text = DB.read_text(encoding="utf-8")

    ast.parse(main_text)
    ast.parse(DB.read_text(encoding="utf-8"))

    required_python = [
        "def student_workspace_copy()",
        "def render_v66_stage_header(",
        "def render_v66_ai_coach(",
        "def render_v66_lesson_content(",
        "v66_attempt_",
        "v66_compact_coach",
        "with st.expander(",
        "learning_col, coach_col = st.columns([1.58, .92]",
        "render_ai_usefulness_feedback",
        "db.save_lesson_progress",
    ]
    for token in required_python:
        require(token in main_text, f"Missing V6.6 Python feature: {token}")

    required_css = [
        ".v66-stage-header",
        ".v66-panel-heading",
        ".v66-concept-hero",
        ".v66-ai-policy",
        ".v66-reflection-marker",
        "@media (max-width: 720px)",
        "@media (prefers-color-scheme: dark)",
    ]
    for token in required_css:
        require(token in css_text, f"Missing V6.6 CSS feature: {token}")

    require('APP_VERSION = "v6.6-student-learning-workspace"' in db_text, "App version was not updated")
    require(ASSET.exists() and ASSET.stat().st_size > 100_000, "Student workspace cover is missing or empty")

    # The old seven-tab module shell must no longer be the active module implementation.
    require(main_text.count("def render_learning_module(student: Dict[str, Any]) -> None:") == 1, "Unexpected duplicate learning module renderer")

    print("V6.6 student learning workspace validation passed.")


if __name__ == "__main__":
    main()
