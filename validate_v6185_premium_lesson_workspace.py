"""Validation for V6.18.5 Premium Lesson Workspace & Pedagogical Orchestrator."""
from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

fake_st = types.ModuleType("streamlit")
fake_st.secrets = {
    "ENABLE_LESSON_BLOCK_GENERATION": "true",
    "LESSON_BLOCK_REQUIRE_SEQUENCE": "true",
}
fake_st.cache_resource = lambda *args, **kwargs: (lambda fn: fn)
sys.modules["streamlit"] = fake_st

renderer = importlib.import_module("lesson_content_renderer")
pedagogy = importlib.import_module("pedagogical_orchestrator")
blocks = importlib.import_module("lesson_block_generation_engine")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_renderer() -> None:
    raw = """## مثال محلول (Worked example)\n\n**المتطلب:** None\n\n### Attempt\nجرّب أولًا.\n\n```python\nx = None\nprint(x)\n```\n\n### Teacher implementation note\nراقب التفكير.\n"""
    cleaned = renderer.normalize_generated_markdown(raw, "ar")
    require("Worked example" not in cleaned, "duplicated English heading was not removed")
    require("Teacher implementation note" not in cleaned, "teacher heading was not localized")
    require("**المتطلب:** None" not in cleaned, "placeholder line was not removed")
    require("x = None" in cleaned, "None inside code must be preserved")
    require(not renderer.markdown_has_unclosed_fence(cleaned), "cleaned Markdown has an unclosed fence")
    require(renderer.content_has_placeholder("**النوع:** None"), "placeholder detection failed")


def validate_pedagogy_contract() -> None:
    contract = pedagogy.prompt_contract("worked_example", "Arabic")
    for token in ("attempt-first", "graduated hints", "pedagogical co-designer", "teacher remains"):
        require(token.lower() in contract.lower(), f"missing pedagogical contract token: {token}")
    principles = [item["key"] for item in pedagogy.principles_for_block("formative_assessment")]
    require("formative_feedback" in principles, "formative assessment must include feedback principle")
    require("retrieval" in principles, "formative assessment should retrieve learning evidence")


def validate_block_validation() -> None:
    good = """## جرّب أولًا\nما الناتج؟\n\n## تلميحات\nابدأ بالسطر الأول.\n\n## الحل النموذجي\n```python\nprint('ok')\n```\n\n## تحقق ذاتي\nغيّر القيمة وتوقع الناتج.\n"""
    report = blocks.validate_block_content("worked_example", good, [])
    require("worked_example_missing_attempt" not in report["warnings"], "attempt-first signal not detected")
    require("worked_example_missing_hints" not in report["warnings"], "hints not detected")
    require("worked_example_missing_solution" not in report["warnings"], "solution not detected")
    require("pedagogical_principles" in report, "pedagogical metadata missing")

    broken = "## عنوان\n\n```python\nprint('x')\n"
    report = blocks.validate_block_content("explanation", broken, [])
    require("unclosed_code_fence" in report["errors"], "unclosed code fence must block approval")


def validate_ui_static() -> None:
    source = (ROOT / "teacher_studio.py").read_text(encoding="utf-8")
    css = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")
    db_source = (ROOT / "db.py").read_text(encoding="utf-8")
    for token in (
        "import pedagogical_orchestrator",
        "import lesson_content_renderer",
        "lesson_quality_snapshot",
        "normalize_generated_markdown",
        "v6185-lesson-hero",
        "v6185-section-purpose",
    ):
        require(token in source or token in css, f"missing UI token: {token}")
    require(any(v in db_source for v in ('APP_VERSION = "v6.18.7-frictionless-ui-contract"', 'APP_VERSION = "v6.18.6-unified-premium-platform-design"', 'APP_VERSION = "v6.18.5-premium-lesson-workspace"')), "app version was not updated")


def main() -> None:
    validate_renderer()
    validate_pedagogy_contract()
    validate_block_validation()
    validate_ui_static()
    print("V6.18.5 premium lesson workspace validation passed.")


if __name__ == "__main__":
    main()
