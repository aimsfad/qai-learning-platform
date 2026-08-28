"""Behavioral and static validation for V6.18.4 Simple Teacher Journey."""
from __future__ import annotations

import inspect
import importlib
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

fake_st = types.ModuleType("streamlit")
fake_st.secrets = {"ENABLE_LESSON_BLOCK_GENERATION": "true", "LESSON_BLOCK_REQUIRE_SEQUENCE": "true"}
fake_st.cache_resource = lambda *args, **kwargs: (lambda fn: fn)
sys.modules["streamlit"] = fake_st

blocks = importlib.import_module("lesson_block_generation_engine")
journey = importlib.import_module("simple_teacher_journey")


def validate_simple_state() -> None:
    assert len(journey.SIMPLE_STEPS) == 5
    base = {
        "statuses": {
            "setup": "completed",
            "resources": "completed",
            "evidence": "review",
            "blueprint": "locked",
            "lessons": "locked",
            "quality": "locked",
            "publish": "locked",
        },
        "lesson_progress": {"required": 0, "approved": 0},
    }
    state = journey.build_simple_state(base)
    assert state["current_key"] == "sources"
    assert state["statuses"]["sources"] == "review"
    assert state["total_steps"] == 5
    assert journey.source_substep(base) == "evidence"

    complete = {
        "statuses": {
            "setup": "completed", "resources": "completed", "evidence": "completed",
            "blueprint": "completed", "lessons": "completed", "quality": "completed", "publish": "available",
        }
    }
    state = journey.build_simple_state(complete)
    assert state["current_key"] == "review"
    assert state["completed_count"] == 4


def validate_lesson_batch_contract() -> None:
    signature = inspect.signature(blocks.generate_and_persist)
    assert "context_blocks" in signature.parameters
    assert callable(blocks.generate_full_lesson)
    assert callable(blocks.approve_full_lesson)
    assert callable(blocks.assembled_lesson)

    original_status = blocks.block_generation_status
    original_latest_approved = blocks.db.latest_approved_lesson_blocks
    original_latest = blocks.db.latest_teacher_lesson_block
    original_generate = blocks.generate_and_persist
    original_state = blocks.lesson_block_state
    original_approve = blocks.db.approve_teacher_lesson_block
    original_completion = blocks.lesson_completion
    original_quality = blocks.lesson_quality_snapshot
    original_active = blocks._active_blueprint_run_id
    try:
        stored = {}
        blocks.block_generation_status = lambda: {"enabled": True, "require_approval": True, "require_sequence": True}
        blocks._active_blueprint_run_id = lambda project_id: 3
        blocks.db.latest_approved_lesson_blocks = lambda project_id, lesson_id, **kwargs: []
        blocks.db.latest_teacher_lesson_block = lambda project_id, lesson_id, block_type, approved_only=False, **kwargs: stored.get(block_type)

        def fake_generate(project, teacher_username, blueprint_bundle, lesson_id, block_type, *, context_blocks=None):
            run = {"id": len(stored) + 1, "project_id": project["id"], "lesson_id": lesson_id, "block_type": block_type,
                   "status": "completed", "content_text": block_type, "approved_by_teacher": 0}
            stored[block_type] = run
            return run

        blocks.generate_and_persist = fake_generate
        blocks.lesson_block_state = lambda project_id, lesson_id, language_code="en", **kwargs: [
            {"block_type": key, "state": "needs_review", "approved": False, "run": stored.get(key)}
            for key in blocks.ordered_block_types()
        ]
        result = blocks.generate_full_lesson(
            {"id": 1}, "teacher", {"id": 3, "approved_by_teacher": 1}, "L1"
        )
        assert result["generated"] == len(blocks.ordered_block_types())
        assert result["ready_for_review"] is True

        approved = []
        blocks.db.approve_teacher_lesson_block = lambda run_id, project_id, username: approved.append(run_id)
        blocks.lesson_completion = lambda project_id, lesson_id, **kwargs: {"required": 9, "available": 9, "approved": 9, "complete": True}
        blocks.lesson_quality_snapshot = lambda project_id, lesson_id, **kwargs: {"pedagogical_gate": {"can_approve": True, "blockers": []}}
        completion = blocks.approve_full_lesson(1, "L1", "teacher")
        assert len(approved) == len(blocks.ordered_block_types())
        assert completion["complete"] is True
    finally:
        blocks.block_generation_status = original_status
        blocks.db.latest_approved_lesson_blocks = original_latest_approved
        blocks.db.latest_teacher_lesson_block = original_latest
        blocks.generate_and_persist = original_generate
        blocks.lesson_block_state = original_state
        blocks.db.approve_teacher_lesson_block = original_approve
        blocks.lesson_completion = original_completion
        blocks.lesson_quality_snapshot = original_quality
        blocks._active_blueprint_run_id = original_active


def validate_teacher_ui_static() -> None:
    text = (ROOT / "teacher_studio.py").read_text(encoding="utf-8")
    css = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")
    secrets = (ROOT / ".streamlit" / "secrets_example.toml").read_text(encoding="utf-8")
    assert "import simple_teacher_journey" in text
    assert "def _render_simple_project_workspace" in text
    assert "def _render_simple_lesson_builder" in text
    assert "def _render_simple_plan" in text
    assert "generate_full_lesson" in text
    assert "approve_full_lesson" in text
    assert "v6184-current-step" in css
    assert "v6184-action-marker" in css
    assert 'TEACHER_SIMPLE_MODE_DEFAULT = "true"' in secrets
    assert any(v in (ROOT / "db.py").read_text(encoding="utf-8") for v in ('APP_VERSION = "v6.18.4-simple-teacher-journey"', 'APP_VERSION = "v6.20.0-published-course-runtime"', 'APP_VERSION = "v6.19.1-learner-evidence-misconception-tracing"', 'APP_VERSION = "v6.19.0-pedagogical-quality-adaptive-coach"', 'APP_VERSION = "v6.18.9-lesson-identity-content-hygiene"', 'APP_VERSION = "v6.18.8-teacher-workspace-screenshot-polish"', 'APP_VERSION = "v6.18.7-frictionless-ui-contract"', 'APP_VERSION = "v6.18.6-unified-premium-platform-design"', 'APP_VERSION = "v6.18.5-premium-lesson-workspace"'))


def main() -> None:
    validate_simple_state()
    validate_lesson_batch_contract()
    validate_teacher_ui_static()
    print("V6.18.4 simple teacher journey validation passed.")


if __name__ == "__main__":
    main()
