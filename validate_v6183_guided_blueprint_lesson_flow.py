"""Behavioral/static validation for V6.18.3."""
from __future__ import annotations

import ast
import importlib
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Static/behavioral validation does not need the Streamlit runtime.
fake_st = types.ModuleType("streamlit")
fake_st.secrets = {
    "ENABLE_LESSON_BLUEPRINT": "true",
    "ENABLE_BLUEPRINT_EDITOR": "true",
    "ENABLE_LESSON_BLOCK_GENERATION": "true",
    "REQUIRE_BLOCK_APPROVAL_FOR_LESSON_COMPLETION": "true",
    "LESSON_BLOCK_REQUIRE_SEQUENCE": "true",
}
fake_st.cache_resource = lambda *args, **kwargs: (lambda fn: fn)
sys.modules["streamlit"] = fake_st

blocks = importlib.import_module("lesson_block_generation_engine")
contracts = importlib.import_module("workflow_runtime_contracts")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_contracts() -> None:
    for scope in ("blueprint", "lesson_blocks"):
        report = contracts.check_contract(scope)
        require(bool(report.get("ok")), f"{scope} contract missing: {report.get('missing')}")


def validate_block_state() -> None:
    original_latest = blocks.db.latest_lesson_blocks_by_type
    original_active = blocks._active_blueprint_run_id
    try:
        blocks._active_blueprint_run_id = lambda project_id: 77
        blocks.db.latest_lesson_blocks_by_type = lambda project_id, lesson_id, **kwargs: {
            "activation": {
                "id": 11,
                "block_type": "activation",
                "approved_by_teacher": 1,
                "status": "completed",
                "version_number": 1,
                "word_count": 80,
            },
            "explanation": {
                "id": 12,
                "block_type": "explanation",
                "approved_by_teacher": 0,
                "status": "needs_review",
                "version_number": 1,
                "word_count": 240,
            },
        }
        rows = blocks.lesson_block_state(1, "L1", "en")
        require(len(rows) == len(blocks.BLOCK_SPECS), "all canonical blocks must be represented")
        require(rows[0]["state"] == "approved", "first block should be approved")
        require(rows[1]["state"] == "needs_review", "generated block should require review")
        require(rows[2]["locked"] is True, "later blocks should wait for approval")
        require(blocks.next_incomplete_block(1, "L1") == "explanation", "next block mismatch")
        require(blocks.can_generate_block(1, "L1", "explanation")["allowed"], "existing revision must remain editable")
        require(not blocks.can_generate_block(1, "L1", "worked_example")["allowed"], "future block should be locked")
        completion = blocks.lesson_completion(1, "L1")
        require(completion["approved"] == 1 and completion["available"] == 2, "completion aggregation mismatch")
    finally:
        blocks.db.latest_lesson_blocks_by_type = original_latest
        blocks._active_blueprint_run_id = original_active


def validate_teacher_ui_source() -> None:
    source = (ROOT / "teacher_studio.py").read_text(encoding="utf-8")
    require("import workflow_runtime_contracts" in source, "runtime contracts are not wired into teacher UI")
    require("_render_blueprint_stage_flow" in source, "blueprint stage flow missing")
    require("_render_lesson_block_map" in source, "lesson block map missing")
    require("approve_blueprint_top_" in source, "prominent blueprint approval action missing")
    require("block_pending_type_" in source, "automatic next-block navigation missing")
    secrets = (ROOT / ".streamlit" / "secrets_example.toml").read_text(encoding="utf-8")
    require("LESSON_BLOCK_REQUIRE_SEQUENCE" in secrets, "sequence secret example missing")
    ast.parse(source)


def validate_css() -> None:
    css = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")
    for token in (".v6183-stage-flow", ".v6183-block-grid", ".v6183-block-approved", ".v6183-block-locked"):
        require(token in css, f"missing CSS token: {token}")


def main() -> None:
    validate_contracts()
    validate_block_state()
    validate_teacher_ui_source()
    validate_css()
    print("V6.18.3 guided blueprint and lesson production validation passed.")


if __name__ == "__main__":
    main()
