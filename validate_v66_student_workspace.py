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
        "v66_compact_coach",
        "with st.expander(",
        "render_ai_usefulness_feedback",
        "db.save_lesson_progress",
    ]
    for token in required_python:
        require(token in main_text, f"Missing V6.6 Python feature: {token}")
    require("v66_attempt_" in main_text or "attempt_gate.build_attempt_key" in main_text, "Missing learner attempt state key")

    require(
        "learning_col, coach_col = st.columns([1.58, .92]" in main_text
        or "learning_col, coach_col = st.columns([3, 2]" in main_text,
        "Missing V6.6+ learner/coach split",
    )

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

    require(any(v in db_text for v in ('APP_VERSION = "v6.6-student-learning-workspace"', 'APP_VERSION = "v6.7-home-hero-student-tools"', 'APP_VERSION = "v6.8-student-command-workspace"', 'APP_VERSION = "v6.8.1-student-ux-hotfix"', 'APP_VERSION = "v6.8.2-attempt-first-gate"')), "App version is not compatible with the V6.6+ student workspace")
    require(ASSET.exists() and ASSET.stat().st_size > 100_000, "Student workspace cover is missing or empty")

    # The old seven-tab module shell must no longer be the active module implementation.
    require(main_text.count("def render_learning_module(student: Dict[str, Any]) -> None:") == 1, "Unexpected duplicate learning module renderer")

    print("V6.6 student learning workspace validation passed.")


if __name__ == "__main__":
    main()
