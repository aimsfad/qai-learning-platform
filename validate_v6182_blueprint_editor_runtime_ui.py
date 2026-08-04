"""Validation for V6.18.2 blueprint editor runtime and teacher UI polish."""

from __future__ import annotations

import ast
import importlib
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    # Streamlit stub for modules that read secrets or render HTML.
    captured: list[str] = []
    fake_st = types.ModuleType("streamlit")
    fake_st.secrets = {
        "ENABLE_LESSON_BLUEPRINT": "true",
        "ENABLE_BLUEPRINT_EDITOR": "true",
        "BLUEPRINT_MIN_READINESS": "0.70",
    }
    fake_st.markdown = lambda body, **kwargs: captured.append(str(body))
    fake_st.cache_resource = lambda *args, **kwargs: (lambda fn: fn)
    sys.modules["streamlit"] = fake_st
    sys.path.insert(0, str(ROOT))

    engine = importlib.import_module("lesson_blueprint_engine")
    global_ui = importlib.import_module("global_design_system")

    required = {
        "prepare_editor_draft", "normalize_blueprint", "recompute_blueprint_quality",
        "compare_blueprints", "add_unit", "update_unit", "move_unit", "delete_unit",
        "add_lesson", "update_lesson", "move_lesson", "delete_lesson",
        "add_outcome", "update_outcome", "delete_outcome", "save_manual_revision",
    }
    missing = sorted(name for name in required if not callable(getattr(engine, name, None)))
    assert not missing, f"Missing editor API: {missing}"

    baseline = {
        "blueprint": {
            "schema_version": "3alimnia.lesson-blueprint.v1.1",
            "project_id": 1,
            "concepts": [
                {"concept_id": "C1", "name": "Values", "prerequisites": [], "source_ids": ["S1"]},
                {"concept_id": "C2", "name": "Variables", "prerequisites": ["C1"], "source_ids": ["S1"]},
            ],
            "concept_edges": [{"from_concept_id": "C1", "to_concept_id": "C2", "relation_type": "prerequisite"}],
            "units": [{"unit_id": "U1", "title": "Foundations", "description": "", "sequence_order": 1}],
            "lessons": [{
                "lesson_id": "L1", "unit_id": "U1", "title": "Values and variables",
                "sequence_order": 1, "estimated_duration_minutes": 45,
                "concept_ids": ["C1", "C2"], "source_ids": ["S1"], "prerequisites": [],
                "misconceptions": [], "activities": [], "assessments": [],
            }],
            "outcomes": [{
                "outcome_id": "LO1.1", "lesson_id": "L1", "bloom_level": "apply",
                "verb": "apply", "object": "variables", "condition": "after practice",
                "success_criterion": "75%", "activity_id": "A-L1-LO1.1", "assessment_id": "AS-L1-LO1.1",
            }],
        }
    }
    draft = engine.prepare_editor_draft(baseline)
    assert draft["units"][0]["unit_id"] == "U1"
    draft = engine.add_unit(draft, "Applied project", "A guided mini-project")
    new_unit = draft["units"][-1]["unit_id"]
    draft = engine.add_lesson(
        draft, unit_id=new_unit, title="Mini-project", duration_minutes=60,
        concept_ids="C1, C2", source_ids="S1",
    )
    new_lesson = draft["lessons"][-1]["lesson_id"]
    draft = engine.add_outcome(
        draft, lesson_id=new_lesson, bloom_level="create", verb="build",
        object_text="a small program", condition="after guided practice",
        success_criterion="runs without errors",
    )
    comparison = engine.compare_blueprints(baseline["blueprint"], draft)
    assert comparison["changed"] is True
    assert new_unit in comparison["units"]["added"]
    assert new_lesson in comparison["lessons"]["added"]
    quality = engine.recompute_blueprint_quality(draft)
    assert quality["integrity_score"] == 1.0

    # The page-header payload must be a single balanced HTML tree. This avoids
    # Streamlit rendering a detached </div> as a visible Markdown code block.
    global_ui.render_page_header(
        "Teacher workspace", "Build reviewable educational assets.",
        lang="en", eyebrow="Teacher workspace", status="Content Studio",
        meta=["7-stage workflow", "Human approval"], compact=True, icon="edit_note",
    )
    assert captured, "Page header did not render"
    header = captured[-1]
    assert header.startswith("<section"), header[:80]
    assert "\n" not in header
    assert header.count("<div") == header.count("</div>"), header
    assert header.endswith("</section>")

    teacher_source = (ROOT / "teacher_studio.py").read_text(encoding="utf-8")
    assert "Blueprint editor API is incomplete" in teacher_source
    assert "base_run_id=int(bundle[\"id\"])" in teacher_source
    assert "edited_blueprint=st.session_state[draft_key]" in teacher_source
    assert "lesson_blueprint_engine.save_manual_revision(project_id" not in teacher_source

    # All lesson_blueprint_engine attributes used by the teacher UI must exist.
    tree = ast.parse(teacher_source)
    used = {
        node.attr for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "lesson_blueprint_engine"
    }
    undefined = sorted(name for name in used if not callable(getattr(engine, name, None)))
    assert not undefined, f"Teacher UI calls undefined blueprint API: {undefined}"

    css = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")
    assert "V6.18.2 — Teacher workspace and blueprint editor polish" in css
    assert "teacher_studio_nav_control" in css
    assert "APP_VERSION = \"v6.18.3-guided-blueprint-lesson-production\"" in (ROOT / "db.py").read_text(encoding="utf-8")

    print("V6.18.2 blueprint editor runtime and UI validation passed.")


if __name__ == "__main__":
    main()
