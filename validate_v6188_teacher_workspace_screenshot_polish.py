"""Validation for V6.18.8 Teacher Workspace Screenshot QA & Clarity Polish."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

ROOT = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def read(path: str) -> str:
    text = (ROOT / path).read_text(encoding="utf-8")
    if path.endswith(".py"):
        ast.parse(text, filename=path)
    return text


def load_teacher_display_helpers() -> Dict[str, Any]:
    source = read("teacher_studio.py")
    tree = ast.parse(source, filename="teacher_studio.py")
    wanted = {
        "_localized_level_text",
        "_localized_duration_text",
        "_clean_lesson_display_title",
        "_lesson_position_text",
    }
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in wanted]
    require({node.name for node in nodes} == wanted, "teacher display helper functions are incomplete")
    module = ast.Module(body=nodes, type_ignores=[])
    identity_spec = importlib.util.spec_from_file_location("lesson_identity_v6188", ROOT / "lesson_identity.py")
    require(identity_spec is not None and identity_spec.loader is not None, "lesson identity import spec failed")
    identity = importlib.util.module_from_spec(identity_spec)
    identity_spec.loader.exec_module(identity)
    ns: Dict[str, Any] = {
        "re": re,
        "Any": Any,
        "Dict": Dict,
        "List": List,
        "Optional": Optional,
        "Sequence": Sequence,
        "lesson_identity": identity,
        "_PLACEHOLDER_TEXT": {"", "none", "null", "undefined", "untitled", "n/a", "na", "-", "—"},
    }
    exec(compile(module, "teacher_display_helpers", "exec"), ns)
    return ns


def validate_live_screenshot_fixes() -> None:
    ns = load_teacher_display_helpers()
    require(ns["_localized_level_text"]("Beginner", "ar") == "مبتدئ", "Arabic learner-level localization failed")
    require(ns["_localized_duration_text"]("300 minutes", "ar") == "300 دقيقة", "Arabic duration localization failed")
    require(ns["_localized_duration_text"]("2 hours", "fr") == "2 h", "French duration localization failed")
    require(ns["_lesson_position_text"](2, 4, "ar") == "الدرس 2 من 4", "Arabic lesson position copy failed")

    cleaned = ns["_clean_lesson_display_title"](
        "درس 2: البرمجة و Untitled",
        index=2,
        lang="ar",
        lesson={"lesson_id": "L2", "concept_ids": []},
        blueprint={},
    )
    require(cleaned == "درس 2: البرمجة", f"placeholder leaked into visible lesson title: {cleaned!r}")

    fallback = ns["_clean_lesson_display_title"](
        "Untitled",
        index=3,
        lang="ar",
        lesson={"lesson_id": "L3", "concept_ids": ["C2"]},
        blueprint={"concepts": [{"concept_id": "C2", "name": "الحلقات"}]},
    )
    require(fallback in {"الدرس 3: الحلقات", "درس 3: الحلقات"}, f"concept fallback failed: {fallback!r}")


def validate_renderer_and_css() -> None:
    spec = importlib.util.spec_from_file_location("lesson_content_renderer_v6188", ROOT / "lesson_content_renderer.py")
    require(spec is not None and spec.loader is not None, "renderer import spec failed")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    html = module.lesson_section_nav_html([
        {"index": 1, "label": "تنشيط المعارف السابقة", "run": True, "approved": True},
    ], "ar")
    require("title='تنشيط المعارف السابقة'" in html, "section chip tooltip missing")
    require("aria-label='01 تنشيط المعارف السابقة'" in html, "section chip accessibility label missing")

    css = read(".streamlit/v6_theme.css")
    final = css.split("V6.18.8 — Teacher Workspace Screenshot QA & Clarity Polish", 1)[-1]
    for token in (
        ".st-key-v6163_project_header",
        "gap:.48rem !important",
        "v6184-current-step",
        "simple_lesson_action_bar_",
        'data-stale="true"',
        "opacity:.72 !important",
    ):
        require(token in final, f"V6.18.8 CSS token missing: {token}")


def validate_non_destructive_integration() -> None:
    db = read("db.py")
    is_v6190 = 'APP_VERSION = "v6.19.0-pedagogical-quality-adaptive-coach"' in db
    is_v6189 = 'APP_VERSION = "v6.18.9-lesson-identity-content-hygiene"' in db
    require(
        is_v6190 or is_v6189 or 'APP_VERSION = "v6.18.8-teacher-workspace-screenshot-polish"' in db,
        "V6.18.8+ app version missing",
    )

    # V6.18.8 itself was UI-only and protected these hashes. V6.18.9 is an
    # intentional follow-up that changes evidence/blueprint/block boundaries
    # to fix source-title contamination while retaining the established files.
    if is_v6190 or is_v6189:
        for path in (
            "lesson_block_generation_engine.py",
            "lesson_blueprint_engine.py",
            "pedagogical_orchestrator.py",
            "production_pipeline.py",
            "evidence_synthesis_engine.py",
            "web_research_engine.py",
            "content_generation_engine.py",
        ):
            require((ROOT / path).exists(), f"preserved engine missing: {path}")
        return

    expected = {
        "lesson_block_generation_engine.py": "6b9cfe82afef0eaeb87183137b449e505bdbde9ca4c825c2619749fca5493998",
        "lesson_blueprint_engine.py": "a0548faa9ab7f46d3639e5c277082be2f8b03735bc8b0052c2cb9901ff879cbf",
        "pedagogical_orchestrator.py": "5d758b14fe3b6364d9b7c18aab64a8ecc14bdc825c8bfb0951e826e41293aead",
        "production_pipeline.py": "d2794241361d3942a63fd4487b6a9816d360332f01ae76b582ecc66e69a731c5",
        "evidence_synthesis_engine.py": "21c019d6b431d65c8a366733e3dbb08d55b26180abe3e14e7fd50981cf8e7dc6",
        "web_research_engine.py": "4ef47ae1fe2ca5eef30ad04865d5908cf0c964d87484b7042acf993b82a4e581",
        "content_generation_engine.py": "e50d12e29a5376a22dd91ccc7b661048ddf133be3319115bbbf5f3d421f3eb78",
    }
    for path, digest in expected.items():
        actual = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        require(actual == digest, f"protected engine changed unexpectedly: {path}")


def main() -> None:
    validate_live_screenshot_fixes()
    validate_renderer_and_css()
    validate_non_destructive_integration()
    print("V6.18.8 teacher workspace screenshot polish validation passed.")


if __name__ == "__main__":
    main()
