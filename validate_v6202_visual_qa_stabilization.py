from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    config = (ROOT / "config.py").read_text(encoding="utf-8")
    app = (ROOT / "app.py").read_text(encoding="utf-8")
    teacher = (ROOT / "teacher_studio.py").read_text(encoding="utf-8")
    main_app = (ROOT / "main_app.py").read_text(encoding="utf-8")
    css_path = ROOT / ".streamlit" / "v6202_visual_qa_stabilization.css"
    css = css_path.read_text(encoding="utf-8")

    for path in (ROOT / "config.py", ROOT / "app.py", ROOT / "teacher_studio.py", ROOT / "main_app.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    require(css_path.exists() and css_path.stat().st_size > 6000, "V6.20.2 visual QA stylesheet is missing or too small.")
    require("V6202_STYLE_PATH" in config and "v6202_visual_qa_stabilization.css" in config, "Final V6.20.2 style layer is not registered.")
    require("V6201_STYLE_PATH, V6202_STYLE_PATH" in config, "V6.20.2 is not loaded after V6.20.1.")
    require(":material/smart_toy:" in app and "icon=icon" in app, "Learner tool dock does not use native Material icons.")
    require("[0.55, 2.3, 0.55]" in teacher, "Single-project workspace card was not widened.")
    require("def _strip_redundant_section_heading" in teacher, "Duplicate generated section heading guard is missing.")
    require("compact=True" in main_app.split("def render_ai_tutor_lab", 1)[1].split("def ", 1)[0], "AI Tutor hero is not compact.")
    for token in (
        ".v65-program-card",
        ".st-key-v67_student_tool_dock",
        ".v618-page-header-compact",
        "@media (min-width: 1181px) and (max-width: 1440px)",
        "@media (max-width: 700px)",
    ):
        require(token in css, f"Expected visual QA rule missing: {token}")

    print("V6.20.2 screenshot-driven visual QA stabilization validation passed.")


if __name__ == "__main__":
    main()
