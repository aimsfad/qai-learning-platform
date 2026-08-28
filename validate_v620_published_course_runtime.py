"""V6.20 validation: published teacher-course runtime and release hygiene."""

from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _fake_streamlit() -> None:
    fake = types.ModuleType("streamlit")
    fake.secrets = {}

    def cache_resource(*args, **kwargs):
        def decorator(fn):
            return fn
        return decorator

    fake.cache_resource = cache_resource
    sys.modules["streamlit"] = fake


def validate_static_contracts() -> None:
    db_source = (ROOT / "db.py").read_text(encoding="utf-8")
    app_source = (ROOT / "app.py").read_text(encoding="utf-8")
    main_source = (ROOT / "main_app.py").read_text(encoding="utf-8")
    teacher_source = (ROOT / "teacher_studio.py").read_text(encoding="utf-8")
    runtime_source = (ROOT / "published_course_runtime.py").read_text(encoding="utf-8")
    feedback_source = (ROOT / "feedback_engine.py").read_text(encoding="utf-8")
    css_source = (ROOT / ".streamlit" / "v6_theme.css").read_text(encoding="utf-8")
    secrets_example = (ROOT / ".streamlit" / "secrets_example.toml").read_text(encoding="utf-8")
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    packager = (ROOT / "package_release.py").read_text(encoding="utf-8")

    require('APP_VERSION = "v6.20.0-published-course-runtime"' in db_source, "V6.20 app version missing")
    for table in (
        "published_course_enrollments",
        "published_course_lesson_progress",
        "published_course_ai_interactions",
    ):
        require(table in db_source, f"missing V6.20 table: {table}")
    require("teacher_project_runtime_readiness" in db_source, "publication readiness gate missing")
    require("ENABLE_PUBLISHED_COURSE_RUNTIME" in db_source, "runtime publication gate flag missing")
    require('("Learning", "Published Courses"' in app_source, "native Published Courses route missing")
    require('pages = ["Student Home", "Published Courses"]' in main_source, "student Published Courses permission missing")
    require("published_course_runtime.render_catalog(student)" in teacher_source, "teacher catalog does not delegate to V6.20 runtime")
    require("teacher_project_runtime_readiness" in teacher_source, "teacher publication UI lacks runtime readiness")
    require("generate_course_tutor_response" in feedback_source, "domain-neutral published-course coach missing")
    require("course_system_prompt" in feedback_source, "domain-neutral coach system contract missing")
    require("attempt_gate.validate_attempt_text" in runtime_source, "attempt-first course gate missing")
    require("latest_approved_lesson_blocks" in runtime_source, "runtime is not bound to approved lesson blocks")
    require("max_unlocked_index" in runtime_source, "sequential lesson unlock contract missing")
    require("v620-course-card" in css_source and "v620-support-card" in css_source, "V6.20 UI styles missing")
    require('ENABLE_PUBLISHED_COURSE_RUNTIME = "true"' in secrets_example, "V6.20 example feature flag missing")
    require(".streamlit/secrets.toml" in gitignore, "local Streamlit secrets are not ignored")
    require('".streamlit/secrets.toml"' in packager and '".git"' in packager, "release packager does not exclude secrets/VCS history")


def validate_database_runtime() -> None:
    with tempfile.TemporaryDirectory(prefix="v620_db_") as tmp:
        database = Path(tmp) / "validation.sqlite"
        os.environ["DATABASE_URL"] = f"sqlite:///{database.as_posix()}"
        os.environ["ENABLE_PUBLISHED_COURSE_RUNTIME"] = "true"
        _fake_streamlit()
        sys.modules.pop("db", None)
        db = importlib.import_module("db")
        db.init_db()

        project_id = db.save_teacher_project(
            {
                "teacher_username": "validator",
                "project_name": "Validated Algebra Course",
                "domain": "Mathematics",
                "program_name": "Validation",
                "unit_title": "Linear relationships",
                "target_concept": "Slope and intercept",
                "target_learners": "Secondary learners",
                "learner_level": "Secondary",
                "primary_language": "English",
                "primary_language_code": "en",
                "expected_duration": "2 lessons",
                "status": "draft",
            }
        )
        blueprint = {
            "concepts": [
                {"concept_id": "c1", "concept_name": "Slope"},
                {"concept_id": "c2", "concept_name": "Intercept"},
            ],
            "units": [{"unit_id": "u1", "title": "Linear relationships", "lesson_ids": ["l1", "l2"]}],
            "lessons": [
                {
                    "unit_id": "u1", "lesson_id": "l1", "title": "Reading slope",
                    "concept_ids": ["c1"], "lesson_sequence": ["activation", "explanation"],
                },
                {
                    "unit_id": "u1", "lesson_id": "l2", "title": "Using intercepts",
                    "concept_ids": ["c2"], "lesson_sequence": ["activation", "explanation"],
                },
            ],
            "outcomes": [
                {"lesson_id": "l1", "outcome_id": "o1", "verb": "interpret", "object": "slope", "success_criterion": "from a graph"},
                {"lesson_id": "l2", "outcome_id": "o2", "verb": "identify", "object": "intercept", "success_criterion": "from an equation"},
            ],
            "concept_edges": [{"from_concept_id": "c1", "to_concept_id": "c2", "relation_type": "prerequisite"}],
        }
        blueprint_id = db.save_teacher_blueprint_bundle(
            project_id=project_id,
            evidence_run_id=0,
            blueprint=blueprint,
            quality={"status": "ready", "identity_error_count": 0},
            status="ready",
            edited_by="validator",
        )
        db.approve_teacher_blueprint_run(blueprint_id, project_id, "validator")

        for lesson in blueprint["lessons"]:
            for order, block_type in enumerate(lesson["lesson_sequence"], start=1):
                run_id = db.save_teacher_lesson_block(
                    project_id=project_id,
                    blueprint_run_id=blueprint_id,
                    lesson_id=lesson["lesson_id"],
                    block_type=block_type,
                    sequence_order=order,
                    prompt_text="validation",
                    content_text=f"Approved {block_type} content for {lesson['title']}.",
                    provider="validator",
                    model="deterministic",
                    status="ok",
                    validation={"word_count": 8},
                    edited_by="validator",
                )
                db.approve_teacher_lesson_block(run_id, project_id, "validator")

        readiness = db.teacher_project_runtime_readiness(project_id)
        require(readiness.get("ready") is True, f"course should be publication-ready: {readiness}")
        require(int(readiness.get("ready_lesson_count") or 0) == 2, "not all lessons became runtime-ready")
        db.set_teacher_project_status(project_id, "validator", "published")
        require((db.get_published_teacher_project(project_id) or {}).get("status") == "published", "publication failed")

        student = db.create_student(
            "Runtime Validator", "validator@example.test", "3alimnIA", "Secondary", 1, 0,
            "Validation123!", participant_code="V620-TEST", preferred_language="en",
        )
        enrollment = db.start_published_course_enrollment(student["id"], project_id, blueprint_id, "l1")
        require(int(enrollment.get("blueprint_run_id") or 0) == blueprint_id, "enrollment did not pin the blueprint version")

        db.save_published_course_attempt(
            student_id=student["id"], project_id=project_id, blueprint_run_id=blueprint_id,
            lesson_id="l1", attempt_text="I think slope compares the vertical change with the horizontal change in the graph.",
        )
        db.complete_published_course_lesson(
            student_id=student["id"], project_id=project_id, blueprint_run_id=blueprint_id,
            lesson_id="l1", reflection_text="I can now explain slope using two points.",
        )
        db.set_published_course_position(student["id"], project_id, "l2")
        summary = db.published_course_progress_summary(student["id"], project_id)
        require(summary.get("completed_lessons") == 1, "lesson progress was not persisted")
        require(abs(float(summary.get("progress") or 0.0) - 0.5) < 1e-9, "course progress is incorrect")

        interaction_id = db.log_published_course_ai_interaction(
            student_id=student["id"], project_id=project_id, blueprint_run_id=blueprint_id,
            lesson_id="l1", task="hint", prompt="validation prompt", response="validation response",
            mode="rule_based", provider="local", model="local-fallback",
            adaptive_support_level=1, adaptive_support_mode="hint", adaptive_support_confidence=0.6,
        )
        require(interaction_id > 0, "AI interaction was not logged")

        db.save_published_course_attempt(
            student_id=student["id"], project_id=project_id, blueprint_run_id=blueprint_id,
            lesson_id="l2", attempt_text="I will inspect the constant term and compare it with where the line crosses the axis.",
        )
        db.complete_published_course_lesson(
            student_id=student["id"], project_id=project_id, blueprint_run_id=blueprint_id,
            lesson_id="l2", reflection_text="I can identify the intercept from both graphs and equations.",
        )
        db.set_published_course_position(student["id"], project_id, "l2", completed=True)
        # Moving the cursor after completion must not silently reopen the course.
        db.set_published_course_position(student["id"], project_id, "l1")
        final_enrollment = db.get_published_course_enrollment(student["id"], project_id) or {}
        require(final_enrollment.get("status") == "completed", "completed enrollment was silently reopened")

        delivery = db.published_course_delivery_summary(project_id)
        require(delivery.get("enrollments") == 1, "delivery enrollment aggregate is incorrect")
        require(delivery.get("completed_enrollments") == 1, "delivery completion aggregate is incorrect")
        require(delivery.get("completed_lesson_records") == 2, "lesson completion aggregate is incorrect")
        require(delivery.get("ai_interactions") == 1, "AI interaction aggregate is incorrect")


def main() -> None:
    validate_static_contracts()
    validate_database_runtime()
    print("V6.20 published course runtime validation passed.")


if __name__ == "__main__":
    main()
